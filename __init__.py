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

# Make a tupel of all classes we are using to register them in a loop
classes = (OBJECT_OT_HexagonGenerator, OBJECT_PT_HexagonPanel)

# Create a list of properties for the scene
PROPS = [
    ("delete_scene", bpy.props.BoolProperty(name="Delete actual scene", default=True)),
    ("created_world", bpy.props.PointerProperty(name="Created world", type=bpy.types.Object)),
    ("hexagon_amount", bpy.props.IntProperty(name="Number of hexagons", default=100)),
    ("hexagon_spacing", bpy.props.FloatProperty(name="Space between hexagons", default=0)),
    ("height_min", bpy.props.FloatProperty(name="Height minimum", default=3)),
    ("height_max", bpy.props.FloatProperty(name="Height maximum", default=20)),
    ("sea_level", bpy.props.FloatProperty(name="Sea Level", default=6)),
    ("noise", bpy.props.FloatProperty(name="Enviroment noise", default=0.05)),
    ("object_probability", bpy.props.FloatProperty(name="Object probability", default=0.3))
]


def register():
    # Register the properties
    for (prop_name, prop_value) in PROPS:
        setattr(bpy.types.Scene, prop_name, prop_value)

    # Register the classes
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    # Unregister the classes
    for (prop_name, _) in PROPS:
        delattr(bpy.types.Scene, prop_name)

    # Unregister the properties
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
