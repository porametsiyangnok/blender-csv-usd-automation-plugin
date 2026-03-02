import os
import bpy
from . import logging_util as logu


def import_usd(filepath: str) -> bool:
    """Importiert eine USD-Datei in die Szene."""
    if not filepath:
        logu.log("Kein USD-Pfad angegeben.", "ERROR")
        return False

    abs_path = bpy.path.abspath(filepath)
    abs_path = os.path.normpath(abs_path)

    if not os.path.isfile(abs_path):
        logu.log(f"USD-Datei nicht gefunden: {abs_path}", "ERROR")
        return False

    try:
    
        bpy.ops.wm.usd_import(filepath=abs_path)
        logu.log(f"USD erfolgreich importiert: {abs_path}", "INFO")
        return True
    except Exception as e:
        logu.log(f"Fehler beim USD-Import: {e}", "ERROR")
        return False
