# gom-xarm-bridge-mvp

> Un bridge ROS 1 ligero que conecta un escáner 3D GOM Inspect (Windows) con un robot UFactory xArm de 5 ejes (Linux) usando solo herramientas gratuitas, un socket TCP y dos scripts Python.

---

## El Problema

La inspección de calidad industrial y la manipulación robótica suelen ser islas separadas. Una estación de metrología mide una pieza, un ingeniero lee los números, los introduce manualmente en el controlador del robot y el robot se mueve. Este proyecto elimina al humano del medio.

El problema: la API de scripting Python de GOM Inspect está bloqueada tras una licencia Professional. Este proyecto lo evita por completo — sin necesidad de actualizar la licencia.

---

## Cómo Funciona

```
┌──────────────────────────┐          ┌─────────────────────────────────┐
│       Windows PC         │          │          Linux PC (ROS)         │
│                          │          │                                 │
│  ATOS Core 3D Scanner    │          │  xArm 5-axis Robot              │
│         ↓                │          │         ↑                       │
│  GOM Inspect 2019 Free   │          │  /xarm/move_line service        │
│  (operador exporta CSV)  │          │         ↑                       │
│         ↓                │  TCP     │  bridge_node.py                 │
│  gom_watcher.py          │─────────▶│  (nodo ROS, servidor TCP)       │
│  (detecta el archivo,    │  :9999   │                                 │
│   extrae X,Y,            │  JSON    │                                 │
│   envía JSON)            │          │                                 │
└──────────────────────────┘          └─────────────────────────────────┘
```

**Flujo del operador (3 pasos):**
1. Escanear la pieza con el escáner ATOS Core.
2. En GOM Inspect: `File → Export → Feature List → Save as CSV` (dos clics).
3. El resto es automático — el script watcher detecta el archivo, extrae las coordenadas del centroide y el brazo robótico se mueve a la posición correcta en ~1 segundo.

---

## Por Qué Importa — Visión Smart Factory

Este MVP es intencionalmente mínimo, pero demuestra el patrón central detrás de la manufactura adaptativa moderna:

**Inspeccionar → Decidir → Actuar**, en bucle cerrado, sin intervención humana.

Algunas direcciones en las que esta arquitectura puede crecer:

| Mejora | Qué desbloquea |
|---|---|
| Reemplazar la exportación CSV con OCR en la pantalla de GOM | Cero clics manuales — bucle completamente autónomo |
| Añadir un nodo de transformación de coordenadas | Mapear el frame del escáner → frame del robot automáticamente tras una calibración única |
| Añadir una cámara de profundidad (ej. RealSense) | Detección de piezas en tiempo real sin estación de metrología dedicada |
| Extender el bridge para publicar en un topic ROS | Múltiples robots o nodos posteriores se suscriben y reaccionan |
| Añadir MoveIt para planificación de trayectorias | Trayectorias con detección de colisiones, no solo movimientos punto a punto |
| Conectar a un sistema MES / SCADA | El robot reporta resultados de vuelta a la capa de gestión de la fábrica |

La idea de que un escáner pueda _indicar_ a un robot adónde ir — y que el robot simplemente vaya — es el bloque fundamental de las celdas de manufactura sin operador. Este proyecto demuestra que el concepto funciona con herramientas estándar y libres de licencia.

---

## Estructura del Repositorio

```
gom-xarm-bridge-mvp/
├── src/
│   └── gom_xarm_bridge/          # paquete ROS 1 (corre en Linux)
│       ├── package.xml
│       ├── CMakeLists.txt
│       └── scripts/
│           └── bridge_node.py    # servidor TCP + llamada al servicio xArm
├── windows_scripts/
│   └── gom_watcher.py            # vigilante de archivos + parser CSV (corre en Windows)
├── CLAUDE.md                     # archivo de contexto para sesiones de Claude Code
└── README.md
```

`xarm_ros` (el driver ROS oficial de UFactory) es una dependencia externa clonada localmente — no está incluida en este repositorio.

---

## Requisitos Previos

**PC Linux:**
- ROS 1 Noetic
- Herramientas de build `catkin`
- Python 3
- Robot xArm de 5 ejes accesible en la red local

**PC Windows:**
- Python 3
- Librería `watchdog` (`pip install watchdog`)
- GOM Inspect 2019 (cualquier edición, incluyendo Basic/Free)

Ambas máquinas deben estar en la misma red local.

---

## Configuración

### Linux

```bash
# 1. Clonar este repositorio
git clone https://github.com/<tu-usuario>/gom-xarm-bridge-mvp.git xArm-cobot
cd xArm-cobot

# 2. Clonar la dependencia xarm_ros
mkdir -p repo
git clone https://github.com/xArm-Developer/xarm_ros.git repo/xarm_ros --recursive

# 3. Enlazar xarm_ros al workspace catkin
mkdir -p src
ln -s $(pwd)/repo/xarm_ros src/xarm_ros

# 4. Compilar
catkin_make
source devel/setup.bash
```

### Windows

```cmd
pip install watchdog
```

Abre `windows_scripts/gom_watcher.py` y configura estas cuatro variables al inicio del archivo:

