#!/usr/bin/env python
from matplotlib import pyplot as plt
import requests
import json
import time

# configure connection vm, sflow and onos
vm_ip_address = '192.168.56.104'
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
        self.data = {'interfaces': interfaces}
        #return {'interfaces': interfaces}

    # TODO: Define function to modify flows
    def modify_flows(self):
        return

    # Print JSON environment
    def print_data(self):
        print(json.dumps(self.data, indent=2))

    def print_data_larger_than_x_percent(self, x):
        for interface in self.data["interfaces"]:
            if interface["utilization"] > x:
                print(interface)

    def calculate_interface_utilization(ifinoctets):
        return (ifinoctets * 8) / mininet_link_speed

    def sort_dictionary_descending(dictionary):
        return {k: v for k, v in sorted(dictionary.items(), key=lambda item: item[1], reverse=True)}

    def generate_plot(self, data_at_time_steps):
        plot_data = {}
        interfaces_plotted = {}

        # Initialize plot_data
        for data_at_time_step in data_at_time_steps:
            for interface in data_at_time_step:
                plot_data[interface['interface']] = {}
                interfaces_plotted[interface['interface']] = False
        for key in plot_data:
            for i in range(len(data_at_time_steps)):
                plot_data[key][i] = 0.0

        # Populate plot_data
        for idx, data_at_time_step in enumerate(data_at_time_steps):
            for interface in data_at_time_step:
                plot_data[interface['interface']][idx] = interface['utilization']
                if interface['utilization'] > 0.25:
                    interfaces_plotted[interface['interface']] = True

        # Generate plot
        fig, ax = plt.subplots(figsize=(10, 4), dpi=80)
        for interface in [*plot_data.keys()]:
            if interfaces_plotted[interface]:
                ax.plot([*plot_data[interface].keys()], [*plot_data[interface].values()], linewidth=2, label=interface)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.set_xlim(0, 50)
        ax.set_ylim(0, 1)
        ax.grid(axis='y', color='w')
        ax.set_ylabel('Interface utilization')
        ax.set_xlabel('Time steps')
        ax.set_facecolor('#f1f1f2')
        ax.legend()
        plt.show()

        return plot_data


# TODO: Fix below code – currently only used for test purposes
test = NetworkTopology()
data_at_time_steps = []
t_end = time.time() + 50    # 45 seconds
while time.time() < t_end:
    test.generate_json_environment()
    data_at_time_steps.append(test.data["interfaces"])
    time.sleep(1)
test.generate_plot(data_at_time_steps)


# Below is example of environment...

# {
#   "interfaces": [
#     {
#       "interface": "s1-eth2",
#       "utilization": 6.670665866826634e-05,
#       "of_dpid": "0000000000000001",
#       "of_port": "2"
#     },
#     {
#       "interface": "s2-eth1",
#       "utilization": 0.0,
#       "of_dpid": "0000000000000002",
#       "of_port": "1"
#     }
#   ]
# }


