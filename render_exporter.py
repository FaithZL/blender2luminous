import bpy
import bmesh
import os
import math
from math import *
import mathutils
from mathutils import Vector
import shutil
import struct
import json

from importlib import reload

if __name__ == "__main__":
    from blender2luminous import material_nodes
    reload(material_nodes)
else:
    from . import material_nodes

#render engine custom begin
class LuminousRenderEngine(bpy.types.RenderEngine):
    bl_idname = 'Luminous_Renderer'
    bl_label = 'Luminous_Renderer'
    bl_use_preview = False
    bl_use_material = True
    bl_use_shading_nodes = False
    bl_use_shading_nodes_custom = False
    bl_use_texture_preview = True
    bl_use_texture = True
    
    def render(self, scene):
        self.report({'ERROR'}, 'Use export function in PBRT panel.')
        
from bl_ui import properties_render
from bl_ui import properties_material
for member in dir(properties_render):
    subclass = getattr(properties_render, member)
    try:
        subclass.COMPAT_ENGINES.add('Luminous_Renderer')
    except:
        pass

for member in dir(properties_material):
    subclass = getattr(properties_material, member)
    try:
        subclass.COMPAT_ENGINES.add('Luminous_Renderer')
    except:
        pass

bpy.utils.register_class(LuminousRenderEngine)


def create_directory_if_needed(directory_filepath, force=False):
    if not os.path.exists(directory_filepath):
        os.makedirs(directory_filepath)
    elif force:
        os.rmdir(directory_filepath)
        os.makedirs(directory_filepath)

def get_filename(filepath):
    folderpath, filename = os.path.split(filepath)
    return filename

def matrixToList(matrix4x4):
    items = []
    for row in matrix4x4.row:
        items.extend(row)
    return items

def getTextureInSlotName(textureSlotParam):
    srcfile = textureSlotParam
    head, tail = os.path.split(srcfile)
    print("File name is :")
    print(tail)

    return tail

def exportTextureInSlotNew(textureSlotParam,isFloatTexture):
    srcfile = bpy.path.abspath(textureSlotParam)
    texturefilename = getTextureInSlotName(srcfile)


    dstdir = bpy.path.abspath(bpy.data.scenes[0].exportpath + 'textures/' + texturefilename)
    print("os.path.dirname...")
    print(os.path.dirname(srcfile))
    print("\n")
    print("srcfile: ")
    print(srcfile)
    print("\n")
    print("dstdir: ")
    print(dstdir)
    print("\n")
    print("File name is :")
    print(texturefilename)
    print("Copying texture from source directory to destination directory.")
    # shutil.copyfile(srcfile, dstdir)
    return ''

def export_texture_from_input (pbrt_file, inputSlot, mat, isFloatTexture):
    textureName = ""
    links = inputSlot.links
    print('Number of links: ')
    print(len(links))
    for x in inputSlot.links:
        textureName = x.from_node.image.name
        exportTextureInSlotNew(x.from_node.image.filepath,isFloatTexture)
    return textureName

def create_constant_tex(name, val):
    return {
        "type" : "ConstantTexture",
        "name" : name,
        "param" : {
            "val": val,
			"color_space": "SRGB"
        }
    }

def export_matte(scene_json, mat, mat_name):
    print("\nexport matte start !")

    Kd = [mat.Kd[0],mat.Kd[1],mat.Kd[2],mat.Kd[3]]

    tex_data = create_constant_tex(mat_name + "_constant", Kd)

    add_textures(scene_json, tex_data)

    tab = {
        "type": "MatteMaterial",
        "name": mat_name,
        "param": {
            "diffuse": tex_data["name"]
        }
    }
    add_material(scene_json, tab)

    print("export matte end !")

def export_material(scene, scene_json, object, slot_idx):
    mat = object.material_slots[slot_idx].material 
    if not mat or not mat.use_nodes:
        return
    
    def is_custom_node(node):
        return isinstance(node, material_nodes.MyCustomTreeNode)

    print('\nMat name: ', mat.name)
    for node in mat.node_tree.nodes:
        if not is_custom_node(node):
            continue
        if node.bl_idname == 'CustomNodeTypeMatte':
            export_matte(scene_json, node, mat.name)
            

