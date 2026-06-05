# Instrucciones xArm 5 — ROS (Smart Factory Lab)

## 1. Crear el workspace y clonar el repositorio de xArm ROS

```bash
mkdir -p ~/xarm_ws/src
cd ~/xarm_ws/src
rm -rf xarm_ros
git clone --recursive https://github.com/xArm-Developer/xarm_ros.git
```

### Alternativa: instalar desde ZIP (USB)

```bash
# Primero busca dónde está montada la USB
lsblk

# Descomprime el zip desde la USB
cd /media/smart2/08E4-926E
unzip xarm_ros-master.zip

# Cópialo al workspace
cp -r xarm_ros-master ~/xarm_ws/src/xarm_ros
```

## 2. Actualizar submódulos

```bash
cd ~/xarm_ws/src/xarm_ros

# Si no usaste --recursive al clonar, inicializa y actualiza todos los submódulos
git submodule update --init --recursive

# Pull del repositorio principal y actualización de submódulos
git pull --recurse-submodules
```

## 3. Instalar dependencias

```bash
cd ~/xarm_ws
rosdep install --from-paths src --ignore-src -r -y
rosdep update
rosdep check --from-paths . --ignore-src --rosdistro kinetic
rosdep install --from-paths . --ignore-src --rosdistro kinetic -y
```

> Sustituir `kinetic` por la distribución ROS que uses (p. ej. `noetic`).

## 4. Compilar el workspace

```bash
cd ~/xarm_ws
catkin_make
```

## 5. Cargar el workspace compilado

```bash
cd ~/xarm_ws
source ~/xarm_ws/devel/setup.bash
```

## 6. Lanzar driver y conectar al robot

### Con MoveIt y RViz

```bash
roslaunch xarm5_moveit_config realMove_exec.launch robot_ip:=192.168.31.xxx [velocity_control:=false] [report_type:=normal]
```

### Con xarm_api (solo driver)

```bash
roslaunch xarm_bringup xarm5_server.launch robot_ip:=192.168.31.xxx
```

---

> **Nota:** Si ya completaste los pasos de instalación, cada vez que inicies solo necesitas el paso 5 en adelante.
