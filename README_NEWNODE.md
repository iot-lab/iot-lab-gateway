How allow the monitoring of a new node by the Gateway
=====================================================

# Define a new udev rule
1/. Use the command udevadm info on the rigth path
2/. Collect the idvendor, idproduct and idserial of your device
3/. Define the udev rules in the file /etc/udev/rules.d/iot-lab-ftdi.rules with the previous information
# Find the good configuration for openocd (or other)
1/. Find the good configuration file (.cfg)
2/. Put it in gateway_code/static
# Define a new class for your open node
1/. Create a new classe for your open node in the file open_node.py
2/. Create all the necessary functions
3/. Change the class rest_server.py to allow new experiment, flash, .. form the outside
4/. Write an idle firmware to rest the battery

# Allow testing on your node
1/. Write some integration tests
2/. Write an autotest firmware for the self-checking of the good working of the node's embedded compenents

# Case of Arduino

Warning : some arduino can't be reset by serial if your firmware don't support it (Mega and leonardo have a reset which can be done with any software)
stop /start serial with a specific beforme programming