#!/usr/bin/env python3
"""
TCP bridge: recibe {x, y} en mm desde Windows y mueve el xArm con move_line.

Arranque:
  rosrun gom_xarm_bridge bridge_node.py
"""

import json
import math
import socket
import threading
import rospy
from xarm_msgs.srv import Move

# ── Geometría fija (ajustar según la mesa real) ──────────────────────────────
Z_FIXED = 100.0     # mm sobre la superficie de la mesa
ROLL    = math.pi   # efector apuntando hacia abajo
PITCH   = 0.0
YAW     = 0.0
SPEED   = 80.0      # mm/s  — conservador para MVP
ACC     = 300.0     # mm/s²

# ── Red ──────────────────────────────────────────────────────────────────────
TCP_HOST = "0.0.0.0"
TCP_PORT = 9999


def move_to(x_mm, y_mm):
    rospy.loginfo(f"Moviendo a X={x_mm:.2f} Y={y_mm:.2f} Z={Z_FIXED}")
    try:
        rospy.wait_for_service("/xarm/move_line", timeout=5.0)
        move = rospy.ServiceProxy("/xarm/move_line", Move)
        resp = move(
            pose    = [x_mm, y_mm, Z_FIXED, ROLL, PITCH, YAW],
            mvvelo  = SPEED,
            mvacc   = ACC,
            mvtime  = 0.0,
            mvradii = 0.0,
        )
        if resp.ret == 0:
            rospy.loginfo("Movimiento completado OK")
        else:
            rospy.logwarn(f"xArm respondió ret={resp.ret}: {resp.message}")
    except rospy.ROSException as e:
        rospy.logerr(f"Servicio no disponible: {e}")
    except Exception as e:
        rospy.logerr(f"Error llamando move_line: {e}")


def handle_client(conn, addr):
    try:
        data = conn.recv(1024).decode().strip()
        rospy.loginfo(f"Recibido de {addr}: {data}")
        coords = json.loads(data)
        x = float(coords["x"])
        y = float(coords["y"])
        move_to(x, y)
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        rospy.logwarn(f"Payload inválido de {addr}: {e}")
    finally:
        conn.close()


def tcp_server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((TCP_HOST, TCP_PORT))
    srv.listen(5)
    srv.settimeout(1.0)
    rospy.loginfo(f"Bridge escuchando en {TCP_HOST}:{TCP_PORT}")
    while not rospy.is_shutdown():
        try:
            conn, addr = srv.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
        except socket.timeout:
            continue
    srv.close()


if __name__ == "__main__":
    rospy.init_node("gom_xarm_bridge")
    t = threading.Thread(target=tcp_server, daemon=True)
    t.start()
    rospy.spin()