```python
WATCH_DIR    = r"C:\GOM_Exports"   # carpeta donde GOM guarda el CSV
ROBOT_IP     = "192.168.31.100"     # IP del PC Linux
FEATURE_NAME = "Center"            # texto que identifica la fila del centroide en el CSV
COL_X        = "X [mm]"           # nombre exacto de la columna X en tu exportación de GOM
COL_Y        = "Y [mm]"           # nombre exacto de la columna Y en tu exportación de GOM
```

> **Consejo:** Exporta un CSV de prueba desde GOM Inspect y ábrelo en un editor de texto para confirmar los nombres de columna exactos y el delimitador (`;` o `,`) antes de ejecutar el script.

---

## Ejecución

**Linux — dos terminales:**

```bash
# Terminal 1: arrancar el driver de hardware xArm (reemplazar con la IP real del robot)
roslaunch xarm5_moveit_config realMove_exec.launch robot_ip:=192.168.31.xxx velocity_control:=false report_type:=normal

# Terminal 2: arrancar el nodo bridge
rosrun gom_xarm_bridge bridge_node.py
```

**Windows:**

```cmd
python windows_scripts\gom_watcher.py
```

---

## Referencia de Configuración

Estos valores en `bridge_node.py` definen dónde y cómo se mueve el robot. Configúralos una vez para que coincidan con tu setup físico:

| Parámetro | Valor por defecto | Descripción |
|---|---|---|
| `Z_FIXED` | `100.0` | Altura de la herramienta sobre la superficie de la mesa (mm) |
| `ROLL` | `π (3.1416)` | Orientación de la herramienta — por defecto apunta el efector hacia abajo |
| `PITCH` | `0.0` | Pitch de la herramienta (rad) |
| `YAW` | `0.0` | Yaw de la herramienta (rad) |
| `SPEED` | `80.0` | Velocidad de movimiento (mm/s) — mantener baja durante las pruebas iniciales |
| `ACC` | `300.0` | Aceleración (mm/s²) |
| `TCP_PORT` | `9999` | Puerto en el que escucha el bridge |

---

## ⚠️ Calibración de Coordenadas (Obligatoria Antes de Producción)

El escáner ATOS y el robot xArm viven en marcos de coordenadas distintos. Enviar coordenadas brutas del escáner al robot resultará en posiciones incorrectas.

Antes de usar datos reales del escáner, realiza una calibración mano-ojo:
1. Coloca al menos 3 marcadores de referencia en posiciones conocidas sobre la mesa.
2. Registra la posición X,Y de cada marcador tanto en el frame de GOM Inspect como en el frame base del robot.
3. Calcula la transformación rígida (rotación + traslación) entre los dos frames.
4. Aplica esta transformación en `bridge_node.py` antes de llamar a `/xarm/move_line`.

Para un MVP sobre una mesa plana, esto se reduce a una transformación afín 2D (4 parámetros).

---

## Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Escáner 3D | ATOS Core (GOM / Zeiss) |
| Software de metrología | GOM Inspect 2019 Free |
| Robot | UFactory xArm 5-axis |
| Middleware del robot | ROS 1 Noetic |
| Driver del robot | [xarm_ros](https://github.com/xArm-Developer/xarm_ros) |
| Comunicación | TCP socket, payload JSON |
| Vigilancia de archivos | Python `watchdog` |

---

## Limitaciones del MVP

- **Exportación manual:** el operador debe hacer clic en "Export CSV" en GOM Inspect. Es consecuencia de la restricción de la licencia Basic.
- **Sin transformación de coordenadas:** las coordenadas brutas del escáner se envían tal cual. Ver la sección de calibración arriba.
- **Una pieza a la vez:** el bridge procesa un archivo CSV por ciclo de escaneo.
- **Sin recuperación de errores:** si el robot falla a mitad de un movimiento, el bridge registra el error pero no reintenta ni alerta al operador.

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
Anota el valor de `Dirección IPv4` de tu adaptador (p. ej. `192.168.31.50`).

En Linux (abre una terminal):
```bash
ip addr show
```
Anota la IP de la interfaz activa (`eth0`, `enp3s0`, etc. — busca `inet 192.168.31.xxx`).

**0.2 Verificar conectividad**

```cmd
# Desde Windows hacia Linux
ping 192.168.31.100
```
```bash
# Desde Linux hacia Windows
ping 192.168.31.50
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
ROBOT_IP     = "192.168.31.100"     # ← CAMBIAR a la IP real del PC Linux (Parte 0.1)
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
[INFO] Robot: 192.168.31.100:9999
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
# Sustituye 192.168.31.xxx por la IP real del controlador del xArm
roslaunch xarm5_moveit_config realMove_exec.launch robot_ip:=192.168.31.xxx velocity_control:=false report_type:=normal
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
[INFO] [...] Recibido de ('192.168.31.50', 54321): {"x": 123.456, "y": 78.9}
[INFO] [...] Moviendo a X=123.46 Y=78.90 Z=100.0
[INFO] [...] Movimiento completado OK
```

**4.4 Diagnóstico de errores comunes**

| Síntoma | Causa probable | Solución |
|---|---|---|
| `[ERROR] No se pudo conectar a 192.168.31.100:9999` | `bridge_node.py` no corre, o IP incorrecta | Verifica Terminal Linux 3; revisa `ROBOT_IP` en `gom_watcher.py` |
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

## Licencia

MIT
