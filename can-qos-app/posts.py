import json
import requests

# Configure connection to sflow and onos
machine_ip_address = '127.0.0.1'
sflow_rt_port = '8008'
onos_port = '8181'
credentials = ('onos', 'rocks')
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

def select_action(device_id):
    app_id = '99'  # 99 is an arbitrary id used for the can-qos-app
    header = {'Content-Type': 'application/json', 'Accept': 'application/json'}  # defines the header for the request

    # Load the stream template for the post request
    with open('stream_template.json') as f:
        stream = json.load(f)

    # Format the post request
    out_port, in_port, eth_dst, eth_src = get_available_actions(device_id)
    stream['deviceId'] = device_id
    stream['treatment']['instructions'][0]['port'] = out_port
    stream['selector']['criteria'][0]['port'] = in_port
    stream['selector']['criteria'][1]['mac'] = eth_dst
    stream['selector']['criteria'][2]['mac'] = eth_src

    # Process the post request
    r = requests.post(f'{onos}/onos/v1/flows/{device_id}?appId={app_id}', data=json.dumps(stream), auth=credentials,
                      headers=header)
    print(r.status_code)


def get_available_actions(device_id, out_port):
    """Selects and performs a reinforcement learning action, i.e. updates a flow in ONOS."""
    actions = []
    alt_paths = set()

    # Filter src and dst hosts from existing flows
    action_metrics_tuples = filter_eth_src_dst_in_out_port_from_flows(device_id)
    for action_metrics_tuple in action_metrics_tuples:
        if out_port == action_metrics_tuple[3]:
            actions.append({'eth_src': action_metrics_tuple[0], 'eth_dst': action_metrics_tuple[1],
                            'in_port': action_metrics_tuple[2], 'out_port': action_metrics_tuple[3]})

    for action in actions:
        eth_dst_switches = get_switch_connected_to_host(f'{action["eth_dst"]}/None')
        for eth_dst_switch in eth_dst_switches:
            alt_paths.update(get_alternative_paths_from_switch(device_id, eth_dst_switch))
    alt_paths = sorted(list(alt_paths))  # list of alternative paths in ascending order
    alt_paths.remove(out_port)  # remove current path from alternative paths

    actions = [action for action in actions for _ in range(len(alt_paths))]  # create duplicate elements for alternative ports

    # Updates action metrics with alternative ports
    for i in range(len(actions) // len(alt_paths)):
        for j in range(len(alt_paths)):
            actions[i]['out_port'] = alt_paths[i * len(alt_paths) + j]
    return actions


def filter_eth_src_dst_in_out_port_from_flows(device_id):
    """ Returns tuple `(eth_src, eth_dst, in_port, out_port)` from existing flows."""
    src_dst_pairs = []
    r = requests.get(f'{onos}/onos/v1/flows/{device_id}', auth=credentials)
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


def get_alternative_paths_from_switch(src_device_id, dst_device_id):
    """Finds an alternative shortest path from a specific switch to the destination."""
    paths = []
    r = requests.get(f'{onos}/onos/v1/paths/{src_device_id}/{dst_device_id}', auth=credentials)
    response = r.json()
    for path in response['paths']:
        paths.append(path['links'][0]['src']['port'])
    return paths


def get_switch_connected_to_host(host_id):
    locations = []
    r = requests.get(f'{onos}/onos/v1/hosts/{host_id}', auth=credentials)
    response = r.json()
    for location in response['locations']:
        locations.append(location['elementId'])
    return locations


def get_interface_utilizations():
    """Returns interface utilizations."""
    r = requests.get(f'{sflow_rt}/dump/TOPOLOGY/ifoutoctets/json')
    data = r.json()
    return _parse_json(data, True)


def get_openflow_device_id():
    """Returns OpenFlow device IDs."""
    r = requests.get(f'{sflow_rt}/dump/TOPOLOGY/of_dpid/json')
    data = r.json()
    return _parse_json(data)


def get_openflow_port_number():
    """Returns OpenFlow port numbers."""
    r = requests.get(f'{sflow_rt}/dump/TOPOLOGY/of_port/json')
    data = r.json()
    return _parse_json(data)


def get_states():
    states = []
    if_out_utilizations = get_interface_utilizations()
    of_dpids = get_openflow_device_id()
    of_ports = get_openflow_port_number()

    for if_out_utilization, of_dpid, of_port in zip(if_out_utilizations.values(), of_dpids.values(), of_ports.values()):
        states.append({'if_out_utilization': if_out_utilization, 'of_dpid': of_dpid, 'of_port':of_port})

    return states


def get_reward():
    """Returns the reward (or penalty to be correct, since the value is negative)."""
    reward = 0
    states = get_states()
    for state in states:
        reward += state['if_out_utilization']
    return -reward

# select_action("of:0000000000000001")
# print(get_action_metrics('of:0000000000000001'))

# print(filter_eth_src_dst_in_out_port_from_flows('of:0000000000000001'))
#print(get_available_actions('of:0000000000000001', '2'))
#print(get_switch_connected_to_host('00:00:00:00:00:02/None'))
#print(get_alternative_paths_from_switch('of:0000000000000001', 'of:0000000000000004'))
print(get_interface_utilizations())
print(get_openflow_device_id())
print(get_openflow_port_number())
#states = get_states()
print(get_reward())
