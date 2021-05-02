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


# Auxillary functions
def flatten_list(nested_list):
    return [item for sublist in nested_list for item in sublist]


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


# define custom sflow-rt flow metric
def set_flow(name, flow):
    r = requests.get(f'{sflow}/flow/{name}/json')
    if r.status_code == 404:
        requests.put(f'{sflow}/flow/{name}/json', data=json.dumps(flow))


# define custom sflow-rt flow metric
name = 'mn_bytes'
flow = {'value': 'bytes', 't': 5}
set_flow(name, flow)

def calculate_metric_link_utilization():
    while True:
        r = requests.get(f'{sflow}/table/TOPOLOGY/ifname,ifinoctets,ifoutoctets/json')
        metrics = r.json()
        link_utilization = {}
        for metric in metrics:
            link_utilization[f'{metric[0]["metricValue"]}'] = calculate_link_utilization(metric[1]["metricValue"], metric[2]["metricValue"])
        print(sort_dec_desc(link_utilization))
        time.sleep(1)


def calculate_flow_link_utilization():
    # TODO: Check whether ingress and egress flows are needed...
    while True:
        r = requests.get(f'{sflow}/dump/127.0.0.1/mn_bytes/json')
        metrics = r.json()
        link_utilization = {}
        for metric in metrics:
            if metric['dataSource'] != '0':
                link_utilization[data_source_to_port(metric['dataSource'])] = (metric['metricValue'] * 8) / mininet_link_speed
        print(sort_dec_desc(link_utilization))
        time.sleep(1)


#print(data_source_to_port('14'))
#calculate_flow_link_utilization()
calculate_metric_link_utilization()


# Below is example of environment...
"""
[
  {
    "link":"s1-s2",
    "utilization":{
      "ingress":0.463,
      "egress":0.512
    }
  },
  {
    "link":"s1-s3",
    "utilization":{
      "ingress":0.327,
      "egress":0.279
    }
  }
]
"""

