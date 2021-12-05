import bpy

bl_info = {
    "name": "Generate Biomes",
    "author": "Valentin, Fabian, Viktor, Lara",
    "version": (1, 0),
    "blender": (3, 0, 0),
    #"location": "View3D > Toolbar > Generate Biomes",
    "description": "Adds different biomes, where you can set different parameters",
    "warning": "",
    "wiki_url": "",
    "category": "Add Mesh",
}

def main(context, self):
    bpy.ops.object.select_all(action='SELECT')  # selektiert alle Objekte
    bpy.ops.object.delete(use_global=False, confirm=False)# löscht selektierte objekte
    bpy.ops.outliner.orphans_purge()  # löscht überbleibende Meshdaten etc.

    

    #for ob in context.scene.objects:
       # ob.location = loc


class SimpleOperator(bpy.types.Operator):
    bl_idname = "object.simple_operator"
    bl_label = "Simple Object Operator"
    bl_options = {"REGISTER", "UNDO"}

    print ("################  Test print  ################")

    



    @classmethod
    def poll(cls, context):
        return context.active_object is not None


    def execute(self, context):
        main(context, self)
        return {'FINISHED'}



def register():
    bpy.utils.register_class(SimpleOperator)

def unregister():
    bpy.utils.unregister_class(SimpleOperator)

if __name__ == "__main__":
    register() 

