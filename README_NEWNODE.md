How allow the monitoring of a new node by the Gateway
=====================================================

# Define a new udev rule
Your system 
1/. Define the udev rules in the file /etc/udev/rules.d/iot-lab-ftdi.rules
# Find the good configuration for openocd
1/. Set the good configuration file (.cfg) for openocd (gateway_code/static)
# Define a class for your
1/. In the file open_node.py,

# Allow testing on your node
1/. Write some integration tests
2/. Write an autotest firmware for the self-checking of the good working of the node's embedded compenents