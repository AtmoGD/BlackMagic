import bpy

from bpy.types import Panel

class HexagonPanel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Hexa"
    bl_label = "Hexa"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        col = row.column()
        col.operator("object.hexagon_generator", text="Create Hexagon World")