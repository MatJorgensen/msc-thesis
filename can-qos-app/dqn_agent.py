#!/usr/bin/python
from network_environment import NetworkEnvironment
import time

duration = 20  # duration of traffic generation and monitoring

start = time.time()  # used for testing
net = NetworkEnvironment()
net.test_three(duration)
time.sleep(10)
net.get_states()
for state in net.states:
    if state['if_out_utilization'] > 0.4 and state['of_port'] != '1' and state['of_port'] != '2':
        selected_state = state
print(selected_state)
net.get_available_actions(f"of:{selected_state['of_dpid']}", selected_state['of_port'])
print(net.actions)
net.cli()
print('Network created, tested, and terminated.')

