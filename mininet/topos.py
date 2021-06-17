#!/usr/bin/python

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController
from mininet.node import Host
from mininet.node import OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.log import info
from mininet.link import TCLink
from time import sleep

# Mininet command...
# sudo mn --custom sflow-rt/extras/sflow.py --link tc,bw=10 --controller remote --topo tree,2,2 --switch ovs,protocols=OpenFlow13


class TopoOne(Topo):
    """Simple topology with a h1-s1-s2-h2 architecture used to implement and test correct functionality of sFlow-RT."""
    def build(self):
        # Create hosts
        h1 = self.addHost('h1', cls=Host, ip='10.0.0.1', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', cls=Host, ip='10.0.0.2', mac='00:00:00:00:00:02')

        # Create switches
        s1 = self.addSwitch('s1', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch, protocols='OpenFlow13')

        # Create links
        self.addLink(h1, s1, cls=TCLink, bw=10)
        self.addLink(h2, s2, cls=TCLink, bw=10)
        self.addLink(s1, s2, cls=TCLink, bw=10)


class TopoTwo(Topo):
    """Simply topology used to test that flows can be correctly changed using ONOS.

     h1 -- s1 -- s2 -- h2
            \    /
             \  /
              s3
              |
              h3
    """
    def build(self):
        # Create hosts
        h1 = self.addHost('h1', cls=Host, ip='10.0.0.1', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', cls=Host, ip='10.0.0.2', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', cls=Host, ip='10.0.0.3', mac='00:00:00:00:00:03')

        # Create switches
        s1 = self.addSwitch('s1', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s3 = self.addSwitch('s3', cls=OVSKernelSwitch, protocols='OpenFlow13')

        # Create links
        self.addLink(h1, s1, cls=TCLink, bw=10)
        self.addLink(h2, s2, cls=TCLink, bw=10)
        self.addLink(h3, s3, cls=TCLink, bw=10)
        self.addLink(s1, s2, cls=TCLink, bw=10)
        self.addLink(s1, s3, cls=TCLink, bw=10)
        self.addLink(s2, s3, cls=TCLink, bw=10)


class TopoThree(Topo):
    """"""
    def build(self):
        # Create hosts
        h1 = self.addHost('h1', cls=Host, ip='10.0.0.1', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', cls=Host, ip='10.0.0.2', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', cls=Host, ip='10.0.0.3', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', cls=Host, ip='10.0.0.4', mac='00:00:00:00:00:04')
        h5 = self.addHost('h5', cls=Host, ip='10.0.0.5', mac='00:00:00:00:00:05')
        h6 = self.addHost('h6', cls=Host, ip='10.0.0.6', mac='00:00:00:00:00:06')

        # Create switches
        s1 = self.addSwitch('s1', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s3 = self.addSwitch('s3', cls=OVSKernelSwitch, protocols='OpenFlow13')

        # Create links
        self.addLink(h1, s1, cls=TCLink, bw=10)
        self.addLink(h2, s1, cls=TCLink, bw=10)
        self.addLink(h3, s1, cls=TCLink, bw=10)
        self.addLink(h4, s2, cls=TCLink, bw=10)
        self.addLink(h5, s2, cls=TCLink, bw=10)
        self.addLink(h6, s2, cls=TCLink, bw=10)
        self.addLink(s1, s2, cls=TCLink, bw=10)
        self.addLink(s1, s3, cls=TCLink, bw=10)
        self.addLink(s2, s3, cls=TCLink, bw=10)



class TopoFour(Topo):
    """"""
    def build(self):
        # Create hosts
        h1 = self.addHost('h1', cls=Host, ip='10.0.0.1', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', cls=Host, ip='10.0.0.2', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', cls=Host, ip='10.0.0.3', mac='00:00:00:00:00:03')
        h4 = self.addHost('h4', cls=Host, ip='10.0.0.4', mac='00:00:00:00:00:04')

        # Create switches
        s1 = self.addSwitch('s1', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s3 = self.addSwitch('s3', cls=OVSKernelSwitch, protocols='OpenFlow13')
        s4 = self.addSwitch('s4', cls=OVSKernelSwitch, protocols='OpenFlow13')

        # Create links
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


class TopoFive(Topo):
    """"""


class ONOSController(RemoteController):
    """The ONOS SDN controller"""
    def build(self, name):
        self.ip = '127.0.0.1'
        self.port = 6653
        self.protocol = 'tcp'


def run_topo_one():
    return


def run_topo_two():
    return


def generate_traffic_topo_three(net):
    net.pingAll()
    h1, h2, h3, h4, h5, h6 = net.get('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
    print('*** Starting iPerf servers')
    h3.cmd('iperf -s &')
    h6.cmd('iperf -s &')
    sleep(1)    # sleep to prevent connection error using iperf
    print('*** Generating traffic')
    h1.sendCmd(f'iperf -c {h6.IP()} -t 30')
    h2.sendCmd(f'iperf -c {h6.IP()} -t 30')
    h4.sendCmd(f'iperf -c {h3.IP()} -t 30')
    h5.sendCmd(f'iperf -c {h3.IP()} -t 30')
    for host in (h1, h2, h4, h5):
        print(host.waitOutput())
    CLI(net)



def run_topo_four():
    return


def run_topo_five():
    return


topos = {'topo1': TopoOne,
         'topo2': TopoTwo,
         'topo3': TopoThree,
         'topo4': TopoFour,
         'topo5': TopoFive}

controllers = {'onos': ONOSController}

tests = {'test3': generate_traffic_topo_three}


if __name__ == '__main__':
    setLogLevel('info')
    net = Mininet(topo=TopoThree(), controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6653, protocol='tcp'))
    net.start()
    CLI(net)
    net.stop()
