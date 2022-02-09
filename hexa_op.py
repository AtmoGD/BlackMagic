import bpy
# from bpy.ops.object import collection_add
from bpy.types import Mask, Operator

# Just a helper class so you don't have to always type "context.scene..."


class Params():
    def __init__(self, context):
        self.context = context
        self.created_world = context.scene.created_world
        self.hexagon_amount = context.scene.hexagon_amount
        self.hexagon_spacing = context.scene.hexagon_spacing
        self.height_min = context.scene.height_min
        self.height_max = context.scene.height_max
        self.sea_level = context.scene.sea_level
        self.noise = context.scene.noise
        self.object_probability = context.scene.object_probability


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

        for c in context.scene.collection.children:
            context.scene.collection.children.unlink(c)

        # Select all objects
        bpy.ops.object.select_all(action='SELECT')
        # Delete selected objects
        bpy.ops.object.delete(use_global=True, confirm=False)
        # Delete all meshdata etc. what is left
        bpy.ops.outliner.orphans_purge()

    def ChangeParameters(self, params):

        self.UpdateNodeInputs(params.created_world.modifiers[0].node_group, params)
        print("Change Parameters")

    def GenerateWorld(self, params):

        # Create new Collection
        collection_hexa_world = bpy.data.collections.new("HEXAGON_WORLD")
        collection_camera_lights = bpy.data.collections.new("CAMERA & LIGHTS")
        collection_hexagons = bpy.data.collections.new("HEXAGONS")
        collection_objects = bpy.data.collections.new("OBJECTS")

        # A Add Collections to Scene
        bpy.context.scene.collection.children.link(collection_hexa_world)
        bpy.context.scene.collection.children.link(collection_camera_lights)
        bpy.context.scene.collection.children.link(collection_hexagons)
        bpy.context.scene.collection.children.link(collection_objects)

        # Create world hexagons
        self.CreateHexagonTiles(params, collection_hexagons)

        # Create objects
        self.CreateObjects(params, collection_objects)

        # Create camera and lights
        self.CreateCameraAndLights(params, collection_camera_lights)

        # Turn off object and hexagon collecitons
        collection_hexagons.hide_viewport = True
        collection_objects.hide_viewport = True
        collection_hexagons.hide_render = True
        collection_objects.hide_render = True

        # Add an empty object to manipulate transform animations and one for scale animations
        bpy.ops.mesh.primitive_plane_add()
        animation_transform_object = params.context.selected_objects[0]
        animation_transform_object.name = "AnimationTransformController"
        self.RemoveFromOldCollections(animation_transform_object)
        collection_hexa_world.objects.link(animation_transform_object)

        bpy.ops.mesh.primitive_plane_add()
        animation_scale_object = params.context.selected_objects[0]
        animation_scale_object.name = "AnimationScaleController"
        self.RemoveFromOldCollections(animation_scale_object)
        collection_hexa_world.objects.link(animation_scale_object)

        # Create new mesh and save it. It doesn't matter wich one we just need a mesh to add the geometry nodes
        bpy.ops.mesh.primitive_plane_add()
        params.created_world = params.context.selected_objects[0]
        params.created_world.name = "HexagonWorld"

        # Save the world in the scene propertys
        params.context.scene.created_world = params.created_world

        # Add the geometry nodes modifier and save it
        bpy.ops.object.modifier_add(type='NODES')
        geo_mod = params.created_world.modifiers[0]

        self.RemoveFromOldCollections(params.created_world)
        collection_hexa_world.objects.link(params.created_world)

        # Get the geo node group, the nodes, the node output and node input
        geo_node_group = geo_mod.node_group
        nodes = geo_node_group.nodes

        group_in = nodes["Group Input"]
        self.ChangeNodeLocation(group_in, -1000, -500)

        group_out = nodes["Group Output"]
        self.ChangeNodeLocation(group_out, 7000, 0)

        # Create and update the input node with all the parameters
        self.CreateNodeInputs(geo_node_group)
        self.UpdateNodeInputs(geo_node_group, params)

        # ---------------------------------------- Start with the Nodes ------------------------------------

        positions = self.GeneratePositions(geo_node_group, group_in, nodes, animation_transform_object)
        masked_positions = self.GenerateMaskedPositions(geo_node_group, nodes, group_in, positions)
        hexagons, instance_index, scale = self.GenerateHexagons(geo_node_group, nodes, masked_positions, collection_hexagons, group_in, animation_transform_object, animation_scale_object)
        water = self.GenerateWater(geo_node_group, nodes, masked_positions, group_in)
        objects = self.GeneratePlacedObjects(geo_node_group, nodes, masked_positions, instance_index, scale, collection_objects, group_in=group_in)

        join_geometry = self.CreateJoinGeometryNode(nodes, 6400, 0)
        join_geometry_second = self.CreateJoinGeometryNode(nodes, 5800, -1600)

        geo_node_group.links.new(water.outputs[0], join_geometry.inputs[0])
        geo_node_group.links.new(join_geometry_second.outputs[0], join_geometry.inputs[0])

        geo_node_group.links.new(hexagons.outputs[0], join_geometry_second.inputs[0])
        geo_node_group.links.new(objects.outputs[0], join_geometry_second.inputs[0])

        # Create the output node
        geo_node_group.links.new(join_geometry.outputs[0], group_out.inputs[0])

    def RemoveFromOldCollections(self, object):
        for col in object.users_collection:
            col.objects.unlink(object)

    def CreateNodeInputs(self, node_group):
        node_group.inputs.new(type='NodeSocketInt', name='hexagon_amount')
        node_group.inputs.new(type='NodeSocketFloat', name='hexagon_spacing')
        node_group.inputs.new(type='NodeSocketFloat', name='height_min')
        node_group.inputs.new(type='NodeSocketFloat', name='height_max')
        node_group.inputs.new(type='NodeSocketFloat', name='sea_level')
        node_group.inputs.new(type='NodeSocketFloat', name='noise')
        node_group.inputs.new(type='NodeSocketFloat', name='object_probability')

    def UpdateNodeInputs(self, node_group, params):
        node_group.inputs["hexagon_amount"].default_value = params.hexagon_amount
        bpy.data.objects["HexagonWorld"].modifiers["GeometryNodes"]["Input_2"] = params.hexagon_amount
        node_group.inputs["hexagon_spacing"].default_value = params.hexagon_spacing
        bpy.data.objects["HexagonWorld"].modifiers["GeometryNodes"]["Input_3"] = params.hexagon_spacing
        node_group.inputs["height_min"].default_value = params.height_min
        bpy.data.objects["HexagonWorld"].modifiers["GeometryNodes"]["Input_4"] = params.height_min
        node_group.inputs["height_max"].default_value = params.height_max
        bpy.data.objects["HexagonWorld"].modifiers["GeometryNodes"]["Input_5"] = params.height_max
        node_group.inputs["sea_level"].default_value = params.sea_level
        bpy.data.objects["HexagonWorld"].modifiers["GeometryNodes"]["Input_6"] = params.sea_level
        node_group.inputs["noise"].default_value = params.noise
        bpy.data.objects["HexagonWorld"].modifiers["GeometryNodes"]["Input_7"] = params.noise
        node_group.inputs["object_probability"].default_value = params.object_probability
        bpy.data.objects["HexagonWorld"].modifiers["GeometryNodes"]["Input_8"] = params.object_probability
    
    def CreateHexagonTiles(self, params, collection_hexagons):
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=1, depth=1)
        hexagon_mesh = params.context.selected_objects[0]
        sand_material = self.CreateBasicMaterial("Sand", [0.8, 0.435, 0.19, 1])
        hexagon_mesh.data.materials.append(sand_material)
        hexagon_mesh.name = "001.Sand"
        self.RemoveFromOldCollections(hexagon_mesh)
        collection_hexagons.objects.link(hexagon_mesh)

        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=1, depth=1)
        hexagon_mesh = params.context.selected_objects[0]
        gras_material = self.CreateBasicMaterial(
            "Gras", [0.255, 0.8, 0.124, 1])
        hexagon_mesh.data.materials.append(gras_material)
        hexagon_mesh.name = "002.Gras"
        self.RemoveFromOldCollections(hexagon_mesh)
        collection_hexagons.objects.link(hexagon_mesh)

        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=1, depth=1)
        hexagon_mesh = params.context.selected_objects[0]
        rock_material = self.CreateBasicMaterial("Rock", [0.08, 0.08, 0.08, 1])
        hexagon_mesh.data.materials.append(rock_material)
        hexagon_mesh.name = "003.Rock"
        self.RemoveFromOldCollections(hexagon_mesh)
        collection_hexagons.objects.link(hexagon_mesh)

        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=1, depth=1)
        hexagon_mesh = params.context.selected_objects[0]
        snow_material = self.CreateBasicMaterial("Snow", [0.8, 0.8, 0.8, 1])
        hexagon_mesh.data.materials.append(snow_material)
        hexagon_mesh.name = "004.Snow"
        self.RemoveFromOldCollections(hexagon_mesh)
        collection_hexagons.objects.link(hexagon_mesh)

    def CreateObjects(self, params, collection_objects):
        self.CreateTree(params, collection_objects)
        self.CreateBush(params, collection_objects)

    def CreateTree(self, params, collection_objects):
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.5, depth=2)
        tree_stamp = params.context.selected_objects[0]
        stamp_material = self.CreateBasicMaterial(
            "TreeStamp", [0.8, 0.142, 0.076, 1])
        tree_stamp.data.materials.append(stamp_material)
        tree_stamp.name = "Tree"
        self.RemoveFromOldCollections(tree_stamp)
        collection_objects.objects.link(tree_stamp)

        bpy.ops.mesh.primitive_cone_add()
        tree_leafs_first = params.context.selected_objects[0]
        leafs_material = self.CreateBasicMaterial(
            "TreeStamp", [0.465, 0.8, 0.128, 1])
        tree_leafs_first.data.materials.append(leafs_material)
        tree_leafs_first.name = "TreeLeafsFirst"
        self.RemoveFromOldCollections(tree_leafs_first)
        collection_objects.objects.link(tree_leafs_first)
        bpy.ops.transform.transform(value=(0, 0, 1, 0))

        bpy.ops.mesh.primitive_cone_add(radius1=0.9, depth=1.6)
        tree_leafs_second = params.context.selected_objects[0]
        tree_leafs_second.data.materials.append(leafs_material)
        tree_leafs_second.name = "TreeLeafsSecond"
        self.RemoveFromOldCollections(tree_leafs_second)
        collection_objects.objects.link(tree_leafs_second)
        bpy.ops.transform.transform(value=(0, 0, 1.8, 0))

        bpy.ops.object.select_all(action="DESELECT")
        tree_stamp.select_set(True)
        tree_leafs_first.select_set(True)
        tree_leafs_second.select_set(True)
        bpy.context.view_layer.objects.active = tree_stamp
        bpy.ops.object.join()

    def CreateBush(self, params, collection_objects):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.5)
        bush = params.context.selected_objects[0]
        bush_material = self.CreateBasicMaterial(
            "Bush", [0.465, 0.8, 0.128, 1])
        bush.data.materials.append(bush_material)
        bush.name = "Bush"
        self.RemoveFromOldCollections(bush)
        collection_objects.objects.link(bush)

        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.5)
        bush_second = params.context.selected_objects[0]
        bush_second.data.materials.append(bush_material)
        bush_second.name = "Bush Second"
        self.RemoveFromOldCollections(bush_second)
        collection_objects.objects.link(bush_second)
        bpy.ops.transform.transform(value=(0.2, 0.15, 0.25, 0))

        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.5)
        bush_third = params.context.selected_objects[0]
        bush_third.data.materials.append(bush_material)
        bush_third.name = "Bush Third"
        self.RemoveFromOldCollections(bush_third)
        collection_objects.objects.link(bush_third)
        bpy.ops.transform.transform(value=(-0.3, -0.2, 0.1, 0))

        bpy.ops.object.select_all(action="DESELECT")
        bush.select_set(True)
        bush_second.select_set(True)
        bush_third.select_set(True)
        bpy.context.view_layer.objects.active = bush
        bpy.ops.object.join()

    def CreateCameraAndLights(self, params, collection_objects):
        bpy.ops.object.camera_add(location=(154, -90, 150), rotation=(0.872665, 0.008727, 1.047198))
        camera = params.context.selected_objects[0]
        self.RemoveFromOldCollections(camera)
        collection_objects.objects.link(camera)

        bpy.ops.object.light_add(type="SUN", radius=1, location=(0, 0, 0), rotation=(0, -0.5, 0))
        light = params.context.selected_objects[0]
        light.data.energy = 5
        light.name = "Light"
        self.RemoveFromOldCollections(light)
        collection_objects.objects.link(light)

