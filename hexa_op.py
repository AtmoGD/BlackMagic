import bpy

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

        self.createHexagon()
        return {'FINISHED'}

    def deleteScene(self):
        # selektiert alle Objekte
        bpy.ops.object.select_all(action='SELECT')
        # löscht selektierte objekte
        bpy.ops.object.delete(use_global=False, confirm=False)
        # löscht überbleibende Meshdaten etc.
        bpy.ops.outliner.orphans_purge()  # löscht überbleibende Meshdaten etc.

    def createHexagon(self):
        # create a hexagon
        bpy.ops.mesh.primitive_plane_add()
        bpy.ops.object.modifier_add(type='NODES')
        nodeData = bpy.data.node_groups['Geometry Nodes'].nodes
        # nodes = bpy.context.object.modifiers["Nodes"]

