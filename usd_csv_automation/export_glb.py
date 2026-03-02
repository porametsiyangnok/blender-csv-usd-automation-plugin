# export_glb.py
import os
import bpy
from . import logging_util as logu


def export_glb(filepath: str) -> bool:
    """
    Exportiert die Szene oder Auswahl als GLB.
    Die genaue Export-Strategie legen wir später fest.
    """
    if not filepath:
        logu.log("Kein GLB-Exportpfad angegeben.", "ERROR")
        return False

    abs_path = bpy.path.abspath(filepath)
    abs_path = os.path.normpath(abs_path)

    try:
        # Verwende den offiziellen glTF/GLB-Exporter
        bpy.ops.export_scene.gltf(
            filepath=abs_path,
            export_format='GLB',
        
        )
        logu.log(f"GLB erfolgreich exportiert: {abs_path}", "INFO")
        return True
    except Exception as e:
        logu.log(f"Fehler beim GLB-Export: {e}", "ERROR")
        return False
