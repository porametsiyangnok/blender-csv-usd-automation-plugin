import csv
import os
import bpy
from mathutils import Matrix
from .logging_util import log  # zentrale Logging-Funktion


def _to_float(value: str) -> float:
    """Komma -> Punkt, trimmen, dann float."""
    v = value.strip()
    if not v:
        return 0.0
    v = v.replace(",", ".")
    try:
        return float(v)
    except Exception as e:
        log(f"Konnte Zahl nicht konvertieren: '{value}' ({e})", "ERROR")
        return 0.0



# Mover-CSV mit Quaternionen (ein Objekt)


def _parse_mover_quat_csv(header, reader):
    """
    Alter Fall: Mover-CSV mit Quaternions.

    Spalten:
      0: time (Mikrosekunden)
      1: pos_x  (Mikrometer)
      2: pos_y
      3: pos_z
      4: quat q1 (w)
      5: quat q2 (x)
      6: quat q3 (y)
      7: quat q4 (z)

    Rückgabe: Liste von Dicts:
      { "frame": int, "location": (x,y,z), "quaternion": (q1,q2,q3,q4) }
    """
    frames = []

    # Konvertierungs-Konstanten
    FPS = 60.0                # Ziel-FPS in Blender
    TIME_DIVISOR = 1_000_000  # Mikrosekunden -> Sekunden
    POS_SCALE = 1e-6          # Mikrometer -> Meter (Blender-Units)

    for row in reader:
        # Leere / zu kurze Zeilen überspringen
        if not row or len(row) < 8:
            continue

        try:
            # Zeit: Mikrosekunden -> Sekunden -> Frame
            t_raw = _to_float(row[0])          # z.B. 2,12E+06
            time_sec = t_raw / TIME_DIVISOR    # -> ca. 2,12 s
            frame = int(round(time_sec * FPS)) # -> z.B. ~127

            # Position: Mikrometer -> Meter
            x = _to_float(row[1]) * POS_SCALE
            y = _to_float(row[2]) * POS_SCALE
            z = _to_float(row[3]) * POS_SCALE

            # Quaternion direkt übernehmen
            q1 = _to_float(row[4])  # w
            q2 = _to_float(row[5])  # x
            q3 = _to_float(row[6])  # y
            q4 = _to_float(row[7])  # z

            frames.append(
                {
                    "frame": frame,
                    "location": (x, y, z),
                    "quaternion": (q1, q2, q3, q4),
                }
            )

        except Exception as e:
            log(f"Fehler beim Konvertieren einer Zeile (Mover-CSV): {e}", "ERROR")
            continue

    log(f"Mover-CSV geladen, {len(frames)} Frames", "INFO")
    return frames



# ComauRacer-CSV A1..A6 mit Rotationsmatrix (Multi-Objekt)


