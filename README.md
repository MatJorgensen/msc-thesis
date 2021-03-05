<img src="https://images.squarespace-cdn.com/content/5b052242506fbe7ea6c0969c/1539868936426-869NHDYJ3T0P9JJE2G5J/DTU_Logo_Corporate_Red_RGB.png?format=1500w&content-type=image%2Fpng" width="96">

# Cognitive Autonomous Networks: Optimizing Quality-of-Service Using Deep Learning
Source code for my master thesis Cognitive Autonomous Networks: Optimizing Quality-of-Service Using Deep Learning at the Technical University of Denmark.

## Configuring VM
All components of the project is developed in a Ubuntu 20.04 LTS virtual machine. The following is a description on how to install Mininet, sFlow-RT, ONOS, PyTorch, and how to configure the development environment.

### Install package dependencies
```
sudo apt install git zip curl unzip python python3
```

### Install Mininet
```
git clone -b 2.3.0 --single-branch git://github.com/mininet/mininet
mininet/util/install.sh -a
```

Test correct installation by executing command `sudo mn --test pingall`.

### Install sFlow-RT (and OpenJDK 11)
```
sudo apt install openjdk-11-jdk
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
wget https://inmon.com/products/sFlow-RT/sflow-rt.tar.gz
tar -xvzf sflow-rt.tar.gz
./sflow-rt/start.sh
```

### Install ONOS (and Bazelisk)
```
wget https://github.com/bazelbuild/bazelisk/releases/download/v1.7.5/bazelisk-linux-amd64
chmod +x bazelisk-linux-amd64
sudo mv bazelisk-linux-amd64 /usr/local/bin/bazel
git clone -b 2.5.1 --single-branch https://github.com/opennetworkinglab/onos
export ONOS_ROOT=~/onos
source $ONOS_ROOT/tools/dev/bash_profile
cd $ONOS_ROOT
bazel version
bazel build onos
```

To enable `proxyarp` and `fwd` as default ONOS apps execute the command `export ONOS_APPS=$ONOS_APPS,proxyarp,fwd`.


### PyTorch


### Set environmental variables (for ease of use)
Add the following lines to `~/.profile` to export environmental variables on startup.

export PATH="$PATH:/home/mbj/onos/tools/test/bin
export ONOS_CELL=local
export ONOS_APPS=drivers,openflow,gui2,proxyarp,fwd
export ONOS_WEB_USER=onos
export ONOS_ROOT=/home/student/onos
export ONOS_WEB_PASS=rocks
