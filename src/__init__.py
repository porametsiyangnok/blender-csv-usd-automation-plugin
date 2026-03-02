bl_info = {
    "name": "USD CSV Automation",
    "author": "Poramet Siyangnok",
    "version": (1, 0, 0),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > Convert Tools",
    "description": "Importiert USD, wendet CSV-Animationen an und exportiert GLB.",
    "category": "Import-Export",
}

import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, PointerProperty

# Unsere eigenen Module
from . import import_usd
from . import import_csv
from . import animation
from . import export_glb
from . import logging_util



# Add-on Properties (Pfadangaben usw.)

class ISGAddonProperties(PropertyGroup):
    usd_filepath: StringProperty(
        name="USD-Datei",
        description="Pfad zur USD-Datei",
        default="",
        subtype='FILE_PATH',
    )

    csv_filepath: StringProperty(
        name="CSV-Datei",
        description="Pfad zur CSV-Bewegungsdatei",
        default="",
        subtype='FILE_PATH',
    )

    glb_export_path: StringProperty(
        name="GLB-Export",
        description="Zielpfad für exportierte GLB-Datei",
        default="",
        subtype='FILE_PATH',
    )



#Operator: USD importieren

class ISG_OT_ImportUSD(Operator):
    bl_idname = "isg.import_usd"
    bl_label = "USD importieren"
    bl_description = "Importiert eine USD-Datei in die Szene"

    def execute(self, context):
        props = context.scene.isg_addon_props

        ok = import_usd.import_usd(props.usd_filepath)
        if ok:
            self.report({'INFO'}, "USD-Import erfolgreich")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "USD-Import fehlgeschlagen (siehe Konsole)")
            return {'CANCELLED'}



# Operator: CSV laden & Animation anwenden

class ISG_OT_ApplyCSVAnimation(Operator):
    bl_idname = "isg.apply_csv_animation"
    bl_label = "CSV-Animation anwenden"
    bl_description = "Liest CSV und setzt Keyframes auf passende Objekte"

    def execute(self, context):
        props = context.scene.isg_addon_props

        # CSV-Daten laden
        csv_data = import_csv.load_csv(props.csv_filepath)
        if csv_data is None:
            self.report({'ERROR'}, "CSV konnte nicht geladen werden (siehe Konsole)")
            return {'CANCELLED'}

        # Animation anwenden
        try:
            # Mehrere Objekte (Dict: Name -> Frames)
            if isinstance(csv_data, dict):
                animation.apply_animation_multi(csv_data)
            # Ein Objekt (Liste von Frames)
            else:
                animation.apply_animation(csv_data)

        except Exception as e:
            logging_util.log(f"Fehler beim Anwenden der CSV-Animation: {e}", "ERROR")
            self.report({'ERROR'}, "Fehler beim Anwenden der CSV-Animation")
            return {'CANCELLED'}

        self.report({'INFO'}, "CSV-Animation erfolgreich angewendet")
        return {'FINISHED'}


# Operator: GLB exportieren

class ISG_OT_ExportGLB(Operator):
    bl_idname = "isg.export_glb"
    bl_label = "GLB exportieren"
    bl_description = "Exportiert die aktuelle Szene bzw. Auswahl als GLB"

    def execute(self, context):
        props = context.scene.isg_addon_props

        ok = export_glb.export_glb(props.glb_export_path)
        if ok:
            self.report({'INFO'}, "GLB-Export erfolgreich")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "GLB-Export fehlgeschlagen (siehe Konsole)")
            return {'CANCELLED'}



# Panel in der Sidebar

class ISG_PT_MainPanel(Panel):
    bl_label = "ISG GLB Automation"
    bl_idname = "ISG_PT_mainpanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ISG Tools"

    def draw(self, context):
        layout = self.layout
        props = context.scene.isg_addon_props

        # USD 
        box_usd = layout.box()
        box_usd.label(text="USD-Import", icon="IMPORT")
        box_usd.prop(props, "usd_filepath")
        box_usd.operator("isg.import_usd", icon="FILE_FOLDER")

        layout.operator("isg.auto_rig_comau", text="Comau Auto-Rig")


        # CSV / Animation
        box_csv = layout.box()
        box_csv.label(text="CSV-Animation", icon="ANIM_DATA")
        box_csv.prop(props, "csv_filepath")
        box_csv.operator("isg.apply_csv_animation", icon="ANIM")

        # GLB Export
        box_glb = layout.box()
        box_glb.label(text="GLB-Export", icon="EXPORT")
        box_glb.prop(props, "glb_export_path")
        box_glb.operator("isg.export_glb", icon="FILE")



# Registrierung
classes = (
    ISGAddonProperties,
    ISG_OT_ImportUSD,
    ISG_OT_ApplyCSVAnimation,   
    ISG_OT_ExportGLB,
    ISG_PT_MainPanel,
    animation.ISG_OT_AutoRigComau,
)



def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.isg_addon_props = PointerProperty(type=ISGAddonProperties)
    logging_util.log("ISG GLB Automation Add-on registriert.")


def unregister():
    del bpy.types.Scene.isg_addon_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    logging_util.log("ISG GLB Automation Add-on deregistriert.")


if __name__ == "__main__":
    register()
