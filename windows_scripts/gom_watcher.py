"""
gom_watcher.py — corre en la PC Windows con GOM Inspect.

Workflow:
  1. Ejecutar este script antes de empezar a escanear.
  2. En GOM Inspect: File > Export > Elements > Elements (XML) > guardar en WATCH_DIR.
  3. El script detecta el XML, extrae X,Y del centroide y lo envía al robot.

Instalación de dependencias (una sola vez):
  pip install watchdog

Configuración:
  - Ajustar WATCH_DIR a la carpeta donde GOM guarda el XML.
  - Ajustar ROBOT_IP con la IP de la PC Linux.
  - Ajustar FEATURE_NAME si el nombre del feature en GOM no contiene "Center".
  - Ajustar los nombres de tag (TAG_ELEMENT, TAG_X, TAG_Y, etc.) tras
    inspeccionar un XML de prueba con el Bloc de notas.
"""

import json
import os
import socket
import time
import xml.etree.ElementTree as ET

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# ── Configuración ─────────────────────────────────────────────────────────────
WATCH_DIR    = r"C:\GOM_Exports"       # carpeta donde GOM exporta el XML
ROBOT_IP     = "192.168.1.100"         # IP de la PC Linux
ROBOT_PORT   = 9999

FEATURE_NAME = "Center"                # texto que identifica el feature del centroide

# Estructura del XML exportado por GOM Inspect.
# Abre un XML de prueba con el Bloc de notas y ajusta estos valores si difieren.
TAG_ELEMENT           = "element"      # tag de cada feature  (p.ej. <element name="Center">)
ATTR_NAME             = "name"         # atributo con el nombre del feature
TAG_COORDINATE_PARENT = "actual"       # sub-tag con las coordenadas; None si están al nivel raíz
TAG_X                 = "x"           # tag con el valor X en mm
TAG_Y                 = "y"           # tag con el valor Y en mm
# ─────────────────────────────────────────────────────────────────────────────


def parse_centroid_xml(xml_path):
    """Devuelve (x_mm, y_mm) desde el elemento que contiene FEATURE_NAME."""
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as e:
        print(f"[ERROR] XML malformado en {xml_path}: {e}")
        return None

    root = tree.getroot()

    for elem in root.iter(TAG_ELEMENT):
        attr_val = elem.get(ATTR_NAME, "")
        if FEATURE_NAME.lower() not in attr_val.lower():
            continue

        coord_node = elem.find(TAG_COORDINATE_PARENT) if TAG_COORDINATE_PARENT else elem
        if coord_node is None:
            print(f"[ERROR] Tag '{TAG_COORDINATE_PARENT}' no encontrado dentro de '{attr_val}'. "
                  f"Ajusta TAG_COORDINATE_PARENT en la configuración.")
            return None

        x_tag = coord_node.find(TAG_X)
        y_tag = coord_node.find(TAG_Y)

        if x_tag is None or y_tag is None:
            missing = [t for t, n in ((TAG_X, x_tag), (TAG_Y, y_tag)) if n is None]
            print(f"[ERROR] Tags no encontrados: {missing}. "
                  f"Ajusta TAG_X / TAG_Y en la configuración.")
            return None

        try:
            x = float(x_tag.text.replace(",", "."))
            y = float(y_tag.text.replace(",", "."))
            return x, y
        except (ValueError, AttributeError) as e:
            print(f"[ERROR] No se pudo convertir coordenadas a float: {e}")
            return None

    print(f"[WARN] No se encontró ningún elemento con '{FEATURE_NAME}' en {xml_path}")
    return None


def send_to_robot(x, y):
    payload = json.dumps({"x": round(x, 3), "y": round(y, 3)}).encode()
    try:
        with socket.create_connection((ROBOT_IP, ROBOT_PORT), timeout=5) as s:
            s.sendall(payload)
        print(f"[OK] Enviado al robot → X={x:.3f} Y={y:.3f}")
    except (ConnectionRefusedError, socket.timeout) as e:
        print(f"[ERROR] No se pudo conectar a {ROBOT_IP}:{ROBOT_PORT} — {e}")


class XMLHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(".xml"):
            print(f"[INFO] XML detectado: {event.src_path}")
            time.sleep(0.5)  # espera a que GOM termine de escribir el archivo
            result = parse_centroid_xml(event.src_path)
            if result:
                x, y = result
                print(f"[INFO] Centroide encontrado: X={x:.3f} Y={y:.3f}")
                send_to_robot(x, y)


if __name__ == "__main__":
    os.makedirs(WATCH_DIR, exist_ok=True)
    print(f"[INFO] Monitoreando: {WATCH_DIR}")
    print(f"[INFO] Robot: {ROBOT_IP}:{ROBOT_PORT}")
    print(f"[INFO] Esperando exportación XML de GOM Inspect...")

    observer = Observer()
    observer.schedule(XMLHandler(), path=WATCH_DIR, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
