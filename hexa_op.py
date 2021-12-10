import bpy
from bpy.types import Operator, Struct

# Just a helper class so you don't have to always type "context.scene..."
class Params():
    def __init__(self, context):
        self.context = context
        self.created_world = context.scene.created_world
        self.hexagon_amount = context.scene.hexagon_amount
        self.hexagon_spacing = context.scene.hexagon_spacing
        self.source_hexagons = context.scene.source_hexagons

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
        # Create new Collection
        # collection = bpy.data.collections.new("HexagonWorld")
        # bpy.context.scene.collection.children.link(collection)

        # Add an empty object to manipulate transform animations and one for scale animations
        bpy.ops.object.empty_add()
        animation_transform_object = params.context.selected_objects[0]
        animation_transform_object.name = "AnimationTransformController"

        bpy.ops.object.empty_add()
        animation_scale_object = params.context.selected_objects[0]
        animation_scale_object.name = "AnimationScaleController"

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
        self.ChangeLocation(group_out, 4000, 0)

        # Create and update the input node with all the parameters
        self.CreateNodeInputs(geo_node_group)
        self.UpdateNodeInputs(geo_node_group, params)

        # ---------------------------------------- Start with the Nodes ------------------------------------
        
        positions = self.GeneratePositions(geo_node_group, group_in, nodes, animation_transform_object)
        masked_positions = self.GenerateMaskedPositions(geo_node_group, nodes, positions)

        instance_on_points = self.CreateInstantiateOnPointsNode(nodes, 3600, -1200)


        # Create the output node ---------------- JUST TESTING ---------------------------------------------
        geo_node_group.links.new(instance_on_points.outputs[0], group_out.inputs[0])

    def GeneratePositions(self, geo_node_group, group_in, nodes, animation_object):
        
        multiply = self.CreateMultiplyNode(nodes, x=0, y=300)
        geo_node_group.links.new(group_in.outputs["hexagon_amount"], multiply.inputs[0])
        geo_node_group.links.new(group_in.outputs["hexagon_amount"], multiply.inputs[1])

        mesh_line = self.CreateMeshLineNode(nodes, 200, 350)
        geo_node_group.links.new(multiply.outputs[0], mesh_line.inputs[0])

        index = self.CreateIndexNode(nodes, 0, -200)

        modulo = self.CreateModuloNode(nodes, 200, -50)
        geo_node_group.links.new(index.outputs[0], modulo.inputs[0])
        geo_node_group.links.new(group_in.outputs["hexagon_amount"], modulo.inputs[1])

        divide = self.CreateDivideNode(nodes, 200, -250)
        geo_node_group.links.new(index.outputs[0], divide.inputs[0])
        geo_node_group.links.new(group_in.outputs["hexagon_amount"], divide.inputs[1])

        floor = self.CreateFloorNode(nodes, 400, -200)
        geo_node_group.links.new(divide.outputs[0], floor.inputs[0])

        newModulo = self.CreateModuloNode(nodes, 600, -250)
        geo_node_group.links.new(floor.outputs[0], newModulo.inputs[0])
        newModulo.inputs[1].default_value = 2

        multiply = self.CreateMultiplyNode(nodes, 800, -250)
        geo_node_group.links.new(newModulo.outputs[0], multiply.inputs[0])
        multiply.inputs[1].default_value = 0.5

        add = self.CreateAddNode(nodes, 1000, -50)
        geo_node_group.links.new(modulo.outputs[0], add.inputs[0])
        geo_node_group.links.new(multiply.outputs[0], add.inputs[1])

        combineXYZ = self.CreateCombineXYZNode(nodes, 1200, -150)
        geo_node_group.links.new(add.outputs[0], combineXYZ.inputs[0])
        geo_node_group.links.new(floor.outputs[0], combineXYZ.inputs[1])
        combineXYZ.inputs[2].default_value = 0

        multiply_vector = self.CreateVectorMultiplyNode(nodes, 1400, -150)
        geo_node_group.links.new(combineXYZ.outputs[0], multiply_vector.inputs[0])
        multiply_vector.inputs[1].default_value = (1.732, 1.5, 1)

        add = self.CreateAddNode(nodes, 1400, -400)
        add.inputs[0].default_value = 1
        geo_node_group.links.new(group_in.outputs["hexagon_spacing"], add.inputs[1])

        vector_scale = self.CreateVectorScaleNode(nodes, 1600, -150)
        geo_node_group.links.new(multiply_vector.outputs[0], vector_scale.inputs[0])
        geo_node_group.links.new(add.outputs[0], vector_scale.inputs[3])

        set_position = self.CreateSetPositionNode(nodes, 1800, 0)
        geo_node_group.links.new(mesh_line.outputs[0], set_position.inputs[0])
        geo_node_group.links.new(vector_scale.outputs[0], set_position.inputs[2])

        bounding_box = self.CreateBoundingBoxNode(nodes, 2000, -200)
        geo_node_group.links.new(set_position.outputs[0], bounding_box.inputs[0])

        vector_add = self.CreateVectorAddNode(nodes, 2200, -200)
        geo_node_group.links.new(bounding_box.outputs[1], vector_add.inputs[0])
        geo_node_group.links.new(bounding_box.outputs[2], vector_add.inputs[1])

        value = self.CreateValueNode(nodes, 2200, -400, -0.5)
        
        vector_scale = self.CreateVectorScaleNode(nodes, 2400, -200)
        geo_node_group.links.new(vector_add.outputs[0], vector_scale.inputs[0])
        geo_node_group.links.new(value.outputs[0], vector_scale.inputs[3])

        new_set_position = self.CreateSetPositionNode(nodes, 2600, 0)
        geo_node_group.links.new(set_position.outputs[0], new_set_position.inputs[0])
        geo_node_group.links.new(vector_scale.outputs[0], new_set_position.inputs[3])

        transform = self.CreateTransformNode(nodes, 2800, 0)
        geo_node_group.links.new(new_set_position.outputs[0], transform.inputs[0])
        
        object_information = self.CreateObjectInfoNode(nodes, 2600, -400)
        object_information.inputs[0].default_value = animation_object
        geo_node_group.links.new(object_information.outputs[2], transform.inputs[3])

        return transform

    def GenerateMaskedPositions(self, geo_node_group, nodes, positions):
        gradient_texture = self.CreateGradientTextureNode(nodes, 1200, -1200)

        multiply = self.CreateMultiplyNode(nodes, 1400, -1200)
        multiply.inputs[1].default_value = 6
        geo_node_group.links.new(gradient_texture.outputs[1], multiply.inputs[0])

        floor = self.CreateFloorNode(nodes, 1600, -1200)
        geo_node_group.links.new(multiply.outputs[0], floor.inputs[0])

        add = self.CreateAddNode(nodes, 1800, -1200)
        geo_node_group.links.new(floor.outputs[0], add.inputs[0])
        add.inputs[1].default_value = 0.5

        divide = self.CreateDivideNode(nodes, 2000, -1200)
        geo_node_group.links.new(add.outputs[0], divide.inputs[0])
        divide.inputs[1].default_value = 6

        multiply = self.CreateMultiplyNode(nodes, 2200, -1200)
        geo_node_group.links.new(divide.outputs[0], multiply.inputs[0])
        multiply.inputs[1].default_value = 6.283

        cosine = self.CreateCosineNode(nodes, 2400, -1100)
        geo_node_group.links.new(multiply.outputs[0], cosine.inputs[0])

        sine = self.CreateSineNode(nodes, 2400, -1300)
        geo_node_group.links.new(multiply.outputs[0], sine.inputs[0])

        combine_xyz = self.CreateCombineXYZNode(nodes, 2600, -1200)
        geo_node_group.links.new(cosine.outputs[0], combine_xyz.inputs[0])
        geo_node_group.links.new(sine.outputs[0], combine_xyz.inputs[1])
        combine_xyz.inputs[2].default_value = 0

        position = self.CreateInputPositionNode(nodes, 2600, -1400)

        dot_product = self.CreateVectorDotProductNode(nodes, 2800, -1200)
        geo_node_group.links.new(combine_xyz.outputs[0], dot_product.inputs[0])
        geo_node_group.links.new(position.outputs[0], dot_product.inputs[1])

        less_than = self.CreateFloatLessThanNode(nodes, 3000, -1200)
        # geo_node_group.links.new(dot_product.outputs[0], less_than.inputs[0])
        # less_than.inputs[0].default_value = 0.5
        geo_node_group.links.new(dot_product.outputs[0], less_than.inputs[0])
        less_than.inputs[1].default_value = -50

        delete_geometry = self.CreateDeleteGeometryNode(nodes, 3200, -1000)
        geo_node_group.links.new(positions.outputs[0], delete_geometry.inputs[0])
        geo_node_group.links.new(less_than.outputs[0], delete_geometry.inputs[1])

        return delete_geometry

    def CreateNodeInputs(self, node_group):
        node_group.inputs.new(type='NodeSocketInt', name='hexagon_amount')
        node_group.inputs.new(type='NodeSocketFloat', name='hexagon_spacing')
        # node_group.inputs.new(type='NodeSocketCollection', name='source_hexagons')

    def UpdateNodeInputs(self, node_group, params):
        node_group.inputs["hexagon_amount"].default_value = params.hexagon_amount
        bpy.data.objects["HexagonWorld"].modifiers["GeometryNodes"]["Input_2"] = params.hexagon_amount
        node_group.inputs["hexagon_spacing"].default_value = params.hexagon_spacing
        bpy.data.objects["HexagonWorld"].modifiers["GeometryNodes"]["Input_3"] = params.hexagon_spacing
        # node_group.inputs["source_hexagons"].default_value = params.source_hexagons

    def CreateValueNode(self, nodes, x=0, y=0, value=0):
        value_node = nodes.new(type='ShaderNodeValue')
        value_node.outputs[0].default_value = value
        self.ChangeLocation(value_node, x, y)
        return value_node

    def CreateVectorNode(self, nodes, value=(1, 1, 1), x=0, y=0):
        vector_input = nodes.new(type='FunctionNodeInputVector')
        self.ChangeLocation(vector_input, x, y)
        vector_input.outputs[0].default_value = value
        return vector_input

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

    def CreateAddNode(self, nodes, x=0, y=0, clamp=False):
        add = nodes.new(type='ShaderNodeMath')
        add.operation = 'ADD'
        add.use_clamp = clamp
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

    def CreateMathLessThanNode(self, nodes, x=0, y=0):
        less_than = nodes.new(type='ShaderNodeMath')
        less_than.operation = 'LESS_THAN'
        self.ChangeLocation(less_than, x, y)
        return less_than

    def CreateFloatLessThanNode(self, nodes, x=0, y=0):
        less_than = nodes.new(type='FunctionNodeCompareFloats')
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
    
    def CreateInputPositionNode(self, nodes, x=0, y=0):
        input_position = nodes.new(type='GeometryNodeInputPosition')
        self.ChangeLocation(input_position, x, y)
        return input_position

    def ChangeLocation(self, node, x, y):
        node.location.xy = (x, y)