bl_info = {
    "name": "Hexagon World Generator",
    "author": "Tobias Fischer, Dennis Hawran",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D",
    "description": "Create a hexagon world",
    "category": "Object",
}

import bpy

from .hexa_op import OBJECT_OT_HexagonGenerator
from .hexa_panel import OBJECT_PT_HexagonPanel

classes = (OBJECT_OT_HexagonGenerator, OBJECT_PT_HexagonPanel)

PROPS = [
    ("hexagon_radius", bpy.props.FloatProperty(name="Hexagon Radius", default=3)),
    ("hexagon_sides", bpy.props.IntProperty(name="Hexagon Sides", default=6)),
    ("grid_height", bpy.props.IntProperty(name="Grid Height", default=10)),
    ("grid_width", bpy.props.IntProperty(name="Grid Width", default=10)),
    ("delete_scene", bpy.props.BoolProperty(name="Delete actual scene", default=True)),
]


def register():
    for (prop_name, prop_value) in PROPS:
        setattr(bpy.types.Scene, prop_name, prop_value)

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for (prop_name, _) in PROPS:
        delattr(bpy.types.Scene, prop_name)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
