CONTINUE = True

# sampling config

NUM_SENSORS = 100
NUM_CALIBRATION = 9
NUM_OBJ_SAMPLES = 10000

OBJ_SIZE_MIN = 0.01
OBJ_SIZE_MAX = 0.05

X_MIN = -0.007
X_MAX = 0.007

Y_MIN = -0.007
Y_MAX = 0.007

CALIB_DEPTH_MIN = 0.0014
CALIB_DEPTH_MAX = 0.0018

OBJ_DEPTH_MIN = 0.0006
OBJ_DEPTH_MAX = 0.0018

# sensor parameters config

FOV_MIN = 20
FOV_MAX = 60

LENGTH_MIN = 0.0075
LENGTH_MAX = 0.0125

SMOOTHNESS_MIN = 15
SMOOTHNESS_MAX = 100

ROUGH_MIN = 0.4
ROUGH_MAX = 1.0

SCALE_MIN = 0.25
SCALE_MAX = 1

RED_STR_MIN = 40.0
RED_STR_MAX = 100.0

RED_COL_MIN = [0.9, 0.0, 0.0]
RED_COL_MAX = [1.0, 0.05, 0.05]

GREEN_STR_MIN = 80.0
GREEN_STR_MAX = 120.0

GREEN_COL_MIN = [0.0, 0.9, 0.0]
GREEN_COL_MAX = [0.05, 1.0, 0.05]

BLUE_STR_MIN = 70.0
BLUE_STR_MAX = 100.0

BLUE_COL_MIN = [0.0, 0.0, 0.9]
BLUE_COL_MAX = [0.05, 0.05, 1.0]

import bpy
from random import uniform as ru
from math import pi, tan
import os
import shutil
import sys
import numpy as np
import random
from mathutils import Euler

# moves object to specified location and depth
# move is applied to the lowest point of object
# orientation of the object is considered

# object: string object file name
# location: tuple (x,y,z), resonable x,y from -0.008 to 0.008, z upto 0.003
# rotation: (x, y, x) in radians

def move_object(object, location, rotation) -> None:
    bpy.data.objects[object].rotation_euler = rotation
    bpy.context.scene.frame_set(0)
    
    glbl_co = bpy.data.objects[object].location
    low_co = find_lowest(object)
    
    x = glbl_co[0] - low_co[0] + location[0]
    y = glbl_co[1] - low_co[1] + location[1]
    z = glbl_co[2] - low_co[2] - location[2]
    bpy.data.objects[object].location = (x, y, z)
    
    bpy.data.objects[object].hide_render = True
    bpy.data.objects['GelSurface'].modifiers["Shrinkwrap"].target = bpy.data.objects[object]
    
# locates the lowest z value of the object in world coordinates
# orientation of the object is considered

# object: string object file name

def find_lowest(object) -> float:
    obj = bpy.data.objects[object]
    mw = obj.matrix_world
    glbl_co = [ mw @ v.co for v in obj.data.vertices ]
    minZ = min( [ co.z for co in glbl_co ] )
    
    lowest = []
    for v in obj.data.vertices:
        if (mw @ v.co).z == minZ: lowest.append(mw @ v.co)
    return random.choice(lowest)

# changes color & strength of emittor surface

# emittor: string material file name
# color: tuple (r,g,b,a)
# strength: float 0.0-100.0

def set_emittor(emittor, strength, color) -> None:
    emission_node = bpy.data.materials[emittor].node_tree.nodes['Emission']
    
    emission_node.inputs['Color'].default_value = color
    emission_node.inputs['Strength'].default_value =  strength

# sets smootheness of gel (emulating thickness/softness)

# val: int, 1-120 for resonable results

def set_smoothness(val) -> None:
    bpy.data.objects['GelSurface'].modifiers['CorrectiveSmooth'].iterations = val
    bpy.data.objects['GelSurface'].modifiers["Shrinkwrap"].offset = 1e-03 * (val*val)/50000
    
