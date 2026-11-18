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
  - Ajustar FEATURE_NAME si el nombre del feature en GOM no es "Center".
  - Ajustar los nombres de tag si la versión de GOM usa una estructura distinta.

Formato XML esperado (GOM Inspect 2019.1):
  <gom>
    <measured>
      <point name="Center">
        <geometry>
          <pos x="-19.518" y="5.796" z="-11.525"></pos>
        </geometry>
      </point>
    </measured>
  </gom>
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

FEATURE_NAME = "Center"                # atributo 'name' del feature del centroide

# Estructura del XML exportado por GOM Inspect 2019.1.
# Abrir un XML de prueba con el Bloc de notas para verificar si difiere.
TAG_ELEMENT  = "point"      # tag de cada feature:    <point name="Center">
ATTR_NAME    = "name"       # atributo con el nombre: name="Center"
TAG_GEOMETRY = "geometry"   # sub-tag con la posición: <geometry>
TAG_POS      = "pos"        # tag con coords como atributos: <pos x="..." y="...">
# ─────────────────────────────────────────────────────────────────────────────


def parse_centroid_xml(xml_path):
    """Devuelve (x_mm, y_mm) desde el elemento cuyo atributo 'name' contiene FEATURE_NAME."""
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as e:
        print(f"[ERROR] XML malformado en {xml_path}: {e}")
        return None

    root = tree.getroot()

    for elem in root.iter(TAG_ELEMENT):
        if FEATURE_NAME.lower() not in elem.get(ATTR_NAME, "").lower():
            continue

        geometry = elem.find(TAG_GEOMETRY)
        if geometry is None:
            print(f"[ERROR] Tag '{TAG_GEOMETRY}' no encontrado dentro de "
                  f"'{elem.get(ATTR_NAME)}'. Ajusta TAG_GEOMETRY.")
            return None

        pos = geometry.find(TAG_POS)
        if pos is None:
            print(f"[ERROR] Tag '{TAG_POS}' no encontrado dentro de '{TAG_GEOMETRY}'. "
                  f"Ajusta TAG_POS.")
            return None

        x_str = pos.get("x")
        y_str = pos.get("y")
        if x_str is None or y_str is None:
            missing = [a for a, v in (("x", x_str), ("y", y_str)) if v is None]
            print(f"[ERROR] Atributos no encontrados en <{TAG_POS}>: {missing}")
            return None

        try:
            x = float(x_str.replace(",", "."))
            y = float(y_str.replace(",", "."))
            return x, y
        except ValueError as e:
            print(f"[ERROR] No se pudo convertir coordenadas a float: {e}")
            return None

    print(f"[WARN] No se encontró ningún <{TAG_ELEMENT} {ATTR_NAME}='...{FEATURE_NAME}...'> "
          f"en {xml_path}")
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