# <------------------------------------------------------------------------------- Generate the geometry nodes -------------------------------------------------------->

    def GeneratePlacedObjects(self, geo_node_group, nodes, masked_positions, range, offset, object_collection, group_in):
        equal = self.CreateCompareFloatsNode(nodes, 4600, -3000, "EQUAL")
        equal.inputs[1].default_value = 1.5
        equal.inputs[2].default_value = 0.5
        geo_node_group.links.new(range.outputs[0], equal.inputs[0])

        random_value = self.CreateRandomValueNode(nodes, 4600, -3200, "BOOLEAN")
        geo_node_group.links.new(group_in.outputs["object_probability"], random_value.inputs[6])

        multiply = self.CreateMultiplyNode(nodes, 4800, -3100)
        geo_node_group.links.new(equal.outputs[0], multiply.inputs[0])
        geo_node_group.links.new(random_value.outputs[3], multiply.inputs[1])

        collection_info = self.CreateCollectionInfoNode(nodes, 5000, -3300)
        collection_info.inputs[0].default_value = object_collection

        seperate = self.CreateSeperateXYZNode(nodes, 4400, -3600)
        geo_node_group.links.new(offset.outputs[0], seperate.inputs[0])

        add = self.CreateAddNode(nodes, 4600, -3600, second_value=1)
        geo_node_group.links.new(seperate.outputs[2], add.inputs[0])

        multiply_second = self.CreateMultiplyNode(nodes, 4800, -3600, second_value=1)
        geo_node_group.links.new(add.outputs[0], multiply_second.inputs[0])

        combine = self.CreateCombineXYZNode(nodes, 5000, -3600, input_x=0, input_y=0)
        geo_node_group.links.new(multiply_second.outputs[0], combine.inputs[2])

        instance_on_points = self.CreateInstantiateOnPointsNode(nodes, 5200, -3100)
        geo_node_group.links.new(masked_positions.outputs[0], instance_on_points.inputs[0])
        geo_node_group.links.new(multiply.outputs[0], instance_on_points.inputs[1])
        geo_node_group.links.new(collection_info.outputs[0], instance_on_points.inputs[2])

        set_position = self.CreateSetPositionNode(nodes, 5400, -3300)
        geo_node_group.links.new(instance_on_points.outputs[0], set_position.inputs[0])
        geo_node_group.links.new(combine.outputs[0], set_position.inputs[3])

        return set_position

    def GenerateWater(self, geo_node_group, nodes, masked_positions, group_in):
        bounding_box = self.CreateBoundingBoxNode(nodes, 3600, 0)
        geo_node_group.links.new(masked_positions.outputs[0], bounding_box.inputs[0])

        seperate_xyz = self.CreateSeperateXYZNode(nodes, 3800, 0)
        geo_node_group.links.new(bounding_box.outputs[2], seperate_xyz.inputs[0])

        cylinder = self.CreateCylinderNode(nodes, x=4000, y=0)
        geo_node_group.links.new(seperate_xyz.outputs[0], cylinder.inputs[3])
        cylinder.inputs[4].default_value = 1

        transform = self.CreateTransformNode(nodes, x=4200, y=0, trans_z=0.5)
        geo_node_group.links.new(cylinder.outputs[0], transform.inputs[0])

        add = self.CreateAddNode(nodes, x=4000, y=-500)
        geo_node_group.links.new(group_in.outputs["sea_level"], add.inputs[1])

        combine_xyz = self.CreateCombineXYZNode(nodes, x=4200, y=-500, input_x=1, input_y=1)
        geo_node_group.links.new(add.outputs[0], combine_xyz.inputs[2])

        transform_second = self.CreateTransformNode(nodes, x=4400, y=0)
        geo_node_group.links.new( transform.outputs[0], transform_second.inputs[0])
        geo_node_group.links.new(combine_xyz.outputs[0], transform_second.inputs[3])

        water_material = self.CreateWaterMaterial([0.342, 0.8, 1, 1], 0.1, 2)
        set_material = self.CreateSetMaterialNode(nodes, water_material, x=4600, y=0)
        geo_node_group.links.new(transform_second.outputs[0], set_material.inputs[0])

        return set_material

    def GenerateHexagons(self, geo_node_group, nodes, masked_positions, hexa_collection, group_in, animation_transform_object, animation_scale_object):
        position = self.CreateInputPositionNode(nodes, 1400, -2000)

        object_input = self.CreateObjectInfoNode(nodes, 1400, -2100)
        object_input.inputs[0].default_value = animation_transform_object

        subtract = self.CreateVectorSubtractNode(nodes, 1600, -2000)
        geo_node_group.links.new(position.outputs[0], subtract.inputs[0])
        geo_node_group.links.new(object_input.outputs[0], subtract.inputs[1])

        vector_rotate = self.CreateVectorRotateNode(nodes, 1800, -2000, invert=True)
        geo_node_group.links.new(subtract.outputs[0], vector_rotate.inputs[0])
        geo_node_group.links.new(object_input.outputs[1], vector_rotate.inputs[4])

        multiply = self.CreateVectorMultiplyNode(nodes, 2000, -2000)
        geo_node_group.links.new(vector_rotate.outputs[0], multiply.inputs[0])
        geo_node_group.links.new(object_input.outputs[2], multiply.inputs[1])

        noise_texture = self.CreateNoiseTextureNode(nodes, 2200, -2000)
        geo_node_group.links.new(multiply.outputs[0], noise_texture.inputs[0])
        geo_node_group.links.new(group_in.outputs["noise"], noise_texture.inputs[2])
        noise_texture.inputs[3].default_value = 0

        map_range = self.CreateMapRangeNode(nodes, 2400, -2200)
        geo_node_group.links.new(noise_texture.outputs[0], map_range.inputs[0])
        geo_node_group.links.new(group_in.outputs["height_min"], map_range.inputs[3])
        geo_node_group.links.new(group_in.outputs["height_max"], map_range.inputs[4])

        combine_xyz = self.CreateCombineXYZNode(nodes, 2600, -2300, 1, 1)
        geo_node_group.links.new(map_range.outputs[0], combine_xyz.inputs[2])

        object_input_second = self.CreateObjectInfoNode(nodes, 2600, -2100)
        object_input_second.inputs[0].default_value = animation_scale_object

        multiply = self.CreateVectorMultiplyNode(nodes, 2800, -2200)
        geo_node_group.links.new(object_input_second.outputs[2], multiply.inputs[0])
        geo_node_group.links.new(combine_xyz.outputs[0], multiply.inputs[1])

        map_range_second = self.CreateMapRangeNode(nodes, 2800, -1700, to_max=len(hexa_collection.objects))
        geo_node_group.links.new(noise_texture.outputs[0], map_range_second.inputs[0])

        collection_info = self.CreateCollectionInfoNode(nodes, 2800, -2000)
        collection_info.inputs[0].default_value = hexa_collection

        transform = self.CreateTransformNode(nodes, 3200, -2000, trans_z=0.5)
        geo_node_group.links.new(collection_info.outputs[0], transform.inputs[0])

        instance_on_points = self.CreateInstantiateOnPointsNode(nodes, 3600, -2000)
        geo_node_group.links.new(masked_positions.outputs[0], instance_on_points.inputs[0])
        geo_node_group.links.new(noise_texture.outputs[0], instance_on_points.inputs[1])
        geo_node_group.links.new(transform.outputs[0], instance_on_points.inputs[2])
        geo_node_group.links.new(map_range_second.outputs[0], instance_on_points.inputs[4])
        geo_node_group.links.new(multiply.outputs[0], instance_on_points.inputs[6])

        return instance_on_points, map_range_second, multiply

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

    def GenerateMaskedPositions(self, geo_node_group, nodes, group_in, positions):
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

        multiply = self.CreateMultiplyNode(nodes, 2800, -1400, -0.5)
        geo_node_group.links.new(
            group_in.outputs["hexagon_amount"], multiply.inputs[1])

        less_than = self.CreateCompareFloatsNode(nodes, 3000, -1200)
        geo_node_group.links.new(dot_product.outputs[1], less_than.inputs[0])
        geo_node_group.links.new(multiply.outputs[0], less_than.inputs[1])

        delete_geometry = self.CreateDeleteGeometryNode(nodes, 3200, -1000)
        geo_node_group.links.new(
            positions.outputs[0], delete_geometry.inputs[0])
        geo_node_group.links.new(
            less_than.outputs[0], delete_geometry.inputs[1])

        return delete_geometry