# sets perpendicular length of lights to the gel surface

# val: int, 0.2-1 for resonable results

def set_scale(val) -> None:
    co_z = -0.0065+0.0011/val

    bpy.data.objects['LightSurfaceTop'].scale[1] = val
    bpy.data.objects['LightSurfaceBottom'].scale[1] = val
    bpy.data.objects['LightSurfaceLeft'].scale[1] = val
    bpy.data.objects['LightSurfaceRight'].scale[1] = val

    bpy.data.objects['LightSurfaceTop'].location[2] = co_z
    bpy.data.objects['LightSurfaceBottom'].location[2] = co_z
    bpy.data.objects['LightSurfaceLeft'].location[2] = co_z
    bpy.data.objects['LightSurfaceRight'].location[2] = co_z
    
# sets light type between point source and long type

def set_light_type(type) -> None:
    if type == 'point':
        bpy.data.objects['LightSurfaceTop'].scale[0] = 0.1
        bpy.data.objects['LightSurfaceBottom'].scale[0] = 0.1
        bpy.data.objects['LightSurfaceLeft'].scale[2] = 0.125
        bpy.data.objects['LightSurfaceRight'].scale[2] = 0.125
    if type == 'long':
        bpy.data.objects['LightSurfaceTop'].scale[0] = 1
        bpy.data.objects['LightSurfaceBottom'].scale[0] = 1
        bpy.data.objects['LightSurfaceLeft'].scale[2] = 1
        bpy.data.objects['LightSurfaceRight'].scale[2] = 1
        
# sets fov and sensing range of camera and rescales depth map parameters

def set_cam(fov, length) -> None:
    height = (length/tan((fov/360)*pi))
    bpy.data.objects['Camera'].location[2] = -height
    bpy.data.objects['Camera'].data.angle = (fov/180)*pi
    
    bpy.data.scenes["Scene"].node_tree.nodes["Map Range"].inputs[2].default_value = height
    bpy.data.scenes["Scene"].node_tree.nodes["Map Range"].inputs[1].default_value = height-0.002

    
