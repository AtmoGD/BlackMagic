import bpy
from bpy.types import Operator, Struct

# Just a helper class so you don't have to always type "context.scene..."
class Params():
    def __init__(self, context):
        self.context = context
        self.created_world = context.scene.created_world
        self.nodes = context.scene.nodes

class OBJECT_OT_HexagonGenerator(Operator):
    bl_idname = "object.hexagon_generator"
    bl_label = "Hexagon Generator"
    bl_description = "Generates a hexagon mesh"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        # Check if we should delete the scene. Here we are using "context.scene" because params are not created yet
        if(context.scene.delete_scene):
            self.deleteScene(context)

        # Get all parameters
        params = Params(context)

        # If we already have a world, just change the parameters. Otherwise create a new one.
        if(params.created_world is None):
            self.GenerateWorld(params)
        else:
            self.ChangeParameters()

        return {'FINISHED'}

    def deleteScene(self, context):
        # Delete scene property references
        context.scene.created_world = None
        context.scene.nodes = None

        # Select all objects
        bpy.ops.object.select_all(action='SELECT')
        # Delete selected objects
        bpy.ops.object.delete(use_global=False, confirm=False)
        # Delete all meshdata etc. what is left
        bpy.ops.outliner.orphans_purge()

    def ChangeParameters(self):
        print("Change Parameters")

    def GenerateWorld(self, params):
        # Create new mesh and save it. It doesn't matter wich one we just need a mesh to add the geometry nodes
        bpy.ops.mesh.primitive_plane_add()
        params.created_world = params.context.selected_objects[0]
        params.created_world.name = "HexagonWorld"

        # Save the world in the scene propertys
        params.context.scene.created_world = params.created_world

        # Add the geometry nodes modifier and save it
        bpy.ops.object.modifier_add(type='NODES')
        params.nodes = params.created_world.modifiers[0]

        geo_nodes = bpy.data.node_groups["Geometry Nodes"]
        group_out = geo_nodes.nodes["Group Output"]

        cylinder = geo_nodes.nodes.new(type='GeometryNodeMeshCylinder')
        cylinder.inputs[0].default_value = params.scene.hexagon_sides
        geo_nodes.links.new(cylinder.outputs[0], group_out.inputs[0])

        math_node = geo_nodes.nodes.new(type='ShaderNodeMath')
        inst_on_points = geo_nodes.nodes.new(type='GeometryNodeInstanceOnPoints')