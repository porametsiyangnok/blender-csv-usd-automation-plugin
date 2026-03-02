import bpy

def log(message: str, level: str = "INFO"):
    """Einfaches zentrales Logging."""
    print(f"[{level}] {message}")
    # Optional: später in Textblock in Blender schreiben oder in Datei loggen