def _parse_comauracer_multi_csv(header, reader):
    """
    ComauRacer-CSV mit A1..A6.

    Aufbau:
      Spalte 0: time (Sekunden)
      je Achse A1..A6: 12 Spalten
        Pout.x, Pout.y, Pout.z,
        Sout.xx,xy,xz,yx,yy,yz,zx,zy,zz

    Rückgabe:
      Dict, Schlüssel sind die Achsnamen:
        { "A1": [Frame-Dicts], ..., "A6": [...] }

    WICHTIG:
      Für den Roboter verwenden wir später NUR die Rotation (Quaternion),
      die Positionen werden NICHT animiert.
    """
    axes = ["A1", "A2", "A3", "A4", "A5", "A6"]
    frames_by_axis = {axis: [] for axis in axes}

    FPS = 60.0  # Ziel-FPS
    time0 = None

    for row in reader:
        # 1 Zeit-Spalte + 6 Achsen * 12 Werte = 73 Spalten
        if not row or len(row) < 73:
            continue

        try:
            t_raw = _to_float(row[0])    
            if time0 is None:
                time0 = t_raw

            time_sec = t_raw - time0       # erster Eintrag -> 0
            frame = int(round(time_sec * FPS)) + 1  # erster Frame = 1

            for idx, axis in enumerate(axes):
                base = 1 + idx * 12  # Startindex für diese Achse

                # Position (lesen, aber NICHT animieren)
                x = _to_float(row[base + 0])
                y = _to_float(row[base + 1])
                z = _to_float(row[base + 2])

                # Rotationsmatrix 3x3
                xx = _to_float(row[base + 3])
                xy = _to_float(row[base + 4])
                xz = _to_float(row[base + 5])
                yx = _to_float(row[base + 6])
                yy = _to_float(row[base + 7])
                yz = _to_float(row[base + 8])
                zx = _to_float(row[base + 9])
                zy = _to_float(row[base + 10])
                zz = _to_float(row[base + 11])

                m = Matrix((
                    (xx, xy, xz),
                    (yx, yy, yz),
                    (zx, zy, zz),
                ))
                quat = m.to_quaternion()  # (w, x, y, z)

                # Nur Frame + Quaternion speichern, Position ignorieren
                frames_by_axis[axis].append(
                    {
                        "frame": frame,
                        "quaternion": (quat.w, quat.x, quat.y, quat.z),
                        # "location": (x, y, z),  # absichtlich nicht verwendet
                    }
                )

        except Exception as e:
            log(f"Fehler beim Konvertieren einer Zeile (ComauRacer-CSV): {e}", "ERROR")
            continue

    for axis, lst in frames_by_axis.items():
        log(f"ComauRacer-CSV: {axis} -> {len(lst)} Frames", "INFO")

    return frames_by_axis



# Hauptfunktion: CSV laden & Format erkennen
def load_csv(filepath):
    """
    Lädt eine CSV-Datei und erkennt automatisch das Format:

    1) Mover-CSV (Tab-getrennt, Quaternions, eine Bahn)
       -> Rückgabe: Liste[Dict] (ein Objekt)

    2) ComauRacer-CSV (Semikolon-getrennt, A1..A6, Rotationsmatrix)
       -> Rückgabe: Dict[str, Liste[Dict]], z.B. {"A1":[...], "A2":[...], ...}
    """
    try:
        if not filepath:
            log("CSV-Dateipfad ist leer.", "ERROR")
            return None

        abs_path = bpy.path.abspath(filepath)
        abs_path = os.path.normpath(abs_path)

        log(f"CSV abspath: {abs_path}", "INFO")

        if not os.path.isfile(abs_path):
            log(f"CSV-Datei nicht gefunden: {abs_path}", "ERROR")
            return None

        log(f"CSV wird geladen: {abs_path}", "INFO")

        # Dialekt (Trennzeichen) automatisch erkennen
        with open(abs_path, newline="", encoding="utf-8") as csvfile:
            sample = csvfile.read(4096)
            csvfile.seek(0)

            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=";\t,")
            except Exception:
                # Fallback: Semikolon
                dialect = csv.excel
                dialect.delimiter = ';'

            reader = csv.reader(csvfile, dialect)
            header = next(reader, None)
            log(f"CSV Header: {header}", "INFO")

            if not header:
                log("Leere CSV oder kein Header gefunden.", "ERROR")
                return None

            # Format-Erkennung
            header_str = " ".join(header)

            if "ComauRacer" in header_str and len(header) >= 73:
                log("Erkanntes Format: ComauRacer Multi-Objekt CSV", "INFO")
                return _parse_comauracer_multi_csv(header, reader)

            elif len(header) >= 8:
                log("Erkanntes Format: Mover-CSV mit Quaternion", "INFO")
                return _parse_mover_quat_csv(header, reader)

            else:
                log("Unbekanntes CSV-Format.", "ERROR")
                return None

    except Exception as e:
        log(f"Fehler beim CSV-Import: {e}", "ERROR")
        return None