def export_meshes(scene, scene_json):
    obj_directory_path = bpy.path.abspath(scene.exportpath + 'meshes')
    obj_filepath =  obj_directory_path + '/meshes.obj'
    # print(f'[info] export mesh to {obj_filepath}')
    create_directory_if_needed(obj_directory_path)

    def skip(object):
        return object is None or object.type == 'CAMERA' or object.type != 'MESH'

    for object in scene.objects:
        if skip(object):
            continue

        print('exporting object:' , object.name)
        bpy.context.view_layer.update()
        object.data.update()
        dg = bpy.context.evaluated_depsgraph_get()
        eval_obj = object.evaluated_get(dg)
        mesh = eval_obj.to_mesh()

        for i in range(len(object.material_slots)):
            export_material(scene, scene_json, object, i)
            

    return

    bpy.ops.export_scene.obj(filepath=obj_filepath, use_mesh_modifiers=True, use_normals=True, use_uvs=True, use_materials=True, path_mode='COPY', use_vertex_groups=True)
    scene_json['shapes'] = [{
        'name': 'mesh',
        'type': 'model',
        'param': {
            'fn': 'meshes/meshes.obj',
            'smooth': False,
            'swap_handed': True,
            'subdiv_level': 0,
            'transform': {
                'type': 'trs',
                'param': {
                    't': [0, 0, 0],
                    'r': [0, 0, 0, 0],
                    's': [1, 1, 1]
                }
            }
        }
    }]

def export_environmentmap(scene, scene_json):
    if scene.environmentmaptpath == '':
        print('export: environmentmap path is empyt')
        return
    environmentMapFileName = get_filename(scene.environmentmaptpath)
    srcfile = bpy.path.abspath(scene.environmentmaptpath)
    dstdir = bpy.path.abspath(scene.exportpath + 'textures')
    dstfile = dstdir + '/' + environmentMapFileName
    create_directory_if_needed(dstdir)
    shutil.copyfile(srcfile, dstfile)
    environmentmapscaleValue = scene.environmentmapscale
    environment_texture = {
        'name': 'envmap',
        'type': 'ImageTexture',
        'param': {
            'fn': 'textures/' + environmentMapFileName,
            'color_space': 'LINEAR'
        }
    }
    environment_light = {
        'type': 'Envmap',
        'param': {
            'transform' : {
                'type' : 'yaw_pitch',
                'param' : {
                    'yaw' : 0,
                    'pitch': 0,
                    'position': [0,0,0]
                }
            },
            'scale': [environmentmapscaleValue, environmentmapscaleValue, environmentmapscaleValue],
            'key' : 'envmap'
        }
    }
    if 'textures' in scene_json:
        scene_json['textures'].append(environment_texture)
    else:
        scene_json['textures'] = [environment_texture]
    if 'lights' in scene_json:
        scene_json['lights'].append(environment_light)
    else:
        scene_json['lights'] = [environment_light]

def export_point_lights(scene, scene_json):
    lights = []
    # 不能用bpy.data.objects[bpy.data.lights[0].name]这种形式来获取对象，name不是key，有可能两者不一致，如之前碰到的name=面光，key=g面光
    # for light_data in bpy.data.lights:
    #     light_obj = bpy.data.objects[light_data.name]
    for obj in scene.objects:
        if obj.type != 'LIGHT' or obj.data.type != 'POINT':
            continue
        light_obj = obj
        light_data = obj.data
        light = {
            'type': 'PointLight',
            'param': {
                'transform': {
                    'type': 'matrix4x4',
                    'param': {
                        'matrix4x4':  matrixToList(light_obj.matrix_world)
                    }
                },
                'color': list(light_data.color)
            }
        }
        lights.append(light)

    if 'lights' in scene_json:
        scene_json['lights'].extend(lights)
    else:
        scene_json['lights'] = lights

