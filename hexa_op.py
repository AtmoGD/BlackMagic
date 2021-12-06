import bpy

from bpy.types import Operator

class HexagonGenerator(Operator):
    bl_idname = "object.hexagon_generator"
    bl_label = "Hexagon Generator"
    bl_description = "Generates a hexagon mesh"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        self.deleteScene()
        return {'FINISHED'}

    def deleteScene():
        bpy.ops.object.select_all(action='SELECT')  # selektiert alle Objekte
        bpy.ops.object.delete(use_global=False, confirm=False)# löscht selektierte objekte
        bpy.ops.outliner.orphans_purge()  # löscht überbleibende Meshdaten etc.