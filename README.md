# gom-xarm-bridge-mvp

> A lightweight ROS 1 bridge that connects a GOM Inspect 3D scanner (Windows) to a UFactory xArm 5-axis robot (Linux) using only free tools, a TCP socket, and two Python scripts.

---

## The Problem

Industrial quality inspection and robotic manipulation are usually separate islands. A metrology station measures a part, an engineer reads the numbers, manually enters coordinates into a robot controller, and the robot moves. This project removes the human in the middle.

The catch: GOM Inspect's Python scripting API is locked behind a Professional license. This project works around that entirely — no license upgrade needed.

---

## How It Works

```
┌──────────────────────────┐          ┌─────────────────────────────────┐
│       Windows PC         │          │          Linux PC (ROS)         │
│                          │          │                                 │
│  ATOS Core 3D Scanner    │          │  xArm 5-axis Robot              │
│         ↓                │          │         ↑                       │
│  GOM Inspect 2019 Free   │          │  /xarm/move_line service        │
│  (operator exports CSV)  │          │         ↑                       │
│         ↓                │  TCP     │  bridge_node.py                 │
│  gom_watcher.py          │─────────▶│  (ROS node, TCP server)         │
│  (detects file,          │  :9999   │                                 │
│   parses X,Y,            │  JSON    │                                 │
│   sends JSON)            │          │                                 │
└──────────────────────────┘          └─────────────────────────────────┘
```

**Operator workflow (3 steps):**
1. Scan the part with the ATOS Core scanner.
2. In GOM Inspect: `File → Export → Feature List → Save as CSV` (two clicks).
3. The rest is automatic — the watcher script detects the file, extracts the centroid coordinates, and the robot arm moves to the correct position within ~1 second.

---

## Why This Matters — Smart Factory Vision

This MVP is intentionally minimal, but it demonstrates the core pattern behind modern adaptive manufacturing:

**Inspect → Decide → Act**, closed-loop, without human intervention.

Some directions this architecture can grow into:

| Upgrade | What it unlocks |
|---|---|
| Replace CSV export with OCR on GOM's screen | Zero manual clicks — fully autonomous loop |
| Add a coordinate transformation node | Map scanner frame → robot frame automatically after a one-time calibration |
| Add a depth camera (e.g. RealSense) | Real-time part detection without a dedicated metrology station |
| Extend bridge to publish on a ROS topic | Multiple robots or downstream nodes subscribe and react |
| Add MoveIt for path planning | Collision-aware trajectories, not just point-to-point moves |
| Connect to a MES / SCADA system | The robot reports results back to the factory management layer |

The idea that a scanner can _tell_ a robot where to go — and the robot just goes — is the building block of lights-out manufacturing cells. This project proves the concept works with off-the-shelf, license-free tools.

---

## Repository Structure

```
gom-xarm-bridge-mvp/
├── src/
│   └── gom_xarm_bridge/          # ROS 1 package (runs on Linux)
│       ├── package.xml
│       ├── CMakeLists.txt
│       └── scripts/
│           └── bridge_node.py    # TCP server + xArm service caller
├── windows_scripts/
│   └── gom_watcher.py            # File watcher + CSV parser (runs on Windows)
├── CLAUDE.md                     # Context file for Claude Code sessions
└── README.md
```

`xarm_ros` (the official UFactory ROS driver) is a separate dependency cloned locally — it is not included in this repository.

---

## Prerequisites

**Linux PC:**
- ROS 1 Noetic
- `catkin` build tools
- Python 3
- xArm 5-axis robot reachable on the local network

**Windows PC:**
- Python 3
- `watchdog` library (`pip install watchdog`)
- GOM Inspect 2019 (any edition, including Basic/Free)

Both machines must be on the same local network.

---

## Setup

### Linux

```bash
# 1. Clone this repo
git clone https://github.com/<your-user>/gom-xarm-bridge-mvp.git xArm-cobot
cd xArm-cobot

# 2. Clone the xarm_ros dependency
mkdir -p repo
git clone https://github.com/xArm-Developer/xarm_ros.git repo/xarm_ros --recursive

# 3. Link xarm_ros into the catkin workspace
mkdir -p src
ln -s $(pwd)/repo/xarm_ros src/xarm_ros

# 4. Build
catkin_make
source devel/setup.bash
```

### Windows

```cmd
pip install watchdog
```

Open `windows_scripts/gom_watcher.py` and set these four variables at the top of the file:

