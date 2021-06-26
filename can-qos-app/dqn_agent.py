#!/usr/bin/python
from network_environment import NetworkEnvironment
import time

duration = 20  # duration of traffic generation and monitoring

start = time.time()  # used for testing
net = NetworkEnvironment()
net.cli()
#net.select_action()
#net.my_test(duration)
#time.sleep(5)
#stop_in = time.time() + 5
#while time.time() < stop_in:
#    print(net.get_state())
#    time.sleep(1)
#net.generate_json_data(duration + 15)  # ensure duration for 'generate_json_data()' is 15 seconds longer than 'my_test()'
#net.cleanup()
#end = time.time()  # used for testing
print('Network created, tested, and terminated.')
#print(f'Total execution time: {start - end}.')
