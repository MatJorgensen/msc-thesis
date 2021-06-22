#!/usr/bin/env python

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController
from mininet.node import Host
from mininet.node import OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import TCLink
from time import sleep


class TopoOne(Topo):
    """Basic topology used to implement and test correct functionality of sFlow-RT."""
    def build(self):
        h1 = self.addHost('h1', cls=Host, ip='10.0.0.1', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', cls=Host, ip='10.0.0.2', mac='00:00:00:00:00:02')

        s1 = self.addSwitch('s1', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch, protocols='OpenFlow13')

        self.addLink(h1, s1, cls=TCLink, bw=10)
        self.addLink(h2, s2, cls=TCLink, bw=10)
        self.addLink(s1, s2, cls=TCLink, bw=10)


class TopoTwo(Topo):
    """Simple topology used to test that flows can be correctly updated using ONOS."""
    def build(self):
        h1 = self.addHost('h1', cls=Host, ip='10.0.0.1', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', cls=Host, ip='10.0.0.2', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', cls=Host, ip='10.0.0.3', mac='00:00:00:00:00:03')

        s1 = self.addSwitch('s1', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s3 = self.addSwitch('s3', cls=OVSKernelSwitch, protocols='OpenFlow13')

        self.addLink(h1, s1, cls=TCLink, bw=10)
        self.addLink(h2, s1, cls=TCLink, bw=10)
        self.addLink(h3, s2, cls=TCLink, bw=10)
        self.addLink(s1, s2, cls=TCLink, bw=10)
        self.addLink(s1, s3, cls=TCLink, bw=10)
        self.addLink(s2, s3, cls=TCLink, bw=10)


class TopoThree(Topo):
    """Simple topology used to train and test the functionality of the CAN."""
    def build(self):
        h1 = self.addHost('h1', cls=Host, ip='10.0.0.1', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', cls=Host, ip='10.0.0.2', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', cls=Host, ip='10.0.0.3', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', cls=Host, ip='10.0.0.4', mac='00:00:00:00:00:04')

        s1 = self.addSwitch('s1', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s3 = self.addSwitch('s3', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s4 = self.addSwitch('s4', cls=OVSKernelSwitch, protocols='OpenFlow13')

        self.addLink(h1, s1, cls=TCLink, bw=10)
        self.addLink(h1, s2, cls=TCLink, bw=10)
        self.addLink(h2, s1, cls=TCLink, bw=10)
        self.addLink(h2, s2, cls=TCLink, bw=10)
        self.addLink(h3, s3, cls=TCLink, bw=10)
        self.addLink(h3, s4, cls=TCLink, bw=10)
        self.addLink(h4, s3, cls=TCLink, bw=10)
        self.addLink(h4, s4, cls=TCLink, bw=10)
        self.addLink(s1, s2, cls=TCLink, bw=10)
        self.addLink(s1, s3, cls=TCLink, bw=10)
        self.addLink(s1, s4, cls=TCLink, bw=10)
        self.addLink(s2, s3, cls=TCLink, bw=10)
        self.addLink(s2, s4, cls=TCLink, bw=10)
        self.addLink(s3, s4, cls=TCLink, bw=10)


class TopoFour(Topo):
    """An advanced topology used to train and test the functionality of the CAN."""
    def build(self):
        return
        # TODO: Define topology


class ONOSController(RemoteController):
    """The ONOS SDN controller."""
    def build(self, name):
        self.ip = '127.0.0.1'
        self.port = 6633
        self.protocol = 'tcp'


def test_one(net, time=30):
    """Generates TCP traffic between a client host h1 and server host h2."""
    h1, h2 = net.get('h1', 'h2')
    print(f'*** Starting iPerf server')
    h1.cmd('iperf -s &')
    sleep(1)    # sleep to prevent connection error using iperf
    print(f'*** Generating traffic')
    h2.sendCmd(f'iperf -c {h1.IP()} -t{time}')
    print(h2.waitOutput())


def test_two(net, time=30):
    """Generates TCP traffic between two client hosts h1 and h2, respectively, and a server host h3."""
    h1, h2, h3 = net.get('h1', 'h2', 'h3')
    print(f'*** Starting iPerf server')
    h3.cmd('iperf -s &')
    sleep(1)    # sleep to prevent connection error using iperf
    print('*** Generating traffic')
    h1.sendCmd(f'iperf -c {h3.IP()} -t {time}')
    h2.sendCmd(f'iperf -c {h3.IP()} -t {time}')
    for h in (h1, h2):
        print(h.waitOutput())


def test_three(net, time=30):
    """Generates TCP traffic between four client hosts h1, h2, h4, and h5, respectively, and two server hosts h3 and h6."""
    h1, h2, h3, h4, h5, h6 = net.get('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
    print(f'*** Starting iPerf servers')
    h3.cmd('iperf -s &')
    h6.cmd('iperf -s &')
    sleep(1)    # sleep to prevent connection error using iperf
    print('*** Generating traffic')
    h1.sendCmd(f'iperf -c {h6.IP()} -t {time}')
    h2.sendCmd(f'iperf -c {h6.IP()} -t {time}')
    h4.sendCmd(f'iperf -c {h3.IP()} -t {time}')
    h5.sendCmd(f'iperf -c {h3.IP()} -t {time}')
    for h in (h1, h2, h4, h5):
        print(h.waitOutput())


def test_four(net):
    """Generates TCP traffic..."""
    # TODO: Define traffic pattern
    return


def test_five(net):
    """Generates random TCP and UDP traffic, mimicking a real-world traffic pattern."""
    # TODO: Define traffic pattern
    return


topos = {'topo1': TopoOne,
         'topo2': TopoTwo,
         'topo3': TopoThree,
         'topo4': TopoFour}

controllers = {'onos': ONOSController}

tests = {'test1': test_one,
         'test2': test_two,
         'test3': test_three,
         'test4': test_four,
         'test5': test_five}

if __name__ == 'mininet_topologies':
    setLogLevel('info')
    net = Mininet(topo=TopoOne, controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6633, protocol='tcp'))
    net.start()
    CLI(net)
    net.stop()
