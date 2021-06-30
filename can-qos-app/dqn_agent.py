#!/usr/bin/python
import random
import time
import torch
import numpy as np
from network_environment import NetworkEnvironment

# Run code using following steps:
# - Start ONOS by executing command `bazel run onos-local -- clean debug`
# - Start sFlow-RT by executing command ´.\sflow-rt\start.sh`

duration = 95  # duration of traffic generation and monitoring

net = NetworkEnvironment()
net.test_three(duration)
time.sleep(10)
net.get_states()
print('*** STATES ***')
print(net.states)
for state in net.states:
    if state['if_out_utilization'] > 0.4 and state['of_port'] != '0' and state['of_port'] != '1':
        of_dpid = state['of_dpid']
        of_port = state['of_port']
net.get_available_actions(f'of:{of_dpid}', of_port)
print('*** AVAILABLE ACTIONS ***')
print(net.actions)
action = random.choice(net.actions)  # select random action
eth_src = action['eth_src']
eth_dst = action['eth_dst']
in_port = action['in_port']
out_port = action['out_port']
net.perform_action(of_dpid, out_port, in_port, eth_dst, eth_src)
print('*** NEW STATES ***')
net.get_states()
print(net.states)
print('*** REWARD ***')
net.get_reward()
print(net.reward)
print('Network created, tested, and terminated.')


# model = torch.nn.Sequential(
#     torch.nn.Linear(12, 64),
#     torch.nn.ReLU(),
#     torch.nn.Linear(64, 64),
#     torch.nn.ReLU(),
#     torch.nn.Linear(64, 4)
# )
# loss_fn = torch.nn.MSELoss()
# learning_rate = 0.0003
# optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
# gamma = 0.9
# epsilon = 0.4
# epochs = 100
# losses = []
# for i in range(epochs):
#     net = NetworkEnvironment
#     net.get_states()
#     state1 = net.states
#     status = 1
#     while (status == 1):
#         qval = model(state1)
#         qval_ = qval.data.numpy()
#         if (random.random() < epsilon):
#             action_ = np.random.randint(0, 4)
#         else:
#             action_ = np.argmax(qval_)
#         actions = net.get_available_actions(f'of:{of_dpid}', of_port)
#         action = random.choice(net.actions)  # select random action
#         eth_src = action['eth_src']
#         eth_dst = action['eth_dst']
#         in_port = action['in_port']
#         out_port = action['out_port']
#         net.perform_action(of_dpid, out_port, in_port, eth_dst, eth_src)
#         net.get_states()
#         state2 = net.states
#         reward = net.get_reward()
#         with torch.no_grad():
#             newQ = model(state2.rehsape(1, 12))
#         maxQ = torch.max(newQ)
#         if reward == -1:
#             Y = reward + (gamma * maxQ)
#         else:
#             Y = reward
#         Y = torch.Tensor([Y]).detach()
#         X = qval.squeeze()[action_]
#         loss = loss_fn(X, Y)
#         optimizer.zero_grad()
#         loss.backward()
#         losses.append(loss.item())
#         optimizer.step()
#         state1 = state2
#         if reward != -1:
#             status = 0
#     if epsilon > 0.1:
#         epsilon -= (1/epochs)
