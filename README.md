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

## License

MIT
