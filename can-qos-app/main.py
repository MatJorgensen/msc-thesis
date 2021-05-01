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

# define custom sflow-rt flow metric
name = 'mn_bytes'
flow = {'value': 'bytes', 't': 2}
r = requests.put(f'{sflow}/flow/{name}/json', data=json.dumps(flow))

#name = 'mn_flow'
#flow = {'keys': 'ipsource,ipdestination,ipprotocol,or:tcpsourceport:icmptype,or:tcpdestinationport:udpdestinationport:icmpcode', 'value': 'bytes', 't': 2}
#r = requests.put(f'{sflow}/flow/{name}/json', data=json.dumps(flow))


# Auxillary functions
def flatten_list(list):
    return [item for sublist in list for item in sublist]

def calculate_link_utilization(ifinoctets, ifoutoctets):
    #if (ifinoctets == 0 or ifinoctets == 0):
    return max((ifinoctets * 8) / mininet_link_speed, (ifoutoctets * 8) / mininet_link_speed)
    #else:
    #    return 0

def sort_dec_desc(dictionary):
    return {k: v for k, v in sorted(dictionary.items(), key=lambda item: item[1], reverse=True)}


def data_source_to_port(data_source):
    r = requests.get(f'{sflow}/dump/127.0.0.1/ifname/json')
    metrics = r.json()
    for metric in metrics:
        if metric['dataSource'] == data_source:
            return metric['metricValue']


def calculate_metric_link_utilization():
    while True:
        r = requests.get(f'{sflow}/table/TOPOLOGY/ifname,ifinoctets,ifoutoctets/json')
        metrics = r.json()
        link_utilization = {}
        for metric in metrics:
            link_utilization[f'{metric[0]["metricValue"]}'] = calculate_link_utilization(metric[1]["metricValue"], metric[2]["metricValue"])
        print(sort_dec_desc(link_utilization))
        time.sleep(2)


def calculate_flow_link_utilization():
    # TODO: Check whether ingress and egress flows are needed...
    r = requests.get(f'{sflow}/dump/127.0.0.1/mn_bytes/json')
    metrics = r.json()
    link_utilization = {}
    for metric in metrics:
        print(metric)
        link_utilization[data_source_to_port(metric['dataSource'])] = metric['metricValue']
    print(sort_dec_desc(link_utilization))


#print(data_source_to_port('14'))
calculate_flow_link_utilization()
#calculate_metric_link_utilization()





def calculate_top_interfaces(metric):
    r = requests.get(f'{sflow}/table/TOPOLOGY/sort:{metric}:-/json')


    r.json()

    return

"""
def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


if __name__ == '__main__':
    print_hi('PyCharm')
"""