#!/usr/bin/env python
import requests
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
mininet_link_bw = 10 * 1_000_000

# The ip address of sflow-rt and onos
sflow_rt = f'http://{machine_ip_address}:{sflow_rt_port}'
onos = f'http://{machine_ip_address}:{onos_port}'


class NetworkEnvironment:
    def __init__(self):
        setLogLevel('info')
        Cleanup.cleanup()   # clean up any running mininet network
        self.enable_sflow_rt()   # compile and run sflow-rt helper script
        self.net = Mininet(topo=TopoOne(), controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6633, protocol='tcp'))
        self.net.start()

    def get_interface_utilizations(self):
        """Returns link utilizations, i.e. the reinforcement learning states."""
        return

    def update_flows(self):
        """Updates a flow in ONOS, i.e. selects and performs a reinforcement learning action."""
        return

    def reward(self):
        """Returns the reward."""
        return

    def generate_json_data(self, duration=1, print_result=True):
        """Requests metrics from sFlow-RT"""# each second for a specified duration."""
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
            sleep(1)    # halt execution for a second

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

    def my_test(self, duration=30):
        """Generates TCP traffic between a client host h1 and server host h2."""
        h1, h2 = self.net.get('h1', 'h2')
        info(f'*** Starting iPerf server\n')
        h1.cmd('iperf -s &')
        sleep(1)  # sleep to prevent connection error using iperf
        info(f'*** Generating traffic\n')
        h2.cmd(f'iperf -c {h1.IP()} -t{duration} &')
        # sleep(duration)  # wait for iperf to finish
        info(f'*** Test executing in background\n')
        sleep(9)  # halt execution to wait for sflow-rt to poll metrics

# Mininet classes and functions
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
        h3 = self.addHost('h3', cls=Host, ip='10.0.0.3', mac='00:00:00:00:00:03')

        s1 = self.addSwitch('s1', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s3 = self.addSwitch('s3', cls=OVSKernelSwitch, protocols='OpenFlow13')

        self.addLink(h1, s1, cls=TCLink, bw=10)
        self.addLink(h2, s1, cls=TCLink, bw=10)
        self.addLink(h3, s2, cls=TCLink, bw=10)
        self.addLink(s1, s2, cls=TCLink, bw=10)
        self.addLink(s1, s3, cls=TCLink, bw=10)
        self.addLink(s2, s3, cls=TCLink, bw=10)


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
        self.addLink(h1, s2, cls=TCLink, bw=10)
        self.addLink(h2, s1, cls=TCLink, bw=10)
        self.addLink(h2, s2, cls=TCLink, bw=10)
        self.addLink(h3, s3, cls=TCLink, bw=10)
        self.addLink(h3, s4, cls=TCLink, bw=10)
        self.addLink(h4, s3, cls=TCLink, bw=10)
        self.addLink(h4, s4, cls=TCLink, bw=10)
        self.addLink(s1, s2, cls=TCLink, bw=10)
        self.addLink(s1, s3, cls=TCLink, bw=10)
        self.addLink(s1, s4, cls=TCLink, bw=10)
        self.addLink(s2, s3, cls=TCLink, bw=10)
        self.addLink(s2, s4, cls=TCLink, bw=10)
        self.addLink(s3, s4, cls=TCLink, bw=10)


class TopoFour(Topo):
    """An advanced topology used to train and test the functionality of the CAN."""
    def build(self):
        return
        # TODO: Define topology


class ONOSController(RemoteController):
    """The ONOS SDN controller."""
    def build(self, name):
        self.ip = '127.0.0.1'
        self.port = 6633
        self.protocol = 'tcp'


def test_one(net, time=30):
    """Generates TCP traffic between a client host h1 and server host h2."""
    h1, h2 = net.get('h1', 'h2')
    info(f'*** Starting iPerf server\n')
    h1.cmd('iperf -s &')
    sleep(1)    # sleep to prevent connection error using iperf
    info(f'*** Generating traffic\n')
    h2.cmd(f'iperf -c {h1.IP()} -t{time}')
    #h2.sendCmd(f'iperf -c {h1.IP()} -t{time}')
    info(f'*** Generated traffic\n')
    #info(h2.waitOutput())


def test_two(net, time=30):
    """Generates TCP traffic between two client hosts h1 and h2, respectively, and a server host h3."""
    h1, h2, h3 = net.get('h1', 'h2', 'h3')
    info(f'*** Starting iPerf server\n')
    h3.cmd('iperf -s &')
    sleep(1)    # sleep to prevent connection error using iperf
    info('*** Generating traffic\n')
    h1.sendCmd(f'iperf -c {h3.IP()} -t {time}')
    h2.sendCmd(f'iperf -c {h3.IP()} -t {time}')
    for h in (h1, h2):
        info(h.waitOutput())


def test_three(net, time=30):
    """Generates TCP traffic between four client hosts h1, h2, h4, and h5, respectively, and two server hosts h3 and h6."""
    h1, h2, h3, h4, h5, h6 = net.get('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
    info(f'*** Starting iPerf servers\n')
    h3.cmd('iperf -s &')
    h6.cmd('iperf -s &')
    sleep(1)    # sleep to prevent connection error using iperf
    info('*** Generating traffic\n')
    h1.sendCmd(f'iperf -c {h6.IP()} -t {time}')
    h2.sendCmd(f'iperf -c {h6.IP()} -t {time}')
    h4.sendCmd(f'iperf -c {h3.IP()} -t {time}')
    h5.sendCmd(f'iperf -c {h3.IP()} -t {time}')
    for h in (h1, h2, h4, h5):
        info(h.waitOutput())


def test_four(net):
    """Generates TCP traffic..."""
    # TODO: Define traffic pattern
    return


def test_five(net):
    """Generates random TCP and UDP traffic, mimicking a real-world traffic pattern."""
    # TODO: Define traffic pattern
    return


topos = {'topo1': TopoOne,
         'topo2': TopoTwo,
         'topo3': TopoThree,
         'topo4': TopoFour}

controllers = {'onos': ONOSController}

tests = {'test1': test_one,
         'test2': test_two,
         'test3': test_three,
         'test4': test_four,
         'test5': test_five}

if __name__ == 'mininet_topologies':
    setLogLevel('info')
    net = Mininet(topo=TopoOne, controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6633, protocol='tcp'))
    net.start()
    CLI(net)
    net.stop()
