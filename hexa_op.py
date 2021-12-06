import bpy
from bpy import context
from bpy.ops import node

from bpy.types import Operator


class OBJECT_OT_HexagonGenerator(Operator):
    bl_idname = "object.hexagon_generator"
    bl_label = "Hexagon Generator"
    bl_description = "Generates a hexagon mesh"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        if(context.scene.delete_scene):
            self.deleteScene()

        self.createHexagon(context)
        return {'FINISHED'}

    def deleteScene(self):
        # selektiert alle Objekte
        bpy.ops.object.select_all(action='SELECT')
        # löscht selektierte objekte
        bpy.ops.object.delete(use_global=False, confirm=False)
        # löscht überbleibende Meshdaten etc.
        bpy.ops.outliner.orphans_purge()  # löscht überbleibende Meshdaten etc.

    def createHexagon(self, context):

        bpy.ops.mesh.primitive_plane_add()
        bpy.ops.object.modifier_add(type='NODES')

        geo_nodes = bpy.data.node_groups["Geometry Nodes"]
        group_out = geo_nodes.nodes["Group Output"]

        cylinder = geo_nodes.nodes.new(type='GeometryNodeMeshCylinder')
        cylinder.inputs[0].default_value = context.scene.hexagon_sides
        geo_nodes.links.new(cylinder.outputs[0], group_out.inputs[0])

        math_node = geo_nodes.nodes.new(type='ShaderNodeMath')
        inst_on_points = geo_nodes.nodes.new(type='GeometryNodeInstanceOnPoints')