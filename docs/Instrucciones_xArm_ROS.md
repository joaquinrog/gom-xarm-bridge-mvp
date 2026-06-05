# xArm ROS — Setup Instructions (Official)

## 1. Create a catkin workspace

If you already have a workspace, skip to the next part.
Follow the instructions at the ROS wiki. This guide assumes `~/catkin_ws` as the workspace directory.

## 2. Obtain the package

```bash
cd ~/catkin_ws/src
git clone https://github.com/xArm-Developer/xarm_ros.git --recursive
```

## 3. Update the package

```bash
cd ~/catkin_ws/src/xarm_ros

# If you did not use --recursive when cloning, initialize and update all submodules
git submodule update --init --recursive

# Pull the main repository and update submodules
git pull --recurse-submodules
```

## 4. Install other dependent packages

```bash
rosdep update
rosdep check --from-paths . --ignore-src --rosdistro kinetic
```

> Change `kinetic` to the ROS distribution you use (e.g. `noetic`).

If there are missing dependencies:

```bash
rosdep install --from-paths . --ignore-src --rosdistro kinetic -y
```

## 5. Build the code

```bash
cd ~/catkin_ws
catkin_make
```

## 6. Source the setup script

```bash
echo "source ~/catkin_ws/devel/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

> Skip the `echo` line if it is already in your `~/.bashrc`.

## 7. Try out in RViz (simulation)

```bash
roslaunch xarm_description xarm7_rviz_display.launch
```

## 8. Move the real robot

```bash
roslaunch xarm5_moveit_config realMove_exec.launch robot_ip:=<your controller box LAN IP address> [velocity_control:=false] [report_type:=normal]
```
