import bpy
from .hexa_op import HexagonGenerator
from .hexa_panel import HexagonPanel

classes = (HexagonGenerator, HexagonPanel)

bl_info = {
    "name": "Hexagon World Generator",
    "author": "Tobias Fischer, Dennis Hawran",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D",
    "description": "Create a hexagon world",
    "category": "Object",
}

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register() 

