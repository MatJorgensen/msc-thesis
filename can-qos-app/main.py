#!/usr/bin/env python
import requests
import json
import time

# configure connection vm, sflow and onos
vm_ip_address = '192.168.56.102'
sflow_port = '8008'
onos_port = '8181'
mininet_link_speed = 10 * 1000000

# ip address of sflow-rt and onos
sflow = f'http://{vm_ip_address}:{sflow_port}'
onos = f'http://{vm_ip_address}:{onos_port}'


class NetworkTopology:
    # Initializes the reinforcement learning environment
    def __init__(self):
        self.data = self.generate_json_environment()

    # Generates and updates the JSON environment
    def generate_json_environment(self):
        r = requests.get(f'{sflow}/table/TOPOLOGY/ifname,ifinoctets,of_dpid,of_port/json')
        data = r.json()
        interfaces = []
        # Parse JSON from sFlow-RT
        for item in data:
            interface = {}
            for subitem in item:
                if subitem['metricName'] == 'ifname':
                    interface['interface'] = subitem['metricValue']
                if subitem['metricName'] == 'ifinoctets':
                    interface['utilization'] = (subitem['metricValue'] * 8) / mininet_link_speed
                if subitem['metricName'] == 'of_dpid':
                    interface['of_dpid'] = subitem['metricValue']
                if subitem['metricName'] == 'of_port':
                    interface['of_port'] = subitem['metricValue']
            interfaces.append(interface)

        # Remove redundant switch interfaces and return
        interfaces = [i for i in interfaces if not ('eth' not in i['interface'])]
        return {'interfaces': interfaces}

    # TODO: Define function to modify flows
    def modify_flows(self):
        return

    # Print JSON environment
    def print_data(self):
        print(json.dumps(self.data, indent=2))

    def calculate_interface_utilization(ifinoctets):
        return (ifinoctets * 8) / mininet_link_speed

    def sort_dictionary_descending(dictionary):
        return {k: v for k, v in sorted(dictionary.items(), key=lambda item: item[1], reverse=True)}


test = NetworkTopology()
test.generate_json_environment()
test.print_data()

# Below is example of environment...
"""
{
  "interfaces": [
    {
      "interface": "s1-eth2",
      "utilization": 6.670665866826634e-05,
      "of_dpid": "0000000000000001",
      "of_port": "2"
    },
    {
      "interface": "s2-eth1",
      "utilization": 0.0,
      "of_dpid": "0000000000000002",
      "of_port": "1"
    }
  ]
}
"""
