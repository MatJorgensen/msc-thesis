#!/usr/bin/python
from network_environment import NetworkEnvironment
import time

duration = 20  # duration of traffic generation and monitoring

start = time.time()  # used for testing
net = NetworkEnvironment()
net.my_test(duration)
net.generate_json_data(duration + 15)  # ensure duration for 'generate_json_data()' is 15 seconds longer than 'my_test()'
net.cleanup()
end = time.time()  # used for testing
print('Network created, tested, and terminated.')
print(f'Total execution time: {start - end}.')