# <------------------------------------------------------------------------------- The code to create all the nodes -------------------------------------------------------->

    def CreateBasicMaterial(self, name, color):
        material = bpy.data.materials.new(name)
        material.use_nodes = True
        material_nodes = material.node_tree.nodes
        material_nodes["Principled BSDF"].inputs[0].default_value = color
        return material

    def CreateWaterMaterial(self, color, roughness, iqr):
        material = bpy.data.materials.new("Water")
        material.use_nodes = True
        material_nodes = material.node_tree.nodes

        glass_node = material_nodes.new("ShaderNodeBsdfGlass")
        glass_node.inputs[0].default_value = color
        glass_node.inputs[1].default_value = roughness
        glass_node.inputs[2].default_value = iqr

        output = material_nodes["Material Output"]

        material.node_tree.links.new(glass_node.outputs[0], output.inputs[0])

        return material

    def CreateValueNode(self, nodes, x=0, y=0, value=0):
        value_node = nodes.new(type='ShaderNodeValue')
        value_node.outputs[0].default_value = value
        self.ChangeNodeLocation(value_node, x, y)
        return value_node

    def CreateRandomValueNode(self, nodes, x=0, y=0, mode="BOOLEAN"):
        random = nodes.new(type='FunctionNodeRandomValue')
        random.data_type = mode
        self.ChangeNodeLocation(random, x, y)
        return random

    def CreateVectorNode(self, nodes, value=(1, 1, 1), x=0, y=0):
        vector_input = nodes.new(type='FunctionNodeInputVector')
        self.ChangeNodeLocation(vector_input, x, y)
        vector_input.outputs[0].default_value = value
        return vector_input

    def CreateGradientTextureNode(self, nodes, x=0, y=0, gradient_type='RADIAL'):
        gradient_texture = nodes.new(type='ShaderNodeTexGradient')
        gradient_texture.gradient_type = gradient_type
        self.ChangeNodeLocation(gradient_texture, x, y)
        return gradient_texture

    def CreateNoiseTextureNode(self, nodes, x=0, y=0, noise_dimensions='2D'):
        noise_texture = nodes.new(type='ShaderNodeTexNoise')
        noise_texture.noise_dimensions = noise_dimensions
        self.ChangeNodeLocation(noise_texture, x, y)
        return noise_texture

    def CreateJoinGeometryNode(self, nodes, x=0, y=0):
        join_geometry = nodes.new(type='GeometryNodeJoinGeometry')
        self.ChangeNodeLocation(join_geometry, x, y)
        return join_geometry

    def CreateCylinderNode(self, nodes, sides=6, x=0, y=0):
        cylinder = nodes.new(type='GeometryNodeMeshCylinder')
        cylinder.inputs[0].default_value = sides
        self.ChangeNodeLocation(cylinder, x, y)
        return cylinder

    def CreateAddNode(self, nodes, x=0, y=0, clamp=False, first_value=0, second_value=0):
        add = nodes.new(type='ShaderNodeMath')
        add.operation = 'ADD'
        add.use_clamp = clamp
        add.inputs[0].default_value = first_value
        add.inputs[1].default_value = second_value
        self.ChangeNodeLocation(add, x, y)
        return add

    def CreateMultiplyNode(self, nodes, x=0, y=0, first_value=0, second_value=0):
        multiply = nodes.new(type='ShaderNodeMath')
        multiply.operation = 'MULTIPLY'
        multiply.inputs[0].default_value = first_value
        multiply.inputs[1].default_value = second_value
        self.ChangeNodeLocation(multiply, x, y)
        return multiply

    def CreateModuloNode(self, nodes, x=0, y=0):
        modulo = nodes.new(type='ShaderNodeMath')
        modulo.operation = 'MODULO'
        self.ChangeNodeLocation(modulo, x, y)
        return modulo

    def CreateDivideNode(self, nodes, x=0, y=0):
        divide = nodes.new(type='ShaderNodeMath')
        divide.operation = 'DIVIDE'
        self.ChangeNodeLocation(divide, x, y)
        return divide

    def CreateFloorNode(self, nodes, x=0, y=0):
        floor = nodes.new(type='ShaderNodeMath')
        floor.operation = 'FLOOR'
        self.ChangeNodeLocation(floor, x, y)
        return floor

    def CreateGreaterThanNode(self, nodes, x=0, y=0):
        greater_than = nodes.new(type='ShaderNodeMath')
        greater_than.operation = 'GREATER_THAN'
        self.ChangeNodeLocation(greater_than, x, y)
        return greater_than

    def CreateMathLessThanNode(self, nodes, x=0, y=0):
        less_than = nodes.new(type='ShaderNodeMath')
        less_than.operation = 'LESS_THAN'
        self.ChangeNodeLocation(less_than, x, y)
        return less_than

    def CreateCompareFloatsNode(self, nodes, x=0, y=0, operation="LESS_THAN"):
        less_than = nodes.new(type='FunctionNodeCompareFloats')
        less_than.operation = operation
        self.ChangeNodeLocation(less_than, x, y)
        return less_than

    def CreateSineNode(self, nodes, x=0, y=0):
        sine = nodes.new(type='ShaderNodeMath')
        sine.operation = 'SINE'
        self.ChangeNodeLocation(sine, x, y)
        return sine

    def CreateCosineNode(self, nodes, x=0, y=0):
        cosine = nodes.new(type='ShaderNodeMath')
        cosine.operation = 'COSINE'
        self.ChangeNodeLocation(cosine, x, y)
        return cosine

    def CreateCombineXYZNode(self, nodes, x=0, y=0, input_x=0, input_y=0, input_z=0):
        cobine_xyz = nodes.new(type='ShaderNodeCombineXYZ')
        cobine_xyz.inputs[0].default_value = input_x
        cobine_xyz.inputs[1].default_value = input_y
        cobine_xyz.inputs[2].default_value = input_z
        self.ChangeNodeLocation(cobine_xyz, x, y)
        return cobine_xyz

    def CreateSeperateXYZNode(self, nodes, x=0, y=0):
        seperate_xyz = nodes.new(type='ShaderNodeSeparateXYZ')
        self.ChangeNodeLocation(seperate_xyz, x, y)
        return seperate_xyz

    def CreateVectorMultiplyNode(self, nodes, x=0, y=0):
        vector_multiply = nodes.new(type='ShaderNodeVectorMath')
        vector_multiply.operation = 'MULTIPLY'
        self.ChangeNodeLocation(vector_multiply, x, y)
        return vector_multiply

    def CreateVectorAddNode(self, nodes, x=0, y=0):
        vector_add = nodes.new(type='ShaderNodeVectorMath')
        vector_add.operation = 'ADD'
        self.ChangeNodeLocation(vector_add, x, y)
        return vector_add

    def CreateVectorSubtractNode(self, nodes, x=0, y=0):
        vector_subtract = nodes.new(type='ShaderNodeVectorMath')
        vector_subtract.operation = 'SUBTRACT'
        self.ChangeNodeLocation(vector_subtract, x, y)
        return vector_subtract

    def CreateVectorScaleNode(self, nodes, x=0, y=0):
        vector_scale = nodes.new(type='ShaderNodeVectorMath')
        vector_scale.operation = 'SCALE'
        self.ChangeNodeLocation(vector_scale, x, y)
        return vector_scale

    def CreateVectorRotateNode(self, nodes, x=0, y=0, rotation_type='EULER_XYZ', invert=False):
        vector_rotate = nodes.new(type='ShaderNodeVectorRotate')
        vector_rotate.rotation_type = rotation_type
        vector_rotate.invert = invert
        self.ChangeNodeLocation(vector_rotate, x, y)
        return vector_rotate

    def CreateVectorDotProductNode(self, nodes, x=0, y=0):
        vector_dot_product = nodes.new(type='ShaderNodeVectorMath')
        vector_dot_product.operation = 'DOT_PRODUCT'
        self.ChangeNodeLocation(vector_dot_product, x, y)
        return vector_dot_product

    def CreateMapRangeNode(self, nodes, x=0, y=0, from_min=0, from_max=1, to_min=0, to_max=1):
        map_range = nodes.new(type='ShaderNodeMapRange')
        map_range.inputs[1].default_value = from_min
        map_range.inputs[2].default_value = from_max
        map_range.inputs[3].default_value = to_min
        map_range.inputs[4].default_value = to_max
        self.ChangeNodeLocation(map_range, x, y)
        return map_range

    def CreateTransformNode(self, nodes, x=0, y=0, trans_x=0, trans_y=0, trans_z=0):
        transform = nodes.new(type='GeometryNodeTransform')
        transform.inputs[1].default_value = [trans_x, trans_y, trans_z]
        self.ChangeNodeLocation(transform, x, y)
        return transform

    def CreateObjectInfoNode(self, nodes, x=0, y=0, transform_space="RELATIVE"):
        object_info = nodes.new(type='GeometryNodeObjectInfo')
        object_info.transform_space = transform_space
        self.ChangeNodeLocation(object_info, x, y)
        return object_info

    def CreateCollectionInfoNode(self, nodes, x=0, y=0, transform_space="ORIGINAL", seperate_children=True, reset_children=True):
        collection_info = nodes.new(type='GeometryNodeCollectionInfo')
        collection_info.transform_space = transform_space
        collection_info.inputs[1].default_value = seperate_children
        collection_info.inputs[2].default_value = reset_children
        self.ChangeNodeLocation(collection_info, x, y)
        return collection_info

    def CreateDeleteGeometryNode(self, nodes, x=0, y=0):
        delete_geometry = nodes.new(type='GeometryNodeDeleteGeometry')
        self.ChangeNodeLocation(delete_geometry, x, y)
        return delete_geometry

    def CreateSetPositionNode(self, nodes, x=0, y=0):
        set_position = nodes.new(type='GeometryNodeSetPosition')
        self.ChangeNodeLocation(set_position, x, y)
        return set_position
        
    def CreateSetMaterialNode(self, nodes, material, x=0, y=0):
        set_material = nodes.new(type='GeometryNodeSetMaterial')
        set_material.inputs[2].default_value = material
        self.ChangeNodeLocation(set_material, x, y)
        return set_material

    def CreateBoundingBoxNode(self, nodes, x=0, y=0):
        bounding_box = nodes.new(type='GeometryNodeBoundBox')
        self.ChangeNodeLocation(bounding_box, x, y)
        return bounding_box

    def CreateInstantiateOnPointsNode(self, nodes, x=0, y=0, pick_instance=True):
        inst_on_points = nodes.new(type='GeometryNodeInstanceOnPoints')
        self.ChangeNodeLocation(inst_on_points, x, y)
        inst_on_points.inputs[3].default_value = pick_instance
        return inst_on_points

    def CreateMeshLineNode(self, nodes, x=0, y=0):
        mesh_line = nodes.new(type='GeometryNodeMeshLine')
        self.ChangeNodeLocation(mesh_line, x, y)
        return mesh_line

    def CreateIndexNode(self, nodes, x=0, y=0):
        index = nodes.new(type='GeometryNodeInputIndex')
        self.ChangeNodeLocation(index, x, y)
        return index
    
    def CreateInputPositionNode(self, nodes, x=0, y=0):
        input_position = nodes.new(type='GeometryNodeInputPosition')
        self.ChangeNodeLocation(input_position, x, y)
        return input_position

    def ChangeNodeLocation(self, node, x, y):
        node.location.xy = (x, y)