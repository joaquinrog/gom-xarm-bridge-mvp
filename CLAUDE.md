# gom-xarm-bridge-mvp

Bridge ROS 1 que conecta un escáner 3D ATOS Core (GOM Inspect, Windows) con un brazo robótico xArm 5-axis (Linux). Un script Python en Windows detecta la exportación manual de un CSV desde GOM Inspect, extrae las coordenadas X,Y del centroide de la pieza y las manda por TCP al nodo ROS en Linux, que mueve el efector final a esa posición.

## Stack

- **ROS 1 Noetic** + Python 3, catkin workspace
- **xarm_ros** (oficial UFactory) — dependencia externa, no modificar
- **watchdog** (pip) — solo en Windows

## Estructura del repo

```
xArm-cobot/
├── src/
│   ├── xarm_ros/              ← symlink → repo/xarm_ros (dependencia, ignorada en git)
│   └── gom_xarm_bridge/       ← paquete ROS propio
│       └── scripts/
│           └── bridge_node.py ← servidor TCP + llamada /xarm/move_line
├── windows_scripts/
│   └── gom_watcher.py         ← vigila carpeta CSV en la PC Windows
└── repo/
    └── xarm_ros/              ← clon del upstream (ignorado en git)
```

## Setup local (primera vez)

```bash
# 1. Clonar xarm_ros como dependencia
mkdir -p repo
git clone https://github.com/xArm-Developer/xarm_ros.git repo/xarm_ros --recursive

# 2. Crear symlink para que catkin lo encuentre
mkdir -p src
ln -s $(pwd)/repo/xarm_ros src/xarm_ros

# 3. Build
catkin_make
source devel/setup.bash
```

## Arranque

```bash
# Terminal 1 — driver del robot + MoveIt + RViz (sustituir IP real)
roslaunch xarm5_moveit_config realMove_exec.launch robot_ip:=192.168.31.xxx velocity_control:=false report_type:=normal

# Terminal 2 — nodo bridge
rosrun gom_xarm_bridge bridge_node.py
```

```cmd
# PC Windows — vigilante de carpeta de exportación
python windows_scripts/gom_watcher.py
```

## Servicio ROS clave

`/xarm/move_line` (`xarm_msgs/Move`) — mueve el efector a posición Cartesiana absoluta en mm.

Pose: `[x_mm, y_mm, z_mm, roll_rad, pitch_rad, yaw_rad]`

## Parámetros a calibrar antes de usar

En `src/gom_xarm_bridge/scripts/bridge_node.py`:

| Variable | Descripción |
|----------|-------------|
| `Z_FIXED` | Altura del efector sobre la mesa (mm) |
| `ROLL / PITCH / YAW` | Orientación del efector (rad) |
| `SPEED` | Velocidad de movimiento (mm/s) |

En `windows_scripts/gom_watcher.py`:

| Variable | Descripción |
|----------|-------------|
| `WATCH_DIR` | Carpeta donde GOM exporta el CSV |
| `ROBOT_IP` | IP de la PC Linux |
| `FEATURE_NAME` | Texto que identifica la fila del centroide en el CSV |
| `COL_X / COL_Y` | Nombres exactos de las columnas X e Y del CSV de GOM |

## Advertencia de seguridad

El sistema de coordenadas del escáner ATOS ≠ frame `world` del xArm. Calibrar la transformación rígida (mínimo 3 puntos conocidos en ambos sistemas) antes de ejecutar con coordenadas reales del escáner.
