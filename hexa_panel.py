from bpy.types import Panel

class OBJECT_PT_HexagonPanel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Item"
    bl_label = "Hexagon Generator"

    def draw(self, context):
        layout = self.layout

        layout.row().prop(context.scene, "delete_scene")
        layout.row().prop(context.scene, "hexagon_amount")
        layout.row().prop(context.scene, "hexagon_spacing")
        layout.row().prop(context.scene, "height_min")
        layout.row().prop(context.scene, "height_max")
        layout.row().prop(context.scene, "sea_level")
        layout.row().prop(context.scene, "noise")
        layout.row().prop(context.scene, "noise_time")
        layout.row().prop(context.scene, "detail")
        layout.row().prop(context.scene, "roughness")
        layout.row().prop(context.scene, "distortion")
        layout.row().prop(context.scene, "object_probability")
        layout.row().operator("object.hexagon_generator", text="Generate Hexagon")