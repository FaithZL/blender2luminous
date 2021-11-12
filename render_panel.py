import bpy
from . import render_exporter

class ExportPbrtScene(bpy.types.Operator):
    bl_idname = 'scene.export'
    bl_label = 'Export Scene To Luminous Renderer'
    bl_options = {"REGISTER", "UNDO"}
    COMPAT_ENGINES = {'Luminous_Renderer'}
    
    def execute(self, context):
        print("Starting calling pbrt_export")
        print("Output path:")
        filepath_full = bpy.path.abspath(bpy.data.scenes[0].exportpath)
        print(filepath_full)
        # for frameNumber in range(bpy.data.scenes['Scene'].batch_frame_start, bpy.data.scenes['Scene'].batch_frame_end +1):
        #     bpy.data.scenes['Scene'].frame_set(frameNumber)
        #     print("Exporting frame: %s" % (frameNumber))
        #     render_exporter.export_pbrt(filepath_full, bpy.data.scenes['Scene'], '{0:05d}'.format(frameNumber))
        render_exporter.export_pbrt(filepath_full, bpy.data.scenes['Scene'])
        self.report({'INFO'}, "Export complete.")
        return {"FINISHED"}

class PbrtRenderSettingsPanel(bpy.types.Panel):
    """Creates a Pbrt settings panel in the render context of the properties editor"""
    bl_label = "Luminous Render settings"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    COMPAT_ENGINES = {'Luminous_Renderer'}

    #Hide the pbrt render panel if PBRT render engine is not currently selected.
    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        if engine != 'Luminous_Renderer':
            return False
        else:
            return True

    def draw(self, context):
        engine = context.scene.render.engine
        if engine != 'Luminous_Renderer':
            bpy.utils.unregister_class(PbrtRenderSettingsPanel)

        layout = self.layout

        scene = context.scene

        # Create a simple row.
        layout.label(text="Output folder path")
        row = layout.row()
        
        row.prop(scene, "exportpath")

        layout.label(text=" Render output filename")
        row = layout.row()
        row.prop(scene,"outputfilename")

        layout.label(text="Environment Map")
        row = layout.row()
        row.prop(scene,"environmentmaptpath")

        layout.label(text="Environment map scale:")
        row = layout.row()
        row.prop(scene, "environmentmapscale")

        # layout.label(text="Frame settings:")
        # row = layout.row()
        # row.prop(scene, "batch_frame_start")
        # row.prop(scene, "batch_frame_end")

        layout.label(text="Resolution:")
        row = layout.row()
        row.prop(scene, "resolution_x")
        row.prop(scene, "resolution_y")
       
        layout.label(text="Filter settings:")
        row = layout.row()
        row.prop(scene,"filterType")
        row = layout.row()
        row.prop(scene,"filter_x_width")
        row.prop(scene,"filter_y_width")

        if scene.filterType == 'sinc':
            row = layout.row()
            row.prop(scene,"filter_tau")
        if scene.filterType == 'mitchell':
            row = layout.row()
            row.prop(scene,"filter_b")
            row.prop(scene,"filter_c")
        if scene.filterType == 'gaussian':
            row = layout.row()
            row.prop(scene,"filter_alpha")
            
        layout.label(text="Integrator settings:")
        row = layout.row()

        row.prop(scene,"integrators")
        row.prop(scene,"maxdepth")
        
        if scene.integrators == 'PT':
            row = layout.row()
            row.prop(scene,"rr_threshold")


        layout.label(text="Sampler settings:")
        row = layout.row()
        row.prop(scene,"sampler")
        row = layout.row()
        if scene.sampler == 'halton':
            row.prop(scene,"spp")
            row.prop(scene,"samplepixelcenter")
        if scene.sampler == 'PCGSampler':
            row.prop(scene,"spp")
            

        # layout.label(text="Depth of field:")
        # row = layout.row()
        # row.prop(scene,"dofLookAt")
        # row = layout.row()
        # row.prop(scene, "lensradius")

        layout.label(text="Light strategy:")
        row = layout.row()
        row.prop(scene,"lightsamplestrategy")
        
        layout.label(text="Export:")
        row = layout.row()
        layout.operator("scene.export", icon='MESH_CUBE', text="Export scene")

