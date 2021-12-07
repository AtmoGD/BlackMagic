import bpy
from bpy.types import Operator, Struct

# Just a helper class so you don't have to always type "context.scene..."
class Params():
    def __init__(self, context):
        self.context = context
        self.created_world = context.scene.created_world
        self.hexagon_amount = context.scene.hexagon_amount

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
            self.ChangeParameters(params)

        return {'FINISHED'}

    def deleteScene(self, context):
        # Delete scene property references
        context.scene.created_world = None

        # Select all objects
        bpy.ops.object.select_all(action='SELECT')
        # Delete selected objects
        bpy.ops.object.delete(use_global=False, confirm=False)
        # Delete all meshdata etc. what is left
        bpy.ops.outliner.orphans_purge()

    def ChangeParameters(self, params):

        self.UpdateNodeInputs(params.created_world.modifiers[0].node_group, params)
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
        geo_mod = params.created_world.modifiers[0]

        #Get the geo node group, the nodes, the node output and node input
        geo_node_group = geo_mod.node_group
        nodes = geo_node_group.nodes
        group_in = nodes["Group Input"]
        group_out = nodes["Group Output"]
        self.ChangeLocation(group_out, 2000, 500)

        # Create and update the input node with all the parameters
        self.CreateNodeInputs(geo_node_group)
        self.UpdateNodeInputs(geo_node_group, params)

        multiply = self.CreateMultiplyNode(nodes)
        geo_node_group.links.new(group_in.outputs["hexagon_amount"], multiply.inputs[0])
        geo_node_group.links.new(group_in.outputs["hexagon_amount"], multiply.inputs[1])

        mesh_line = self.CreateMeshLineNode(nodes, 200, 50)
        geo_node_group.links.new(multiply.outputs[0], mesh_line.inputs[0])



    def CreateNodeInputs(self, node_group):
        node_group.inputs.new(type='NodeSocketInt', name='hexagon_amount')

    def UpdateNodeInputs(self, node_group, params):
        node_group.inputs["hexagon_amount"].default_value = params.hexagon_amount

    def CreateGradientTextureNode(self, nodes, x=0, y=0, gradient_type='RADIAL'):
        gradient_texture = nodes.new(type='ShaderNodeTexGradient')
        gradient_texture.gradient_type = gradient_type
        self.ChangeLocation(gradient_texture, x, y)
        return gradient_texture

    def CreateNoiseTextureNode(self, nodes, x=0, y=0, noise_dimensions='2D'):
        noise_texture = nodes.new(type='ShaderNodeTexNoise')
        noise_texture.noise_dimensions = noise_dimensions
        self.ChangeLocation(noise_texture, x, y)
        return noise_texture

    def CreateJoinGeometryNode(self, nodes, x=0, y=0):
        join_geometry = nodes.new(type='GeometryNodeJoinGeometry')
        self.ChangeLocation(join_geometry, x, y)
        return join_geometry

    def CreateCylinderNode(self, nodes, sides=6, x=0, y=0):
        cylinder = nodes.new(type='GeometryNodeMeshCylinder')
        cylinder.inputs[0].default_value = sides
        self.ChangeLocation(cylinder, x, y)
        return cylinder

    def CreateAddNode(self, nodes, x=0, y=0):
        add = nodes.new(type='ShaderNodeMath')
        add.operation = 'ADD'
        self.ChangeLocation(add, x, y)
        return add

    def CreateMultiplyNode(self, nodes, x=0, y=0):
        multiply = nodes.new(type='ShaderNodeMath')
        multiply.operation = 'MULTIPLY'
        self.ChangeLocation(multiply, x, y)
        return multiply

    def CreateModuloNode(self, nodes, x=0, y=0):
        modulo = nodes.new(type='ShaderNodeMath')
        modulo.operation = 'MODULO'
        self.ChangeLocation(modulo, x, y)
        return modulo

    def CreateDivideNode(self, nodes, x=0, y=0):
        divide = nodes.new(type='ShaderNodeMath')
        divide.operation = 'DIVIDE'
        self.ChangeLocation(divide, x, y)
        return divide

    def CreateFloorNode(self, nodes, x=0, y=0):
        floor = nodes.new(type='ShaderNodeMath')
        floor.operation = 'FLOOR'
        self.ChangeLocation(floor, x, y)
        return floor

    def CreateGreaterThanNode(self, nodes, x=0, y=0):
        greater_than = nodes.new(type='ShaderNodeMath')
        greater_than.operation = 'GREATER_THAN'
        self.ChangeLocation(greater_than, x, y)
        return greater_than

    def CreateLessThanNode(self, nodes, x=0, y=0):
        less_than = nodes.new(type='ShaderNodeMath')
        less_than.operation = 'LESS_THAN'
        self.ChangeLocation(less_than, x, y)
        return less_than

    def CreateSineNode(self, nodes, x=0, y=0):
        sine = nodes.new(type='ShaderNodeMath')
        sine.operation = 'SINE'
        self.ChangeLocation(sine, x, y)
        return sine

    def CreateCosineNode(self, nodes, x=0, y=0):
        cosine = nodes.new(type='ShaderNodeMath')
        cosine.operation = 'COSINE'
        self.ChangeLocation(cosine, x, y)
        return cosine

    def CreateCombineXYZNode(self, nodes, x=0, y=0):
        cobine_xyz = nodes.new(type='ShaderNodeCombineXYZ')
        self.ChangeLocation(cobine_xyz, x, y)
        return cobine_xyz

    def CreateSeperateXYZNode(self, nodes, x=0, y=0):
        seperate_xyz = nodes.new(type='ShaderNodeSeparateXYZ')
        self.ChangeLocation(seperate_xyz, x, y)
        return seperate_xyz

    def CreateVectorMultiplyNode(self, nodes, x=0, y=0):
        vector_multiply = nodes.new(type='ShaderNodeVectorMath')
        vector_multiply.operation = 'MULTIPLY'
        self.ChangeLocation(vector_multiply, x, y)
        return vector_multiply

    def CreateVectorAddNode(self, nodes, x=0, y=0):
        vector_add = nodes.new(type='ShaderNodeVectorMath')
        vector_add.operation = 'ADD'
        self.ChangeLocation(vector_add, x, y)
        return vector_add

    def CreateVectorSubtractNode(self, nodes, x=0, y=0):
        vector_subtract = nodes.new(type='ShaderNodeVectorMath')
        vector_subtract.operation = 'SUBTRACT'
        self.ChangeLocation(vector_subtract, x, y)
        return vector_subtract

    def CreateVectorScaleNode(self, nodes, x=0, y=0):
        vector_scale = nodes.new(type='ShaderNodeVectorMath')
        vector_scale.operation = 'SCALE'
        self.ChangeLocation(vector_scale, x, y)
        return vector_scale

    def CreateVectorRotateNode(self, nodes, x=0, y=0, rotation_type='EULER_XYZ'):
        vector_rotate = nodes.new(type='ShaderNodeVectorRotate')
        vector_rotate.rotation_type = rotation_type
        self.ChangeLocation(vector_rotate, x, y)
        return vector_rotate

    def CreateVectorDotProductNode(self, nodes, x=0, y=0):
        vector_dot_product = nodes.new(type='ShaderNodeVectorMath')
        vector_dot_product.operation = 'DOT_PRODUCT'
        self.ChangeLocation(vector_dot_product, x, y)
        return vector_dot_product

    def CreateMapRangeNode(self, nodes, x=0, y=0):
        map_range = nodes.new(type='ShaderNodeMapRange')
        self.ChangeLocation(map_range, x, y)
        return map_range

    def CreateTransformNode(self, nodes, x=0, y=0):
        transform = nodes.new(type='GeometryNodeTransform')
        self.ChangeLocation(transform, x, y)
        return transform

    def CreateObjectInfoNode(self, nodes, x=0, y=0):
        object_info = nodes.new(type='GeometryNodeObjectInfo')
        self.ChangeLocation(object_info, x, y)
        return object_info

    def CreateCollectionInfoNode(self, nodes, x=0, y=0):
        collection_info = nodes.new(type='GeometryNodeCollectionInfo')
        self.ChangeLocation(collection_info, x, y)
        return collection_info

    def CreateDeleteGeometryNode(self, nodes, x=0, y=0):
        delete_geometry = nodes.new(type='GeometryNodeDeleteGeometry')
        self.ChangeLocation(delete_geometry, x, y)
        return delete_geometry

    def CreateSetPositionNode(self, nodes, x=0, y=0):
        set_position = nodes.new(type='GeometryNodeSetPosition')
        self.ChangeLocation(set_position, x, y)
        return set_position
        
    def CreateSetMaterialNode(self, nodes, x=0, y=0):
        set_material = nodes.new(type='GeometryNodeSetMaterial')
        self.ChangeLocation(set_material, x, y)
        return set_material

    def CreateBoundingBoxNode(self, nodes, x=0, y=0):
        bounding_box = nodes.new(type='GeometryNodeBoundBox')
        self.ChangeLocation(bounding_box, x, y)
        return bounding_box

    def CreateInstantiateOnPointsNode(self, nodes, x=0, y=0):
        inst_on_points = nodes.new(type='GeometryNodeInstanceOnPoints')
        self.ChangeLocation(inst_on_points, x, y)
        return inst_on_points

    def CreateMeshLineNode(self, nodes, x=0, y=0):
        mesh_line = nodes.new(type='GeometryNodeMeshLine')
        self.ChangeLocation(mesh_line, x, y)
        return mesh_line

    def CreateIndexNode(self, nodes, x=0, y=0):
        index = nodes.new(type='GeometryNodeInputIndex')
        self.ChangeLocation(index, x, y)
        return index
    
    def ChangeLocation(self, node, x, y):
        node.location.xy = (x, y)