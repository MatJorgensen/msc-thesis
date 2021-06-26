import json
import requests
from mininet.net import Mininet

onos = f'http://192.168.56.104:8181'
credentials = ('onos', 'rocks')  # used to authenticate with the rest api

def select_action(device_id):
    app_id = '99'  # 99 is an arbitrary id used for the can-qos-app
    header = {'Content-Type': 'application/json', 'Accept': 'application/json'}  # defines the header for the request

    # Load the stream template for the post request
    with open('stream_template.json') as f:
        stream = json.load(f)

    # Format the post request
    out_port, in_port, eth_dst, eth_src = get_action_metrics(device_id)
    stream['deviceId'] = device_id
    stream['treatment']['instructions'][0]['port'] = out_port
    stream['selector']['criteria'][0]['port'] = in_port
    stream['selector']['criteria'][1]['mac'] = eth_dst
    stream['selector']['criteria'][2]['mac'] = eth_src

    # Process the post request
    r = requests.post(f'{onos}/onos/v1/flows/{device_id}?appId={app_id}', data=json.dumps(stream), auth=credentials, headers=header)
    print(r.status_code)

def get_action_metrics(device_id='of:0000000000000001'):
    """Selects and performs a reinforcement learning action, i.e. updates a flow in ONOS."""

    # Filter src and dst hosts from existing flows
    eth_src_dst_pairs = filter_eth_src_dst_in_out_port_from_flows(device_id)
    try:
        eth_src, eth_dst, in_port, curr_out_port = eth_src_dst_pairs[0]
    except ValueError:
        print(f'No ´eth_src´ and ´eth_dst´ in flow table for {device_id}')

    # Get switch connected to `eth_dst`
    try:
        eth_dst_device_id = get_switch_connected_to_host(f'{eth_dst}/None')[0]
    except ValueError:
        print(f'Host {eth_dst} is not connected to a switch')

    # Find alternative paths
    new_out_ports = get_alternative_paths_from_switch(device_id, eth_dst_device_id)
    new_out_ports.remove(curr_out_port)
    try:
        new_out_port = new_out_ports[0]
    except ValueError:
        print(f'No alternative paths from {device_id} to {eth_dst_device_id} exists')

    return (new_out_port, in_port, eth_dst, eth_src)


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

select_action("of:0000000000000001")


