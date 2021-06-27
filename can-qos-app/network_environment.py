#!/usr/bin/env python
import requests
import json
from time import sleep, time
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController, Host, OVSKernelSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.clean import Cleanup
from mininet.log import setLogLevel, info

# Configure connection to sflow and onos
machine_ip_address = '127.0.0.1'
sflow_rt_port = '8008'
onos_port = '8181'
onos_creds = ('onos', 'rocks')  # used to authenticate with the rest api
mininet_link_bw = 10 * 1_000_000

# The ip address of sflow-rt and onos
sflow_rt = f'http://{machine_ip_address}:{sflow_rt_port}'
onos = f'http://{machine_ip_address}:{onos_port}'


def _parse_json(data, link_utilization=False):
    output = {}
    for data_source in data:
        if link_utilization:
            output[data_source['dataSource']] = (data_source['metricValue'] * 8) / mininet_link_bw
        else:
            output[data_source['dataSource']] = data_source['metricValue']
    return output


def _get_interface_names():
    """Returns interface names."""
    r = requests.get(f'{sflow_rt}/dump/TOPOLOGY/ifname/json')
    data = r.json()
    return _parse_json(data)


def _get_interface_utilizations():
    """Returns interface utilizations."""
    r = requests.get(f'{sflow_rt}/dump/TOPOLOGY/ifoutoctets/json')
    data = r.json()
    return _parse_json(data, True)


def _get_openflow_device_id():
    """Returns OpenFlow device IDs."""
    r = requests.get(f'{sflow_rt}/dump/TOPOLOGY/of_dpid/json')
    data = r.json()
    return _parse_json(data)


def _get_openflow_port_number():
    """Returns OpenFlow port numbers."""
    r = requests.get(f'{sflow_rt}/dump/TOPOLOGY/of_port/json')
    data = r.json()
    return _parse_json(data)


def _filter_eth_src_dst_in_out_port_from_flows(device_id):
    """ Returns tuple `(eth_src, eth_dst, in_port, out_port)` from existing flows."""
    src_dst_pairs = []
    r = requests.get(f'{onos}/onos/v1/flows/{device_id}', auth=onos_creds)
    response = r.json()
    for flow in response['flows']:
        eth_src, eth_dst, in_port, out_port = ('', '', '', '')
        if flow['appId'] == 'org.onosproject.fwd':
            for instruction in flow['treatment']['instructions']:
                if 'type' in instruction:  # perhaps redundant
                    if instruction['type'] == 'OUTPUT':
                        out_port = instruction['port']
            for criteria in flow['selector']['criteria']:
                if 'type' in criteria:  # perhaps redundant
                    if criteria['type'] == 'IN_PORT':
                        in_port = criteria['port']
                    if criteria['type'] == 'ETH_DST':
                        eth_dst = criteria['mac']
                    if criteria['type'] == 'ETH_SRC':
                        eth_src = criteria['mac']
                if eth_src and eth_dst:
                    src_dst_pairs.append((eth_src, eth_dst, in_port, out_port))
    return src_dst_pairs


def _get_alternative_paths_from_switch(src_device_id, dst_device_id):
    """Finds an alternative shortest path from a specific switch to the destination."""
    paths = []
    r = requests.get(f'{onos}/onos/v1/paths/{src_device_id}/{dst_device_id}', auth=onos_creds)
    response = r.json()
    print(f'{src_device_id}, {dst_device_id}')
    print(response)
    for path in response['paths']:
        paths.append(path['links'][0]['src']['port'])
    return paths


def _get_switch_connected_to_host(host_id):
    """Returns the list of a hosts immediate switches."""
    locations = []
    r = requests.get(f'{onos}/onos/v1/hosts/{host_id}', auth=onos_creds)
    response = r.json()
    for location in response['locations']:
        locations.append(location['elementId'])
    return locations