# class to store sensor variables and apply settings
class create_sensor():
    def __init__(self, 
                 randomize = True,
                 smoothness = None,
                 top_str = None,
                 top_col = (None, None, None, 1),
                 bot_str = None,
                 bot_col = (None, None, None, 1),
                 lef_str = None,
                 lef_col = (None, None, None, 1),
                 rig_str = None,
                 rig_col = (None, None, None, 1),
                 scale = None,
                 light_type = None,
                 angle = None,
                 fov = None,
                 roughness = None,
                 length = None,
                 write_dir = None,
                 read_dir = None):
        
        self.smoothness = smoothness
        self.scale = scale
        self.light_type = light_type
        self.angle = angle
        self.emittors = [[top_str, top_col], [bot_str, bot_col], [lef_str, lef_col], [rig_str, rig_col]]
        self.fov = fov
        self.roughness = roughness
        self.length = length

        if read_dir != None:
            f = open(read_dir, 'r')
            content = f.readlines()

            self.smoothness = int(content[0])
            self.scale = float(content[1])
            self.light_type = content[2].strip('\n')
            self.angle = content[3].strip('\n')
            self.emittors[0][0] = float(content[4])
            self.emittors[0][1] = (float(content[5]), float(content[6]), float(content[7]), 1)
            self.emittors[1][0] = float(content[8])
            self.emittors[1][1] = (float(content[9]), float(content[10]), float(content[11]), 1)
            self.emittors[2][0] = float(content[12])
            self.emittors[2][1] = (float(content[13]), float(content[14]), float(content[15]), 1)
            self.emittors[3][0] = float(content[16])
            self.emittors[3][1] = (float(content[17]), float(content[18]), float(content[19]), 1)
            self.fov = float(content[20])
            self.roughness = float(content[21])
            self.length = float(content[22])
            
        else:        
            if randomize == True: self.randomize()

            if write_dir != None:
                f = open(write_dir,"w+")
                f.write(f'{self.smoothness}\n')
                f.write(f'{self.scale}\n')
                f.write(f'{self.light_type}\n')
                f.write(f'{self.angle}\n')
                f.write(f'{self.emittors[0][0]}\n')
                f.write(f'{self.emittors[0][1][0]}\n')
                f.write(f'{self.emittors[0][1][1]}\n')
                f.write(f'{self.emittors[0][1][2]}\n')
                f.write(f'{self.emittors[1][0]}\n')
                f.write(f'{self.emittors[1][1][0]}\n')
                f.write(f'{self.emittors[1][1][1]}\n')
                f.write(f'{self.emittors[1][1][2]}\n')
                f.write(f'{self.emittors[2][0]}\n')
                f.write(f'{self.emittors[2][1][0]}\n')
                f.write(f'{self.emittors[2][1][1]}\n')
                f.write(f'{self.emittors[2][1][2]}\n')
                f.write(f'{self.emittors[3][0]}\n')
                f.write(f'{self.emittors[3][1][0]}\n')
                f.write(f'{self.emittors[3][1][1]}\n')
                f.write(f'{self.emittors[3][1][2]}\n')
                f.write(f'{self.fov}\n')
                f.write(f'{self.roughness}\n')
                f.write(f'{self.length}\n')
                f.close()

    def randomize(self):
        self.smoothness = random.randrange(SMOOTHNESS_MIN, SMOOTHNESS_MAX)
        self.scale = ru(SCALE_MIN, SCALE_MAX)
        self.fov = ru(FOV_MIN, FOV_MAX)
        self.roughness = ru(ROUGH_MIN, ROUGH_MAX)
        self.length = ru(LENGTH_MIN, LENGTH_MAX)
        
        if random.random() < 0.35: self.angle = 'diag'
        else: self.angle = 'str'
        
        if random.random() < 0.35: self.light_type = 'point'
        else: self.light_type = 'long'

        emittors = ['RED','GREEN','BLUE','BLOCK']
        emittors = random.sample(emittors, 4)

        for idx, emittor in enumerate(emittors):
            if emittor == 'RED':
                self.emittors[idx][0] =  ru(RED_STR_MIN, RED_STR_MAX)
                self.emittors[idx][1] =  (ru(RED_COL_MIN[0], RED_COL_MAX[0]), 
                                          ru(RED_COL_MIN[1], RED_COL_MAX[1]), 
                                          ru(RED_COL_MIN[2], RED_COL_MAX[2]), 1)
            if emittor == 'GREEN':
                self.emittors[idx][0] =  ru(GREEN_STR_MIN, GREEN_STR_MAX)
                self.emittors[idx][1] =  (ru(GREEN_COL_MIN[0], GREEN_COL_MAX[0]), 
                                          ru(GREEN_COL_MIN[1], GREEN_COL_MAX[1]), 
                                          ru(GREEN_COL_MIN[2], GREEN_COL_MAX[2]), 1)
            if emittor == 'BLUE':
                self.emittors[idx][0] =  ru(BLUE_STR_MIN, BLUE_STR_MAX)
                self.emittors[idx][1] =  (ru(BLUE_COL_MIN[0], BLUE_COL_MAX[0]), 
                                          ru(BLUE_COL_MIN[1], BLUE_COL_MAX[1]), 
                                          ru(BLUE_COL_MIN[2], BLUE_COL_MAX[2]), 1)
            if emittor == 'BLOCK':
                self.emittors[idx][0] =  0
                self.emittors[idx][1] =  (0, 0, 0, 1)

    def apply(self):
        set_smoothness(self.smoothness)
        set_scale(self.scale)
        set_light_type(self.light_type)
        set_cam(self.fov, self.length)
        bpy.data.materials["aluminum-specular-mat"].node_tree.nodes["Glossy BSDF"].inputs[1].default_value = self.roughness
        
        bpy.context.scene.frame_set(0)

        rot_mat = Euler((0, 0, 0)).to_matrix().to_4x4()        
        if bpy.data.objects['LightSurfaceTop'].rotation_euler[0] > 0: 
            if self.angle == 'diag': rot_mat = Euler((0, 0, pi/4)).to_matrix().to_4x4()
        else: 
            if self.angle == 'str': rot_mat = Euler((0, 0, -pi/4)).to_matrix().to_4x4()
            
        bpy.data.objects['LightSurfaceTop'].matrix_world = rot_mat @ bpy.data.objects['LightSurfaceTop'].matrix_world
        bpy.data.objects['LightSurfaceBottom'].matrix_world = rot_mat @ bpy.data.objects['LightSurfaceBottom'].matrix_world
        bpy.data.objects['LightSurfaceLeft'].matrix_world = rot_mat @ bpy.data.objects['LightSurfaceLeft'].matrix_world
        bpy.data.objects['LightSurfaceRight'].matrix_world = rot_mat @ bpy.data.objects['LightSurfaceRight'].matrix_world
        
        if self.light_type == 'long': 
            set_emittor('TopEmittor', self.emittors[0][0], self.emittors[0][1])
            set_emittor('BottomEmittor', self.emittors[1][0], self.emittors[1][1])
            set_emittor('LeftEmittor', self.emittors[2][0], self.emittors[2][1])
            set_emittor('RightEmittor', self.emittors[3][0], self.emittors[3][1])
        else:
            set_emittor('TopEmittor', self.emittors[0][0]*5, self.emittors[0][1])
            set_emittor('BottomEmittor', self.emittors[1][0]*5, self.emittors[1][1])
            set_emittor('LeftEmittor', self.emittors[2][0]*5, self.emittors[2][1])
            set_emittor('RightEmittor', self.emittors[3][0]*5, self.emittors[3][1])