def export_area_lights(scene, scene_json):
    lights = []
    allow_light_shapes = ['RECTANGLE', 'SQUARE']
    for obj in scene.objects:
        if obj.type != 'LIGHT' or obj.data.type != 'AREA' or obj.data.shape not in allow_light_shapes:
            continue
        light_obj = obj
        light_data = obj.data

        if light_data.shape == 'SQUARE':
            width = light_data.size
            height = light_data.size
        else:
            width = light_data.size
            height = light_data.size_y

        light = {
            'name': 'light_' + light_obj.name,
            'type': 'quad',
            'param': {
                'width': width,
                'height': height,
                'emission': list(light_data.color),
                'scale': 1,
                'transform': {
                    'type': 'matrix4x4',
                    'param': {
                        'matrix4x4':  matrixToList(light_obj.matrix_world)
                    }
                },
                'material': ''
            }
        }
        lights.append(light)

    if 'shapes' in scene_json:
        scene_json['shapes'].extend(lights)
    else:
        scene_json['shapes'] = lights

def export_camera(scene, scene_json):
    camera = {}
    camera_obj_blender = None
    camera_data_blender = None
    for camera_blender in bpy.data.cameras:
        if camera_blender.type == 'PERSP':
            camera_obj_blender = bpy.data.objects[camera_blender.name]
            camera_data_blender = camera_blender
            break
    if camera_obj_blender is None:
        print('[error]: no PERSP camera')
        return
    # scene.render.resolution_x是blender的渲染分辨率，把我们的渲染器跟blender的渲染器分开会好些
    resolution_x = scene.resolution_x
    resolution_y = scene.resolution_y
    print('render res: ', resolution_x , ' x ', resolution_y)
    ratio = scene.render.resolution_y / scene.render.resolution_x
    angle_rad = camera_data_blender.angle_y
    scene_json['camera'] = {
        'type': 'ThinLensCamera',
        'param': {
            'fov_y': 2.0 * math.atan ( ratio * math.tan( angle_rad / 2.0 )) * 180.0 / math.pi,
            'velocity': 20,
            'transform': {
                'type': 'matrix4x4',
                'param': {
                    'matrix4x4': matrixToList(camera_obj_blender.matrix_world)
                }
            },
            'film': {
                'param': {
                    'resolution': [resolution_x, resolution_y]
                }
            }
        }
    }

def export_integrator(scene, scene_json):
    scene_json['integrator'] = {
		'type' : scene.integrators,
		'param' : {
			'max_depth' : scene.maxdepth,
			'rr_threshold' : scene.rr_threshold
		}
	}

def export_light_sampler(scene, scene_json):
    scene_json['light_sampler'] = {
		'type': scene.light_sampler
	}

def export_sampler(scene, scene_json):
    scene_json['sampler'] = {
		'type' : scene.sampler,
		'param' : {
			'spp' : scene.spp
		}
	}

def export_filter(scene, scene_json):
    scene_json['filter'] = {
		'type' : scene.filterType,
		'param' : {
			'radius' : [scene.filter_x_width, scene.filter_y_width]
		}
	}

def export_render_output(scene, scene_json):
    scene_json['output'] = {
		'fn': scene.outputfilename,
		'frame_num' : scene.frame_num
    }

def export_scene(scene_json, filepath):
    with open(filepath, 'w') as outputfile:
        json.dump(scene_json, outputfile, indent=4)

def find_index(lst, key):
    for i, elm in enumerate(lst):
        if elm["name"] == key:
            return i
    return -1

def is_contain(lst, key):
    return find_index(lst, key) != -1


def create_texture(tex):
    ret = {}




def create_matte(mat, scene_json):
    ret = {}
    ret["type"] = "MatteMaterial"
    ret["name"] = mat.name
    ret["param"] = {
        "diffuse" : mat.Kd
    }
    return ret

def add_textures(scene_json, tex):
    index = find_index(scene_json["textures"], tex["name"])
    if index != -1:
        return index
    scene_json["textures"].append(tex)

def add_material(scene_json, mat):
    index = find_index(scene_json["materials"], mat["name"])
    if index != -1:
        return index
    scene_json["materials"].append(mat)


def export_luminous(filepath, scene):
    scene_json = {}

    scene_json["textures"] = []
    scene_json["materials"] = []

    export_meshes(scene, scene_json)
    export_environmentmap(scene, scene_json)
    export_point_lights(scene, scene_json)
    export_area_lights(scene, scene_json)
    export_camera(scene, scene_json)
    export_integrator(scene, scene_json)
    export_light_sampler(scene, scene_json)
    export_sampler(scene, scene_json)
    export_filter(scene, scene_json)
    export_render_output(scene, scene_json)

    export_scene(scene_json, bpy.path.abspath(filepath + '/scene.json'))
    