class NetworkEnvironment:
    def __init__(self):
        setLogLevel('info')
        Cleanup.cleanup()  # clean up any running mininet network
        self.enable_sflow_rt()  # compile and run sflow-rt helper script
        self.net = Mininet(topo=TopoThree(),
                           controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6633, protocol='tcp'))
        self.net.start()

    def perform_action(self, device_id, out_port, in_port, eth_dst, eth_src):
        app_id = '99'  # 99 is an arbitrary id used for the can-qos-app
        header = {'Content-Type': 'application/json',
                  'Accept': 'application/json'}  # defines the header for the request

        # Load the stream template for the post request
        with open('stream_template.json') as f:
            stream = json.load(f)

        # Format the post request
        stream['deviceId'] = device_id
        stream['treatment']['instructions'][0]['port'] = out_port
        stream['selector']['criteria'][0]['port'] = in_port
        stream['selector']['criteria'][1]['mac'] = eth_dst
        stream['selector']['criteria'][2]['mac'] = eth_src

        # Process the post request
        r = requests.post(f'{onos}/onos/v1/flows/{device_id}?appId={app_id}', data=json.dumps(stream), auth=onos_creds,
                          headers=header)
        print(r.status_code)

    def get_available_actions(self, device_id, out_port):
        """Selects and performs a reinforcement learning action, i.e. updates a flow in ONOS."""
        actions = []
        alt_paths = set()

        # Filter src and dst hosts from existing flows
        action_metrics_tuples = _filter_eth_src_dst_in_out_port_from_flows(device_id)
        for action_metrics_tuple in action_metrics_tuples:
            if out_port == action_metrics_tuple[3]:
                actions.append({'eth_src': action_metrics_tuple[0], 'eth_dst': action_metrics_tuple[1],
                                'in_port': action_metrics_tuple[2], 'out_port': action_metrics_tuple[3]})

        for action in actions:
            eth_dst_switches = _get_switch_connected_to_host(f'{action["eth_dst"]}/None')
            for eth_dst_switch in eth_dst_switches:
                alt_paths.update(_get_alternative_paths_from_switch(device_id, eth_dst_switch))
        alt_paths = sorted(list(alt_paths))  # list of alternative paths in ascending order
        alt_paths.remove(out_port)  # remove current path from alternative paths

        actions = [action for action in actions for _ in
                   range(len(alt_paths))]  # create duplicate elements for alternative ports

        # Updates action metrics with alternative ports
        for i in range(len(actions) // len(alt_paths)):
            for j in range(len(alt_paths)):
                actions[i * len(alt_paths) + j]['out_port'] = alt_paths[j]
        self.actions = actions

    def get_reward(self):
        """Returns the reward (or penalty to be correct, since the value is negative)."""
        reward = 0
        for state in self.states:
            reward += state['if_out_utilization']
        self.reward = -reward

    def get_states(self):
        states = []
        if_out_utilizations = _get_interface_utilizations()
        of_dpids = _get_openflow_device_id()
        of_ports = _get_openflow_port_number()

        for if_out_utilization, of_dpid, of_port in zip(if_out_utilizations.values(), of_dpids.values(),
                                                        of_ports.values()):
            states.append({'if_out_utilization': if_out_utilization, 'of_dpid': of_dpid, 'of_port': of_port})
        self.states = states

    def generate_json_data(self, duration=1, print_result=True):
        """Requests metrics from sFlow-RT"""  # each second for a specified duration."""
        end_time = time() + duration
        while time() < end_time:
            r = requests.get(f'{sflow_rt}/table/TOPOLOGY/ifname,ifinoctets,of_dpid,of_port/json')
            data = r.json()
            interfaces = []
            for item in data:
                interface = {}
                for subitem in item:
                    if subitem['metricName'] == 'ifname':
                        interface['interface_name'] = subitem['metricValue']
                    if subitem['metricName'] == 'ifinoctets':
                        interface['utilization'] = (subitem['metricValue'] * 8) / mininet_link_bw
                    if subitem['metricName'] == 'of_dpid':
                        interface['of_dpid'] = subitem['metricValue']
                    if subitem['metricName'] == 'of_port':
                        interface['of_port'] = subitem['metricValue']
                interfaces.append(interface)
            self.json_data = interfaces
            if print_result:
                print(self.json_data)
            # TODO: Write 'json_data' to log file
            sleep(1)  # halt execution for a second

    def enable_sflow_rt(self, path_to_script='../../sflow-rt/extras/sflow.py'):
        """Enables sFlow-RT by executing helper script sflow.py."""
        with open(path_to_script, 'rb') as sflow_rt_script:
            code = compile(sflow_rt_script.read(), path_to_script, 'exec')
        exec(code, globals(), globals())

    def cleanup(self, halt_execution=False):
        """Terminates the Mininet topology."""
        info(f'*** Shutting down\n')
        if halt_execution:
            sleep(20)  # halt execution to ensure sflow-rt has time to poll metrics
        self.net.stop()

    # Auxiliary functions used for testing basic functionality -- delete later
    def iperf(self):
        h1, h2 = self.net.get('h1', 'h2')
        self.net.iperf((h1, h2))

    def cli(self):
        """Starts the Mininet CLI."""
        CLI(self.net)

    def test_one(self, duration=30):
        """Generates TCP traffic between a client host h1 and server host h2."""
        h1, h2 = self.net.get('h1', 'h2')
        info(f'*** Starting iperf server\n')
        h1.cmd('iperf -s &')
        sleep(1)  # sleep to prevent connection error using iperf
        info(f'*** Generating traffic\n')
        h2.cmd(f'iperf -c {h1.IP()} -b 10m -t{duration} &')
        info(f'*** Test running as background task\n')
        sleep(9)  # halt execution to wait for sflow-rt to poll metrics

    def test_two(self, duration=30):
        """Generates TCP traffic between a client host h1 and a server host h2."""
        h1, h2 = self.net.get('h1', 'h2')
        info(f'*** Starting iperf server\n')
        h2.cmd('iperf -s &')
        sleep(1)  # sleep to prevent connection error using iperf
        info('*** Generating traffic\n')
        h1.cmd(f'iperf -c {h2.IP()} -b 10m -t {duration} &')
        info(f'*** Test running as background task\n')
        sleep(9)  # halt execution to wait for sflow-rt to poll metrics

    def test_three(self, duration=30):
        """Generates TCP traffic between four client hosts h1, h3, respectively, and two server hosts h2 and h4."""
        h1, h2, h3, h4 = self.net.get('h1', 'h2', 'h3', 'h4')
        info(f'*** Starting iperf servers\n')
        h2.cmd('iperf -s &')
        h4.cmd('iperf -s &')
        sleep(1)  # sleep to prevent connection error using iperf
        info('*** Generating traffic\n')
        h1.cmd(f'iperf -c {h4.IP()} -b 5m -t {duration} &')
        h3.cmd(f'iperf -c {h2.IP()} -b 5m -t {duration} &')
        info(f'*** Test running as background task\n')
        sleep(9)  # halt execution to wait for sflow-rt to poll metrics

    def test_four(self, duration=30):
        """Generates TCP and UDP traffic between four client hosts, h1, h3, h5, and h6, respectively, and two server hosts h2 and h4."""
        h1, h2, h3, h4, h5, h6 = self.net.get('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
        info(f'*** Starting iperf servers\n')
        h2.cmd('iperf -s &')
        h4.cmd('iperf -s &')
        sleep(1)  # sleep to prevent connection error using iperf
        info('*** Generating traffic\n')
        h1.cmd(f'iperf -c {h4.IP()} -b 10m -t {duration} &')
        h3.cmd(f'iperf -c {h2.IP()} -b 10m -t {duration} &')
        h5.cmd(f'iperf -c {h4.IP()} -b 10m -t {duration} &')
        h6.cmd(f'iperf -c {h4.IP()} -b 10m -t {duration} &')
        info(f'*** Test running as background task\n')
        sleep(9)  # halt execution to wait for sflow-rt to poll metrics


# Mininet classes and functions
class TestTopo(Topo):
    """Simple topology used to test that flows can be correctly updated using ONOS."""

    def build(self):
        h1 = self.addHost('h1', cls=Host, ip='10.0.0.1', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', cls=Host, ip='10.0.0.2', mac='00:00:00:00:00:02')

        s1 = self.addSwitch('s1', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s3 = self.addSwitch('s3', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s4 = self.addSwitch('s4', cls=OVSKernelSwitch, protocols='OpenFlow13')

        self.addLink(h1, s1, cls=TCLink, bw=10)
        self.addLink(h2, s4, cls=TCLink, bw=10)
        self.addLink(s1, s2, cls=TCLink, bw=10)
        self.addLink(s1, s3, cls=TCLink, bw=10)
        self.addLink(s2, s4, cls=TCLink, bw=10)
        self.addLink(s3, s4, cls=TCLink, bw=10)


class TopoOne(Topo):
    """Basic topology used to implement and test correct functionality of sFlow-RT."""

    def build(self):
        h1 = self.addHost('h1', cls=Host, ip='10.0.0.1', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', cls=Host, ip='10.0.0.2', mac='00:00:00:00:00:02')

        s1 = self.addSwitch('s1', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch, protocols='OpenFlow13')

        self.addLink(h1, s1, cls=TCLink, bw=10)
        self.addLink(h2, s2, cls=TCLink, bw=10)
        self.addLink(s1, s2, cls=TCLink, bw=10)


class TopoTwo(Topo):
    """Simple topology used to test that flows can be correctly updated using ONOS."""

    def build(self):
        h1 = self.addHost('h1', cls=Host, ip='10.0.0.1', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', cls=Host, ip='10.0.0.2', mac='00:00:00:00:00:02')

        s1 = self.addSwitch('s1', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s3 = self.addSwitch('s3', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s4 = self.addSwitch('s4', cls=OVSKernelSwitch, protocols='OpenFlow13')

        self.addLink(h1, s1, cls=TCLink, bw=10)
        self.addLink(h2, s4, cls=TCLink, bw=10)
        self.addLink(s1, s2, cls=TCLink, bw=10)
        self.addLink(s1, s3, cls=TCLink, bw=10)
        self.addLink(s2, s4, cls=TCLink, bw=10)
        self.addLink(s3, s4, cls=TCLink, bw=10)


class TopoThree(Topo):
    """Simple topology used to train and test the functionality of the CAN."""

    def build(self):
        h1 = self.addHost('h1', cls=Host, ip='10.0.0.1', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', cls=Host, ip='10.0.0.2', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', cls=Host, ip='10.0.0.3', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', cls=Host, ip='10.0.0.4', mac='00:00:00:00:00:04')

        s1 = self.addSwitch('s1', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s3 = self.addSwitch('s3', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s4 = self.addSwitch('s4', cls=OVSKernelSwitch, protocols='OpenFlow13')

        self.addLink(h1, s1, cls=TCLink, bw=10)
        self.addLink(h2, s1, cls=TCLink, bw=10)
        self.addLink(h3, s4, cls=TCLink, bw=10)
        self.addLink(h4, s4, cls=TCLink, bw=10)
        self.addLink(s1, s2, cls=TCLink, bw=10)
        self.addLink(s1, s3, cls=TCLink, bw=10)
        self.addLink(s2, s4, cls=TCLink, bw=10)
        self.addLink(s3, s4, cls=TCLink, bw=10)


class TopoFour(Topo):
    """An advanced topology used to train and test the functionality of the CAN."""

    def build(self):
        h1 = self.addHost('h1', cls=Host, ip='10.0.0.1', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', cls=Host, ip='10.0.0.2', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', cls=Host, ip='10.0.0.3', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', cls=Host, ip='10.0.0.4', mac='00:00:00:00:00:04')
        h5 = self.addHost('h5', cls=Host, ip='10.0.0.5', mac='00:00:00:00:00:05')
        h6 = self.addHost('h6', cls=Host, ip='10.0.0.6', mac='00:00:00:00:00:06')

        s1 = self.addSwitch('s1', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s3 = self.addSwitch('s3', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s4 = self.addSwitch('s4', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s5 = self.addSwitch('s5', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s6 = self.addSwitch('s6', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s7 = self.addSwitch('s7', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s8 = self.addSwitch('s8', cls=OVSKernelSwitch, protocols='OpenFlow13')

        self.addLink(h1, s1, cls=TCLink, bw=10)
        self.addLink(h2, s1, cls=TCLink, bw=10)
        self.addLink(h3, s5, cls=TCLink, bw=10)
        self.addLink(h4, s5, cls=TCLink, bw=10)
        self.addLink(h5, s7, cls=TCLink, bw=10)
        self.addLink(h6, s8, cls=TCLink, bw=10)
        self.addLink(s1, s2, cls=TCLink, bw=10)
        self.addLink(s1, s3, cls=TCLink, bw=10)
        self.addLink(s2, s4, cls=TCLink, bw=10)
        self.addLink(s3, s4, cls=TCLink, bw=10)
        self.addLink(s4, s5, cls=TCLink, bw=10)
        self.addLink(s4, s7, cls=TCLink, bw=10)
        self.addLink(s5, s6, cls=TCLink, bw=10)
        self.addLink(s6, s7, cls=TCLink, bw=10)
        self.addLink(s7, s8, cls=TCLink, bw=10)


class ONOSController(RemoteController):
    """The ONOS SDN controller."""

    def build(self, name):
        self.ip = '127.0.0.1'
        self.port = 6633
        self.protocol = 'tcp'


topos = {'topo1': TopoOne,
         'topo2': TopoTwo,
         'topo3': TopoThree,
         'topo4': TopoFour}

controllers = {'onos': ONOSController}

if __name__ == 'mininet_topologies':
    setLogLevel('info')
    net = Mininet(topo=TopoOne,
                  controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6633, protocol='tcp'))
    net.start()
    CLI(net)
    net.stop()
