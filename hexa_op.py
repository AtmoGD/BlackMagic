import bpy
from bpy import context

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
        plane = bpy.ops.mesh.primitive_plane_add()
        bpy.ops.object.modifier_add(type='NODES')

        # mod = bpy.data.objects[bpy.context.active_object.name].modifiers["GeometryNodes"]
        node_group = bpy.data.node_groups["Geometry Nodes"]
        node_group.nodes.new(type='GeometryNodeMeshCylinder')
        node_group.nodes.new(node_item='71')
        # new_node = 
        # group_in = node_group.
        # nodeData = bpy.data.node_groups['Geometry Nodes'].nodes
        # bpy.ops.node.select()
        
        # bpy.ops.node.select(wait_to_deselect_others=False, deselect_all=True)


        # bpy.ops.node.add_search(use_transform=True, node_item='97')
        # for key in mod.keys:
        #     print(key)


        # nodes = bpy.context.object.modifiers["Nodes"]

