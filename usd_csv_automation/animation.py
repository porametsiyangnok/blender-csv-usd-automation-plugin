import bpy
from .logging_util import log



# 1) Hilfsfunktionen: Objekt-Findung / Mapping


def _guess_object_for_key(key: str):
    """
    Versucht, für einen CSV-Schlüssel (z.B. "A1") ein passendes
    Blender-Objekt zu finden.

    Strategien:
      0. Direkt "KinAxis_<Key>" (z.B. KinAxis_A1)
      1. Exakter Name:          "A1"
      2. Suffix-Match:          "..._A1" (z.B. "KinAxis_A1")
      3. Name endet mit " A1"   (mit Leerzeichen)
      4. Fallback: Name endet einfach mit "A1"
    """

    # Direktes KinAxis-Objekt: "KinAxis_A1", "KinAxis_A2", ...
    direct = bpy.data.objects.get(f"KinAxis_{key}")
    if direct is not None:
        log(f"Mapping: CSV-Key '{key}' -> Objekt '{direct.name}' (KinAxis direct)", "INFO")
        return direct

    # exakter Name: "A1"
    obj = bpy.data.objects.get(key)
    if obj is not None:
        log(f"Mapping: CSV-Key '{key}' -> Objekt '{obj.name}' (exakter Name)", "INFO")
        return obj

    # Suffix "_<key>" oder " <key>"
    for cand in bpy.data.objects:
        if cand.name.endswith("_" + key) or cand.name.endswith(" " + key):
            log(f"Mapping: CSV-Key '{key}' -> Objekt '{cand.name}' (Suffix-Match)", "INFO")
            return cand

    # letzte Notlösung: Name endet einfach mit key
    for cand in bpy.data.objects:
        if cand.name.endswith(key):
            log(f"Mapping: CSV-Key '{key}' -> Objekt '{cand.name}' (weak suffix)", "INFO")
            return cand

    log(f"Mapping: Kein Objekt für CSV-Key '{key}' gefunden.", "WARNING")
    return None


def _build_mapping(csv_keys):
    """
    Erzeugt ein Mapping-Dict von CSV-Key -> Blender-Objektname.

    Eingabe:
      csv_keys = z.B. ["A1", "A2", ..., "A6"]

    Ausgabe:
      {
        "A1": "KinAxis_A1",
        "A2": "KinAxis_A2",
        ...
      }
    """
    mapping = {}

    for key in csv_keys:
        obj = _guess_object_for_key(key)
        if obj is not None:
            mapping[key] = obj.name

    if not mapping:
        log("Mapping: Kein einziges Objekt aus CSV konnte in der Szene gefunden werden.", "ERROR")
    else:
        log(f"Mapping: {len(mapping)} CSV-Keys wurden auf Blender-Objekte gemappt.", "INFO")

    return mapping


def _find_target_object(object_name: str | None = None):
    """
    Findet das Zielobjekt für die Animation:

    - wenn object_name gesetzt:
        -> genau dieses Objekt (exakter Name)
    - sonst:
        -> aktives Objekt oder 'Mover_1' als Fallback
    """
    if object_name:
        obj = bpy.data.objects.get(object_name)
        if obj is None:
            log(f"Objekt '{object_name}' nicht gefunden.", "ERROR")
        else:
            log(f"Objekt '{obj.name}' als Ziel verwendet (expliziter Name).", "INFO")
        return obj

    # aktives Objekt
    obj = bpy.context.view_layer.objects.active
    if obj:
        log(f"Aktives Objekt als Ziel verwendet: {obj.name}", "INFO")
        return obj

    # fallback
    obj = bpy.data.objects.get("Mover_1")
    if obj:
        log("Fallback: Objekt 'Mover_1' als Ziel verwendet.", "INFO")
        return obj

    log("Kein Zielobjekt für Animation gefunden.", "ERROR")
    return None



# Kern: Animation für EIN Objekt


