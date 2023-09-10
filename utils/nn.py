import cv2
from rich import print

def get_classLabels():
    with open('models/labels.txt', 'rt') as f:
        classLabels = f.read().rstrip('\n').split('\n')
    return classLabels

def load_nn():
    #Initialize Objects and corresponding colors which the model can detect

    #Loading Caffe Model
    print('[blue][Status] Loading Model...')
    config_file = 'models/ssd_mobilenet.pbtxt'
    frozen_model = 'models/ssd_mobilenet.pb'
    nn = cv2.dnn_DetectionModel(frozen_model, config_file)


    nn.setInputSize(320,320)
    nn.setInputScale(1.0/127.5)
    nn.setInputMean((127.5,127.5,127.5))
    nn.setInputSwapRB(True)
    return nn
