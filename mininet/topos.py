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
        s3 = self.addSwitch('s2', cls=OVSKernelSwitch, protocols='OpenFlow13')

        # Create links
        self.addLink(h1, s1, cls=TCLink, bw=10)
        self.addLink(h2, s2, cls=TCLink, bw=10)
        self.addLink(h3, s3, cls=TCLink, bw=10)
        self.addLink(s1, s2, cls=TCLink, bw=10)
        self.addLink(s1, s3, cls=TCLink, bw=10)
        self.addLink(s2, s3, cls=TCLink, bw=10)


class TopoThree(Topo):
    """"""


class TopoFour(Topo):
    """"""


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


def run_topo_three():
    return


def run_topo_three():
    return


def run_topo_four():
    return


def run_topo_five():
    return


topos = {'topo1': (lambda: TopoOne()),
         'topo2': (lambda: TopoTwo()),
         'topo3': (lambda: TopoThree()),
         'topo4': (lambda: TopoFour()),
         'topo5': (lambda: TopoFive())}

controllers = {'onos': ONOSController}

if __name__ == '__main__':
    setLogLevel('info')
    net = Mininet(topo=TopoOne(), controller=lambda name: RemoteController(name, ip='127.0.0.1', port=6653, protocol='tcp'))
    net.start()
    CLI(net)
    net.stop()