def apply_animation(frames: list[dict], object_name: str | None = None):
    """
    frames: Liste von Dictionaries:

      {
          "frame": int,
          "location": (x, y, z),      # wird aktuell NICHT benutzt
          "quaternion": (q1, q2, q3, q4)
      }

    object_name:
      - expliziter Name (z.B. 'A1', 'KinAxis_A1')
      - None -> es wird _find_target_object(None) verwendet
    """
    if not frames:
        log("Keine Frames zum Animieren erhalten.", "ERROR")
        return

    obj = _find_target_object(object_name)
    if obj is None:
        return

    log(f"Starte Animation auf Objekt '{obj.name}' mit {len(frames)} Frames.", "INFO")

    # vorhandene Animation löschen
    if obj.animation_data:
        obj.animation_data_clear()
        log("Bestehende Animation des Objekts gelöscht.", "INFO")

    # Quaternion-Modus, weil wir Quaternionen aus CSV bekommen
    obj.rotation_mode = 'QUATERNION'

    count_ok = 0

    for entry in frames:
        try:
            frame = int(entry.get("frame", 0))
            quat = entry.get("quaternion")

            if quat is None:
                continue

            q1, q2, q3, q4 = quat

            obj.rotation_quaternion = (q1, q2, q3, q4)

            obj.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            count_ok += 1

        except Exception as e:
            log(f"Fehler beim Setzen eines Keyframes (Frame {entry.get('frame')}): {e}", "ERROR")
            continue

    log(f"Animation angewendet, {count_ok} Keyframes gesetzt.", "INFO")



# Multi-Objekt-Animation mit automatischem Mapping


def apply_animation_multi(frames_by_key: dict[str, list[dict]]):
    """
    Nimmt ein Dict wie:
      { "A1": [Frame-Dicts], "A2": [...], ... }

    1) baut ein Mapping CSV-Key -> Blender-Objektname
    2) ruft für jedes Paar apply_animation(...) auf
    """
    if not frames_by_key:
        log("apply_animation_multi: Keine Daten erhalten.", "ERROR")
        return

    # Mapping aufbauen
    mapping = _build_mapping(frames_by_key.keys())
    if not mapping:
        log("apply_animation_multi: Kein Mapping vorhanden, Abbruch.", "ERROR")
        return

    # Für jeden Schlüssel die passenden Frames anwenden
    for key, frames in frames_by_key.items():
        if not frames:
            log(f"Keine Frames für CSV-Key '{key}' – übersprungen.", "WARNING")
            continue

        target_name = mapping.get(key)
        if not target_name:
            log(f"Kein Zielobjekt für CSV-Key '{key}', Animation übersprungen.", "WARNING")
            continue

        log(f"Starte Animation für CSV-Key '{key}' -> Objekt '{target_name}'.", "INFO")
        apply_animation(frames, object_name=target_name)



# Auto-Rig: ComauRacer KinAxis_A1..A6 verketten

def auto_rig_comau():
    """
    Baut eine klassische Roboter-Kinematik:

      KinAxis_A1
        -> KinAxis_A2
            -> KinAxis_A3
                -> KinAxis_A4
                    -> KinAxis_A5
                        -> KinAxis_A6

    Die Welt-Position jedes KinAxis bleibt gleich (Keep Transform),
    nur die Parent-Beziehungen werden angepasst.
    """
    axes = []
    for i in range(1, 7):
        name = f"KinAxis_A{i}"
        obj = bpy.data.objects.get(name)
        if obj is None:
            log(f"Auto-Rig: '{name}' nicht gefunden.", "WARNING")
        else:
            axes.append(obj)

    if len(axes) < 2:
        log("Auto-Rig: Weniger als 2 KinAxis-Achsen gefunden – Abbruch.", "ERROR")
        return

    log("Auto-Rig: Starte Kettenaufbau KinAxis_A1 .. KinAxis_A6.", "INFO")

    for idx in range(1, len(axes)):
        parent = axes[idx - 1]
        child = axes[idx]

        if child.parent == parent:
            log(f"Auto-Rig: {child.name} ist bereits Kind von {parent.name}.", "INFO")
            continue

        # Weltmatrix sichern
        world_mat = child.matrix_world.copy()

        # neuen Parent setzen
        child.parent = parent
        # Parent-Inverse für "Keep Transform"
        child.matrix_parent_inverse = parent.matrix_world.inverted()
        # Welt-Transform wiederherstellen
        child.matrix_world = world_mat

        log(f"Auto-Rig: Parent von '{child.name}' -> '{parent.name}' gesetzt (Keep Transform).", "INFO")

    log("Auto-Rig: Kinematik erfolgreich aufgebaut.", "INFO")


# Optionaler Operator, damit du es über einen Button starten kannst

# Blender-Operator für Auto-Rig


class ISG_OT_AutoRigComau(bpy.types.Operator):
    bl_idname = "isg.auto_rig_comau"
    bl_label = "Comau Auto-Rig"
    bl_description = "Verkettet KinAxis_A1..A6 zu einer Roboter-Kinematik"

    def execute(self, context):
        auto_rig_comau()
        self.report({'INFO'}, "Auto-Rig für ComauRacer ausgeführt.")
        return {'FINISHED'}