# get depth map from range 0 - 3 mm
# messes up current sensor values

def get_depth(dir) -> None:
    # apply orthogonal camera standardizations and remove obstructions
    # bpy.data.objects["InterfaceSurface"].hide_render = True
    # bpy.data.objects["EpoxySurface"].hide_render = True
    
    z = bpy.data.images['Viewer Node']
    w, h = z.size
    dmap = np.array(z.pixels[:], dtype=np.float32) # convert to numpy array
    dmap = np.reshape(dmap, (h, w, 4))[:,:,0]
    dmap = np.rot90(dmap, k=2)
    dmap = np.fliplr(dmap)
    dmap = 1 - dmap
    np.save(dir, dmap)
    
    # undo changes
    # bpy.data.objects["InterfaceSurface"].hide_render = False
    # bpy.data.objects["EpoxySurface"].hide_render = False

dir = os.path.dirname(bpy.data.filepath)
sys.path.append(dir)
render_dir = os.environ.get('GELSIGHT_RENDER_DIR', os.path.join(dir, 'renders'))
mesh_dir = os.path.join(dir, 'meshes')

if __name__ == '__main__':

    sensors = []
    if not CONTINUE:
        # create file directory to store renders
        if os.path.exists(render_dir): shutil.rmtree(render_dir)
        os.mkdir(render_dir)
    
        # generate different sensors and paths
        
        for idx in range(NUM_SENSORS):
            idx_formatted = '{0:04}'.format(idx)
            sensor_dir = os.path.join(render_dir, f'sensor_{idx_formatted}')
            os.mkdir(os.path.join(sensor_dir))
            os.mkdir(os.path.join(sensor_dir, 'calibration'))
            os.mkdir(os.path.join(sensor_dir, 'samples'))
            os.mkdir(os.path.join(sensor_dir, 'raw_data'))

            sensor_txt_dir = os.path.join(sensor_dir, 'parameters.txt')
            sensors.append(create_sensor(write_dir=sensor_txt_dir))
    
    else: 
        sensor_dirs = [sensor_dir for sensor_dir in os.listdir(render_dir) if 'sensor' in sensor_dir]
        sensor_dirs.sort()

        for sensor_dir in sensor_dirs:
            sensor_txt_dir = os.path.join(render_dir, sensor_dir, 'parameters.txt')
            sensors.append(create_sensor(read_dir=sensor_txt_dir))

    # generate calibration for all sensors
    calibration_objects = ['IndenterSurface', 'Cube']
    for sensor_idx, sensor in enumerate(sensors):
        sensor_idx_formatted = '{0:04}'.format(sensor_idx)
        sensor_dir = os.path.join(render_dir, f'sensor_{sensor_idx_formatted}')

        if CONTINUE:
            if len(os.listdir(os.path.join(sensor_dir, 'calibration'))) < (NUM_CALIBRATION * len(calibration_objects) + 1):
                shutil.rmtree(os.path.join(sensor_dir, 'calibration'))
                os.mkdir(os.path.join(sensor_dir, 'calibration'))
            else: continue

        sensor.apply()
        
        overall_calib_idx = 0
        calib_idx_formatted = '{0:04}'.format(overall_calib_idx)
        bpy.context.scene.render.filepath = os.path.join(sensor_dir, 'calibration', calib_idx_formatted)
        move_object('IndenterSurface', (0,0,-1), (0,0,0))
        bpy.context.scene.frame_set(0)
        bpy.ops.render.render(write_still=True)
        overall_calib_idx += 1
        
        qt = (sensor.length*2)/3
        
        CALIB_X = [qt, 0, -qt, qt, 0, -qt, qt, 0, -qt]
        CALIB_Y = [qt, qt, qt, 0, 0, 0, -qt, -qt, -qt]
        
        for obj_idx, calib_obj in enumerate(calibration_objects):
            for calib_idx in range(NUM_CALIBRATION):
                calib_idx_formatted = '{0:04}'.format(overall_calib_idx)
                bpy.context.scene.render.filepath = os.path.join(sensor_dir, 'calibration', calib_idx_formatted)
                
                x = ru(-0.001, 0.001) + CALIB_X[calib_idx]
                y = ru(-0.001, 0.001) + CALIB_Y[calib_idx]

                z = ru(CALIB_DEPTH_MIN, CALIB_DEPTH_MAX)
                
                a_x = pi/4
                a_y = pi/4
                a_z = ru(0, 2*pi)
                
                move_object(calib_obj, (x,y,z), (a_x,a_y,a_z))
                
                bpy.context.scene.frame_set(0)
                bpy.ops.render.render(write_still=True)
                
                overall_calib_idx += 1

    # import all meshes into blender
    obj_dir = os.listdir(mesh_dir)
    obj_dir.sort()
    for obj_idx, obj in enumerate(obj_dir):
        bpy.ops.wm.obj_import(filepath=os.path.join(mesh_dir, obj), directory=mesh_dir, files=[{"name":object, "name":obj}])
        obj_dir[obj_idx] = obj.replace('.obj','')
        bpy.data.objects[obj_dir[obj_idx]].hide_render = True

    # remove incomplete render batch
    if CONTINUE:
        sensor_idx_formatted = '{0:04}'.format(0)
        first_sensor_samples = os.listdir(os.path.join(render_dir, f'sensor_{sensor_idx_formatted}', 'samples'))
        sensor_idx_formatted = '{0:04}'.format(NUM_SENSORS-1)
        last_sensor_samples = os.listdir(os.path.join(render_dir, f'sensor_{sensor_idx_formatted}', 'samples'))

        overall_idx = min(len(first_sensor_samples), len(last_sensor_samples))
        sample_idx_formatted = '{0:04}'.format(overall_idx)

        if len(first_sensor_samples) != len(last_sensor_samples):
            for sensor_idx, sensor in enumerate(sensors):
                sensor_idx_formatted = '{0:04}'.format(sensor_idx)
                sample_dir = os.path.join(render_dir, f'sensor_{sensor_idx_formatted}', 'samples', f'{sample_idx_formatted}.png')
                dmap_dir = os.path.join(render_dir, f'sensor_{sensor_idx_formatted}', 'raw_data', f'{sample_idx_formatted}.npy')
                if os.path.exists(sample_dir): os.remove(sample_dir)
                if os.path.exists(dmap_dir): os.remove(dmap_dir)

    else: overall_idx = 0

    # generate samples for all sensors
    for sample_idx in range(overall_idx, NUM_OBJ_SAMPLES):
        # select and scale random object
        obj = random.choice(obj_dir)
        scale = max(bpy.data.objects[obj].dimensions) / ru(OBJ_SIZE_MIN, OBJ_SIZE_MAX)
        cur_scale = bpy.data.objects[obj].scale
        bpy.data.objects[obj].scale = (cur_scale[0] / scale, cur_scale[1] / scale, cur_scale[2] / scale)

        x = ru(X_MIN, X_MAX)
        y = ru(Y_MIN, Y_MAX)
        z = ru(OBJ_DEPTH_MIN, OBJ_DEPTH_MAX)

        a_x = ru(0, 2*pi)
        a_y = ru(0, 2*pi)
        a_z = ru(0, 2*pi)
        
        move_object(obj, (x,y,z), (a_x,a_y,a_z))
        
        overall_idx_formatted = '{0:04}'.format(overall_idx)
    
        for sensor_idx, sensor in enumerate(sensors):
            sensor_idx_formatted = '{0:04}'.format(sensor_idx)
            sensor_dir = os.path.join(render_dir, f'sensor_{sensor_idx_formatted}')
            sensor.apply()
            
            bpy.context.scene.render.filepath = os.path.join(sensor_dir, 'samples', overall_idx_formatted)

            bpy.context.scene.frame_set(0)
            bpy.ops.render.render(write_still=True)
            get_depth(os.path.join(sensor_dir, 'raw_data', f'{overall_idx_formatted}.npy'))

        overall_idx += 1

    # remove meshes from blender
    for obj in obj_dir:
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[obj].select_set(True)
        bpy.ops.object.delete() 

