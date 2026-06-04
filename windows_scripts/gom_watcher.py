"""
gom_watcher.py — corre en la PC Windows con GOM Inspect.

Workflow:
  1. Ejecutar este script antes de empezar a escanear.
  2. En GOM Inspect: File > Export > Feature List > guardar en WATCH_DIR.
  3. El script detecta el CSV, extrae X,Y del centroide y lo envía al robot.

Instalación de dependencias (una sola vez):
  pip install watchdog

Configuración:
  - Ajustar WATCH_DIR a la carpeta donde GOM guarda el CSV.
  - Ajustar ROBOT_IP con la IP de la PC Linux.
  - Ajustar FEATURE_NAME si el nombre del feature en GOM no contiene "Center".
  - Ajustar los nombres de columna (COL_X, COL_Y) tras inspeccionar un CSV de prueba.
"""

import csv
import json
import os
import socket
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# ── Configuración ─────────────────────────────────────────────────────────────
WATCH_DIR    = r"C:\GOM_Exports"       # carpeta donde GOM exporta el CSV
ROBOT_IP     = "192.168.1.100"         # IP de la PC Linux
ROBOT_PORT   = 9999

FEATURE_NAME = "Center"                # texto que identifica la fila del centroide
COL_X        = "X [mm]"               # nombre exacto de la columna X en el CSV
COL_Y        = "Y [mm]"               # nombre exacto de la columna Y en el CSV
CSV_DELIMITER = ";"                    # GOM usa punto y coma por defecto
# ─────────────────────────────────────────────────────────────────────────────


def parse_centroid(csv_path):
    """Devuelve (x_mm, y_mm) desde la fila que contiene FEATURE_NAME."""
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=CSV_DELIMITER)
        for row in reader:
            # Busca en todas las columnas si algún valor contiene FEATURE_NAME
            if any(FEATURE_NAME.lower() in str(v).lower() for v in row.values()):
                try:
                    x = float(row[COL_X].replace(",", "."))
                    y = float(row[COL_Y].replace(",", "."))
                    return x, y
                except (KeyError, ValueError) as e:
                    print(f"[ERROR] Columnas no encontradas. Columnas disponibles: {list(row.keys())}")
                    print(f"        Ajusta COL_X / COL_Y en la configuración. Detalle: {e}")
                    return None
    print(f"[WARN] No se encontró ninguna fila con '{FEATURE_NAME}' en {csv_path}")
    return None


def send_to_robot(x, y):
    payload = json.dumps({"x": round(x, 3), "y": round(y, 3)}).encode()
    try:
        with socket.create_connection((ROBOT_IP, ROBOT_PORT), timeout=5) as s:
            s.sendall(payload)
        print(f"[OK] Enviado al robot → X={x:.3f} Y={y:.3f}")
    except (ConnectionRefusedError, socket.timeout) as e:
        print(f"[ERROR] No se pudo conectar a {ROBOT_IP}:{ROBOT_PORT} — {e}")


class CSVHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(".csv"):
            print(f"[INFO] CSV detectado: {event.src_path}")
            time.sleep(0.5)  # espera a que GOM termine de escribir el archivo
            result = parse_centroid(event.src_path)
            if result:
                x, y = result
                print(f"[INFO] Centroide encontrado: X={x:.3f} Y={y:.3f}")
                send_to_robot(x, y)


if __name__ == "__main__":
    os.makedirs(WATCH_DIR, exist_ok=True)
    print(f"[INFO] Monitoreando: {WATCH_DIR}")
    print(f"[INFO] Robot: {ROBOT_IP}:{ROBOT_PORT}")
    print(f"[INFO] Esperando exportación CSV de GOM Inspect...")

    observer = Observer()
    observer.schedule(CSVHandler(), path=WATCH_DIR, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