```python
WATCH_DIR    = r"C:\GOM_Exports"   # folder where GOM saves the CSV
ROBOT_IP     = "192.168.1.100"     # IP address of the Linux PC
FEATURE_NAME = "Center"            # text that identifies the centroid row in the CSV
COL_X        = "X [mm]"           # exact column name for X in your GOM export
COL_Y        = "Y [mm]"           # exact column name for Y in your GOM export
```

> **Tip:** Export one test CSV from GOM Inspect first and open it in a text editor to confirm the exact column names and delimiter (`;` or `,`) before running the script.

---

## Running

**Linux — two terminals:**

```bash
# Terminal 1: start the xArm hardware driver (replace with your robot's IP)
roslaunch xarm_bringup xarm5_server.launch robot_ip:=192.168.1.xxx

# Terminal 2: start the bridge node
rosrun gom_xarm_bridge bridge_node.py
```

**Windows:**

```cmd
python windows_scripts\gom_watcher.py
```

---

## Configuration Reference

These values in `bridge_node.py` define where and how the robot moves. Set them once to match your physical setup:

| Parameter | Default | Description |
|---|---|---|
| `Z_FIXED` | `100.0` | Tool height above the table surface (mm) |
| `ROLL` | `π (3.1416)` | Tool orientation — default points end-effector downward |
| `PITCH` | `0.0` | Tool pitch (rad) |
| `YAW` | `0.0` | Tool yaw (rad) |
| `SPEED` | `80.0` | Movement speed (mm/s) — keep low during initial testing |
| `ACC` | `300.0` | Acceleration (mm/s²) |
| `TCP_PORT` | `9999` | Port the bridge listens on |

---

## ⚠️ Coordinate Calibration (Required Before Production Use)

The ATOS scanner and the xArm robot live in different coordinate frames. Sending raw scanner coordinates to the robot will result in incorrect positions.

Before using real scan data, perform a hand-eye calibration:
1. Place at least 3 reference markers at known positions on the table.
2. Record the X,Y position of each marker in both the GOM Inspect frame and the robot's base frame.
3. Compute the rigid transformation (rotation + translation) between the two frames.
4. Apply this transformation in `bridge_node.py` before calling `/xarm/move_line`.

For an MVP on a flat table, this reduces to a 2D affine transform (4 parameters).

---

## Tech Stack

