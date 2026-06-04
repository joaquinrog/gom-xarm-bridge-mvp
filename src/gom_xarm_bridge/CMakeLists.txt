cmake_minimum_required(VERSION 3.0.2)
project(gom_xarm_bridge)

find_package(catkin REQUIRED COMPONENTS rospy xarm_msgs)

catkin_package()

catkin_install_python(
  PROGRAMS scripts/bridge_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