#sensor = create_sensor()
#sensor.apply()
#set_scale(0.25)
#set_fov(60)

#bpy.ops.transform.resize(value=(1, 1, 1/CUR_SCALE))
#bpy.ops.transform.translate(value=(0, 0, -1/(CUR_SCALE*1000)))

#rot_mat = Euler((0, 0, -pi/4)).to_matrix().to_4x4()
#bpy.data.objects['LightSurfaceTop'].matrix_world = rot_mat @ bpy.data.objects['LightSurfaceTop'].matrix_world
#bpy.data.objects['LightSurfaceBottom'].matrix_world = rot_mat @ bpy.data.objects['LightSurfaceBottom'].matrix_world
#bpy.data.objects['LightSurfaceLeft'].matrix_world = rot_mat @ bpy.data.objects['LightSurfaceLeft'].matrix_world
#bpy.data.objects['LightSurfaceRight'].matrix_world = rot_mat @ bpy.data.objects['LightSurfaceRight'].matrix_world

#set_camera(0.015)
#set_smoothness(10)

#x = ru(X_MIN, X_MAX)
#y = ru(Y_MIN, Y_MAX)
#z = ru(0.0014, 0.0017)

#a_x = pi/4
#a_y = pi/4
#a_z = ru(0, 2*pi)

#move_object('Cube', (x,y,z), (a_x,a_y,a_z))
#get_depth(os.path.join(render_dir, 'depth.txt'))