def register():
    
    bpy.types.Scene.exportpath = bpy.props.StringProperty(
        name="",
        description="Export folder",
        default="",
        maxlen=1024,
        subtype='DIR_PATH')

    bpy.types.Scene.environmentmaptpath = bpy.props.StringProperty(
        name="",
        description="Environment map",
        default="",
        maxlen=1024,
        subtype='FILE_PATH')

    bpy.types.Scene.outputfilename = bpy.props.StringProperty(
        name="",
        description="Image output file name",
        default="output.png",
        maxlen=1024,
        subtype='FILE_NAME')

    bpy.types.Scene.spp = bpy.props.IntProperty(name = "Samples per pixel", description = "Set spp", 
                                                default = 100, min = 1, max = 9999)
    bpy.types.Scene.maxdepth = bpy.props.IntProperty(name = "Max depth", description = "Set max depth", 
                                                default = 10, min = 1, max = 9999)

    integrators = [("PT", "PT", "", 1), ("wavefrontPT", "wavefrontPT", "", 2)]
    bpy.types.Scene.integrators = bpy.props.EnumProperty(name = "Name", items=integrators , default="PT")

    lightsamplestrategy = [("uniform", "uniform", "", 1), ("power", "power", "", 2), ("bvh", "bvh", "", 3)]
    bpy.types.Scene.lightsamplestrategy = bpy.props.EnumProperty(name = "lightsamplestrategy", items=lightsamplestrategy , default="uniform")

    bpy.types.Scene.environmentmapscale = bpy.props.FloatProperty(name = "Env. map scale", description = "Env. map scale", default = 1, min = 0.001, max = 9999)
    
    bpy.types.Scene.resolution_x = bpy.props.IntProperty(name = "X", description = "Resolution x", default = 768, min = 1, max = 9999)
    bpy.types.Scene.resolution_y = bpy.props.IntProperty(name = "Y", description = "Resolution y", default = 768, min = 1, max = 9999)

    bpy.types.Scene.lensradius = bpy.props.FloatProperty(name = "Lens radius", description = "Lens radius", default = 0, min = 0.001, max = 9999)
    
    bpy.types.Scene.batch_frame_start = bpy.props.IntProperty(name = "Frame start", description = "Frame start", 
                                                            default = 1, min = 1, max = 9999999)
    bpy.types.Scene.batch_frame_end = bpy.props.IntProperty(name = "Frame end", description = "Frame end", 
                                                            default = 1, min = 1, max = 9999999)

    bpy.types.Scene.rr_threshold = bpy.props.FloatProperty(name = "Threshold", description = "Threshold", default = 1.0, min = 0.001, max = 9999)

    filterTypes = [("box", "box", "", 1), ("gaussian", "gaussian", "", 2), ("sinc", "sinc", "", 4),("triangle", "triangle", "", 5)]
    bpy.types.Scene.filterType = bpy.props.EnumProperty(name = "filterType", items=filterTypes , default="triangle")
    bpy.types.Scene.filter_x_width = bpy.props.FloatProperty(name = "x", description = "x", default = 0.5, min = 0.0, max = 999)
    bpy.types.Scene.filter_y_width = bpy.props.FloatProperty(name = "y", description = "y", default = 0.5, min = 0.001, max = 999)
    bpy.types.Scene.filter_tau = bpy.props.FloatProperty(name = "tau", description = "tau", default = 3.0, min = 0.001, max = 999)
    bpy.types.Scene.filter_b = bpy.props.FloatProperty(name = "b", description = "b", default = 3.0, min = 0.0, max = 999)
    bpy.types.Scene.filter_c = bpy.props.FloatProperty(name = "c", description = "c", default = 3.0, min = 0.0, max = 999)
    bpy.types.Scene.filter_alpha = bpy.props.FloatProperty(name = "alpha", description = "alpha", default = 2.0, min = 0.0, max = 999)

    samplers = [("HaltonSampler", "HaltonSampler", "", 1), ("PCGSampler", "PCGSampler", "", 7)]
    bpy.types.Scene.sampler = bpy.props.EnumProperty(name = "Sampler", items=samplers , default="PCGSampler")
    bpy.types.Scene.samplepixelcenter = bpy.props.BoolProperty(name="sample pixel center", description="sample pixel center", default = False)
    bpy.types.Scene.dimension = bpy.props.IntProperty(name = "dimension", description = "dimension", default = 4, min = 0, max = 9999999)
    bpy.types.Scene.jitter = bpy.props.BoolProperty(name="jitter", description="jitter", default = True)
    bpy.types.Scene.xsamples = bpy.props.IntProperty(name = "xsamples", description = "xsamples", default = 4, min = 0, max = 9999999)
    bpy.types.Scene.ysamples = bpy.props.IntProperty(name = "ysamples", description = "ysamples", default = 4, min = 0, max = 9999999)