| Component | Technology |
|---|---|
| 3D Scanner | ATOS Core (GOM / Zeiss) |
| Metrology Software | GOM Inspect 2019 Free |
| Robot | UFactory xArm 5-axis |
| Robot Middleware | ROS 1 Noetic |
| Robot Driver | [xarm_ros](https://github.com/xArm-Developer/xarm_ros) |
| Communication | TCP socket, JSON payload |
| File Watching | Python `watchdog` |

---

## Limitations of This MVP

- **Manual export step:** the operator must click "Export CSV" in GOM Inspect. This is a consequence of the Basic license restriction.
- **No coordinate transformation:** raw scanner coordinates are sent as-is. See the calibration section above.
- **Single part at a time:** the bridge processes one CSV file per scan cycle.
- **No error recovery:** if the robot fails mid-move, the bridge logs the error but does not retry or alert the operator.

---

## Tutorial: Puesta en Marcha desde Cero

> **Audiencia:** operador con conocimientos básicos de Windows y Linux mínimos.
> **Punto de partida:** Windows 11 con GOM Scan 2019 y GOM Inspect 2019 ya instalados; PC Linux con Ubuntu (estado desconocido).
> **Tiempo estimado:** 2–3 horas la primera vez. Ciclos posteriores: ~5 minutos.

---

### Parte 0 — Requisitos de Red

Los dos PCs deben verse en la misma red local antes de continuar.

**0.1 Obtener las IPs**

En Windows (Win → buscar "cmd"):
```cmd
ipconfig
```
Anota el valor de `Dirección IPv4` de tu adaptador (p. ej. `192.168.1.50`).

En Linux (abre una terminal):
```bash
ip addr show
```
Anota la IP de la interfaz activa (`eth0`, `enp3s0`, etc. — busca `inet 192.168.1.xxx`).

**0.2 Verificar conectividad**

```cmd
# Desde Windows hacia Linux
ping 192.168.1.100
```
```bash
# Desde Linux hacia Windows
ping 192.168.1.50
```
Ambos deben recibir respuestas. Si no, revisa que ambas máquinas estén en el mismo switch/router y subred.

**0.3 Abrir el puerto TCP 9999 en Linux** (solo si el ping funciona pero luego hay `ConnectionRefusedError`)

```bash
sudo ufw allow 9999/tcp
```

---

### Parte 1 — Calibración del ATOS Core

El ATOS Core viene **pre-calibrado de fábrica**. Solo necesitas recalibrar cuando el software lo indica.

**¿Cuándo recalibrar?** GOM Scan / GOM Inspect muestra un aviso en pantalla cuando la calibración ha caducado o la temperatura del escáner ha variado demasiado. Si no aparece ningún aviso, salta a la Parte 2.

**Procedimiento de recalibración:**
1. Saca el panel de calibración de su estuche (panel plano con targets circulares).
2. En GOM Inspect: `Herramientas → Calibrar escáner` (o en GOM Scan: `Scanner → Calibrate`).
3. El asistente guía paso a paso: coloca el panel en las orientaciones indicadas en pantalla (generalmente 3–5 posiciones).
4. Al finalizar, el software confirma `Calibration successful` con la desviación residual.

> Referencia visual: busca **"Calibrating Our GOM ATOS Core 300 3D Scanner"** en YouTube para ver el proceso completo.

---

### Parte 2 — Configuración en Windows

**2.1 Verificar / instalar Python 3**

```cmd
python --version
```
Si responde `Python 3.x.x`, continúa. Si no, descarga el instalador desde [python.org/downloads](https://www.python.org/downloads/) y marca **"Add Python to PATH"** durante la instalación.

**2.2 Instalar la dependencia `watchdog`**

```cmd
pip install watchdog
```

**2.3 Crear la carpeta de exportación**

```cmd
mkdir C:\GOM_Exports
```

**2.4 Configurar `gom_watcher.py`**

Abre `windows_scripts\gom_watcher.py` con el Bloc de notas. Localiza el bloque de configuración al inicio del archivo y ajusta:

```python
WATCH_DIR    = r"C:\GOM_Exports"   # no cambiar si usaste el paso 2.3
ROBOT_IP     = "192.168.1.100"     # ← CAMBIAR a la IP real del PC Linux (Parte 0.1)
FEATURE_NAME = "Center"            # nombre del feature de centroide en GOM Inspect
COL_X        = "X [mm]"           # encabezado exacto de la columna X en el CSV
COL_Y        = "Y [mm]"           # encabezado exacto de la columna Y en el CSV
```

> **Cómo confirmar los nombres de columna:** exporta un CSV de prueba (ver Parte 4, paso 4.3) y ábrelo con el Bloc de notas. La primera línea son los encabezados — copia el texto exacto, incluyendo espacios y corchetes.

**2.5 Verificar que el script arranca sin errores**

```cmd
python windows_scripts\gom_watcher.py
```
Salida esperada:
```
[INFO] Monitoreando: C:\GOM_Exports
[INFO] Robot: 192.168.1.100:9999
[INFO] Esperando exportación CSV de GOM Inspect...
```
Detén el script con `Ctrl+C`. El watcher no conecta con el robot hasta detectar un CSV nuevo — es normal que no muestre más nada.

---

### Parte 3 — Configuración en Linux

**3.1 Verificar ROS Noetic**

```bash
rosversion -d
```
Si responde `noetic`, salta al paso 3.2.

Si el comando no existe, instala ROS Noetic:
```bash
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
sudo apt install curl -y
curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
sudo apt update
sudo apt install ros-noetic-desktop-full -y
echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
source ~/.bashrc
sudo apt install python3-rosdep python3-rosinstall python3-catkin-tools build-essential -y
sudo rosdep init
rosdep update
```

**3.2 Preparar el workspace**

```bash
# Clona este repositorio si aún no lo tienes
git clone https://github.com/<tu-usuario>/gom-xarm-bridge-mvp.git ~/xArm-cobot
cd ~/xArm-cobot

# Clona el driver oficial de xArm como dependencia externa
mkdir -p repo
git clone https://github.com/xArm-Developer/xarm_ros.git repo/xarm_ros --recursive

# Crea el symlink para que catkin encuentre el paquete
mkdir -p src
ln -s $(pwd)/repo/xarm_ros src/xarm_ros
```

**3.3 Compilar**

```bash
source /opt/ros/noetic/setup.bash
catkin_make
source devel/setup.bash
```
La primera compilación tarda 3–8 minutos. Al finalizar debe aparecer `[100%] Built target ...`.

Añade el entorno al `.bashrc` para no repetirlo en cada terminal:
```bash
echo "source ~/xArm-cobot/devel/setup.bash" >> ~/.bashrc
```

**3.4 Checklist de verificación**

Ejecuta cada comando y confirma la salida esperada:

```bash
rosversion -d
# → noetic

rospack find gom_xarm_bridge
# → /home/<usuario>/xArm-cobot/src/gom_xarm_bridge

rospack find xarm_msgs
# → /home/<usuario>/xArm-cobot/src/xarm_ros/xarm_msgs

python3 -c "import rospy, xarm_msgs; print('Imports OK')"
# → Imports OK
```

Si algún comando falla, repasa los pasos 3.1–3.3.

**3.5 Parámetros del robot en `bridge_node.py`**

Ajusta estos valores en `src/gom_xarm_bridge/scripts/bridge_node.py` (líneas 17–22) antes de mover el robot real:

| Variable | Valor por defecto | Qué ajustar |
|---|---|---|
| `Z_FIXED` | `100.0` | Altura del efector sobre la mesa en mm — mídela con una regla |
| `SPEED` | `80.0` | Velocidad en mm/s — mantener ≤ 100 hasta validar trayectorias |
| `ACC` | `300.0` | Aceleración en mm/s² — no tocar en MVP |
| `ROLL` | `math.pi` | Efector apuntando hacia abajo — no tocar salvo cambio de herramienta |
| `TCP_PORT` | `9999` | Solo cambiar si hay conflicto de puertos (cambiar también en `gom_watcher.py`) |

---

### Parte 4 — Workflow de Medición Completo

**4.0 Arrancar el sistema (una vez por sesión)**

**Terminal Linux 1 — driver del robot:**
```bash
# Sustituye 192.168.1.xxx por la IP real del controlador del xArm
roslaunch xarm_bringup xarm5_server.launch robot_ip:=192.168.1.xxx
```
Espera hasta ver `xarm is connected!` en la salida.

**Terminal Linux 2 — habilitar servos** (los 3 comandos son obligatorios, en este orden):
```bash
rosservice call /xarm/motion_ctrl 8 1   # habilitar todos los motores
rosservice call /xarm/set_mode 0        # modo POSE (posición cartesiana)
rosservice call /xarm/set_state 0       # estado READY
```
Cada comando debe responder `ret: 0`. Si no, el robot rechazará cualquier movimiento.

**Terminal Linux 3 — nodo bridge:**
```bash
rosrun gom_xarm_bridge bridge_node.py
```
Salida esperada: `[INFO] [...] Bridge escuchando en 0.0.0.0:9999`

**Windows — watcher:**
```cmd
python windows_scripts\gom_watcher.py
```

**4.1 Escanear la pieza con el ATOS Core**

1. Coloca la pieza en el área de medición del escáner.
2. En GOM Scan 2019, inicia un nuevo proyecto o abre uno existente.
3. Realiza el escaneo completo (captura desde múltiples ángulos según necesidad).
4. Guarda el proyecto de escaneo.

**4.2 Medir el centroide en GOM Inspect**

1. Abre el archivo de escaneo en GOM Inspect 2019.
2. Si el centroide no está ya definido: `Insertar → Feature → Punto → Centroide de superficie`.
3. Asegúrate de que el feature se llame **"Center"** (o el valor de `FEATURE_NAME` que hayas configurado).

**4.3 Exportar el Feature List como CSV**

1. En GOM Inspect: `Archivo → Exportar → Lista de features`.
2. En el cuadro de diálogo:
   - Tipo de archivo: **CSV (*.csv)**
   - Directorio: `C:\GOM_Exports`
   - Separador: **punto y coma (`;`)**
3. Haz clic en **Guardar**.

El watcher en Windows responde inmediatamente:
```
[INFO] CSV detectado: C:\GOM_Exports\features_001.csv
[INFO] Centroide encontrado: X=123.456 Y=78.900
[OK]   Enviado al robot → X=123.456 Y=78.900
```

La Terminal Linux 3 confirma:
```
[INFO] [...] Recibido de ('192.168.1.50', 54321): {"x": 123.456, "y": 78.9}
[INFO] [...] Moviendo a X=123.46 Y=78.90 Z=100.0
[INFO] [...] Movimiento completado OK
```

**4.4 Diagnóstico de errores comunes**

| Síntoma | Causa probable | Solución |
|---|---|---|
| `[ERROR] No se pudo conectar a 192.168.1.100:9999` | `bridge_node.py` no corre, o IP incorrecta | Verifica Terminal Linux 3; revisa `ROBOT_IP` en `gom_watcher.py` |
| `[WARN] No se encontró ninguna fila con 'Center'` | Nombre del feature en GOM ≠ `FEATURE_NAME` | Ajusta `FEATURE_NAME` o renombra el feature en GOM Inspect |
| `[ERROR] Columnas no encontradas` | Encabezados CSV distintos a `COL_X`/`COL_Y` | Abre el CSV con Bloc de notas, copia los encabezados exactos |
| `xArm respondió ret=1` o `ret=11` | Robot en modo incorrecto | Repite la secuencia `motion_ctrl → set_mode → set_state` del paso 4.0 |
| Robot no se mueve, sin mensaje de error | Coordenadas fuera del espacio de trabajo | Verifica que X,Y estén dentro del alcance del brazo; reduce `Z_FIXED` |

---

### Parte 5 — Calibración Robot-Escáner (Obligatoria para Producción)

> Puedes saltarte esta parte en pruebas de desarrollo, pero las coordenadas que envíe el escáner no corresponderán a posiciones reales del robot.

**El problema:** el ATOS Core y el xArm miden en sistemas de coordenadas completamente distintos. Un punto `X=150, Y=80` en el escáner no es `X=150, Y=80` en el robot — hay rotación y traslación entre los dos marcos.

**Método de 3 puntos (mínimo viable)**

**Paso A — Preparar marcadores de referencia**

Coloca 3 marcadores físicos sobre la mesa (tornillos, círculos de cinta de colores, esferas de calibración). Deben:
- Estar separados entre sí al menos 150 mm.
- Ser visibles para el escáner **y** alcanzables por el efector del robot.
- No estar alineados en línea recta.

**Paso B — Medir los marcadores con GOM Inspect**

Escanea la mesa con los 3 marcadores y exporta sus coordenadas. Anota:

| Punto | X_escáner (mm) | Y_escáner (mm) |
|---|---|---|
| P1 | | |
| P2 | | |
| P3 | | |

**Paso C — Medir los mismos puntos con el robot**

Usa el modo jog del xArm (desde UFactory Studio o con las flechas del controlador) para mover el efector hasta que toque cada marcador. Lee la posición actual:
```bash
rostopic echo /xarm/xarm_states | grep -A 6 "pose"
```

| Punto | X_robot (mm) | Y_robot (mm) |
|---|---|---|
| P1 | | |
| P2 | | |
| P3 | | |

**Paso D — Calcular la transformación**

Ejecuta este script Python con tus valores medidos:

```python
import numpy as np

pts_scanner = np.array([
    [X1_gom, Y1_gom],
    [X2_gom, Y2_gom],
    [X3_gom, Y3_gom],
], dtype=float)

pts_robot = np.array([
    [X1_robot, Y1_robot],
    [X2_robot, Y2_robot],
    [X3_robot, Y3_robot],
], dtype=float)

A = np.hstack([pts_scanner, np.ones((3, 1))])
coeff_x, _, _, _ = np.linalg.lstsq(A, pts_robot[:, 0], rcond=None)
coeff_y, _, _, _ = np.linalg.lstsq(A, pts_robot[:, 1], rcond=None)

print("coeff_x (a, b, tx):", coeff_x)
print("coeff_y (c, d, ty):", coeff_y)
```

**Paso E — Aplicar la transformación en `bridge_node.py`**

Agrega estos valores y función en `bridge_node.py`, antes de la función `move_to()`:

```python
# Obtenidos del script de calibración (Paso D) — sustituir con valores reales
_a, _b, _tx = coeff_x
_c, _d, _ty = coeff_y

def transform_to_robot_frame(x_scanner, y_scanner):
    x_robot = _a * x_scanner + _b * y_scanner + _tx
    y_robot = _c * x_scanner + _d * y_scanner + _ty
    return x_robot, y_robot
```

En `handle_client()`, reemplaza:
```python
x = float(coords["x"])
y = float(coords["y"])
```
por:
```python
x, y = transform_to_robot_frame(float(coords["x"]), float(coords["y"]))
```

**Verificación:** escanea uno de los 3 marcadores de referencia y exporta su CSV. Si el robot llega a esa posición dentro de ±2–3 mm, la calibración es correcta para producción.

---

## License

MIT
