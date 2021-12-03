import bpy


def main(context, loc):
    bpy.ops.object.select_all(action='SELECT')  # selektiert alle Objekte
    bpy.ops.object.delete(use_global=False, confirm=False)# löscht selektierte objekte
    bpy.ops.outliner.orphans_purge()  # löscht überbleibende Meshdaten etc.


    for ob in context.scene.objects:
        ob.location = loc


class SimpleOperator(bpy.types.Operator):
    bl_idname = "object.simple_operator"
    bl_label = "Simple Object Operator"
    bl_options = {"REGISTER", "UNDO"}

    bpy.ops.transform.translate(value=(-15.2647, -0, -0), orient_axis_ortho='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=False, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)



@classmethod
def poll(cls, context):
    return context.active_object is not None


def execute(self, context):
    main(context, self.my_vec)
    return {'FINISHED'}


my_vec: bpy.props.FloatVectorProperty(
    name='My Vector',
    description='does stuff with the thing.',
    default=(1, 1, 1))


def register():
    bpy.utils.register_class(SimpleOperator)