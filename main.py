import cv2 as cv
import json
from utils.motion_camera import MotionCamera

# Opening JSON file
with open('config.json', 'r') as file:
    cameras_json = json.load(file)

cameras:list[MotionCamera] = []

kwargs = cameras_json.copy() 
del kwargs['cameras']
del kwargs['X11']
kwargs = {
    'segment_size': 5,
    'segment_name': '{}-segment',
    'scale_factor': 0.5,
    'retry_interval': 10,
    'debug': False,
    'min_confidence': 0.5,
    'realtime': False,
    'detect_nth_frame': 5,
    **kwargs,
}

for camera in cameras_json['cameras']:
    new_kwargs = {
        **kwargs,
        'password': camera['password'],
        'mac': camera['mac'],
        'camera_name': camera['name'],
        'segment_path': camera['folder'],
    }
    motion_camera = MotionCamera(
        **new_kwargs,
    )

    cameras.append(motion_camera)

while True:
    for camera in cameras:
        try:
            if cameras_json['X11'] == True:
                frame = camera.loop_detection()
                if frame is not None:
                    cv.imshow(camera.camera_name, frame)

                if cv.waitKey(1) == ord('q'):
                    break
            else:
                camera.loop_detection()
        except KeyboardInterrupt:
            break
    else:
        continue
    break


for camera in cameras:
    camera.release()

if cameras_json['X11'] == True:
    cv.destroyAllWindows()

# DONE - diminuir a qualidade para economizar espaço
# DONE - gravar continuamente pequenos segmentos de vídeo
# DONE - detectar movimento
# DONE - remover os segmentos em que não há nenhum movimento


# DONE - generalizar o código para lidar com mais de 1 camera
# DONE - colocar as informações das cameras em um arquivo toml/json/yaml
# DONE - encontrar o ip da camera a partir do mac address
# DONE - criar um intervalo para reconectar a camera

# DONE - enviar os segmentos para uma conta do google drive
# TODO - procurar uma forma de controlar os motores da camera através do python-onvif
# TODO - guardar todos os dados de um certo intervalo de tempo e só processar os dados (remover os segmentos sem movimento) depois de um tempo


