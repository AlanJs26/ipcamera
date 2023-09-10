import cv2 as cv
from timeit import default_timer as timer
import os
from datetime import datetime
from rich import print as rprint
from utils.utils import FreshestFrame, DummyVideoWriter, find_ip_by_mac
from utils.nn import load_nn, get_classLabels

FONT_SCALE = 2
FONT = cv.FONT_HERSHEY_PLAIN

nn = load_nn()
classLabels = get_classLabels()

class MotionCamera:
    def __init__(
        self,
        mac,
        password,
        camera_name,
        segment_size=5,
        segment_name='{}-segment',
        segment_path='',
        scale_factor=0.5,
        retry_interval=10,
        debug=False,
        min_confidence=0.5,
        realtime=False,
        detect_nth_frame=5,
    ):
        self.debug = debug
        self.mac = mac
        self.password = password
        self.camera_name = camera_name
        self.realtime = realtime

        self.ip=''

        self.RETRY_INTERVAL=retry_interval

        self.SEGMENT_SIZE=segment_size
        self.SEGMENT_NAME=segment_name.format(camera_name)
        self.SEGMENT_PATH=os.path.expanduser(segment_path)

        self.MIN_CONFIDENCE = min_confidence

        self.DETECT_NTH_FRAME = detect_nth_frame

        self.SCALE_FACTOR=scale_factor

        self.result=DummyVideoWriter()

        self.segment_id=0
        self.prev_frame = None
        self.frame = None

        self.prev_file = ''
        self.elapsed = timer()
        self.elapsed_retry = timer()
        self.frame_count = 0
        self.should_keep_segment = False

        self.retry_count = 0

        self.setup()

    def log(self, string, color=''):
        if color:
            rprint(f'[{color}]\\[{self.camera_name}]: {string}')
        else:
            rprint(f'\\[{self.camera_name}]: {string}')

    def setup(self, is_retry=False):
        self.vcap, self.ready = self.setup_vcap()

        if not self.ready or not self.vcap or not self.vcap.isOpened():
            self.log(f'[ERROR] Cannot open video stream', 'red')
            self.ready = False
            return
        else:
            self.log(f'Opened video stream successfully', 'green')

        if not self.debug:
            os.makedirs(self.SEGMENT_PATH, exist_ok=True)

        frame_width = int(self.vcap.get(3))
        frame_height = int(self.vcap.get(4))

        size = (frame_width, frame_height)
        self.lowres_size = (int(size[0]*self.SCALE_FACTOR), int(size[1]*self.SCALE_FACTOR))

        if not is_retry: 
            self.result = self.new_segment()

    def setup_vcap(self):
        mac_dict = find_ip_by_mac()

        if self.mac not in mac_dict:
            self.log(f'[ERROR] Cannot find any ip matching the mac "{self.mac}"', 'red')
            return None, False

        ip_candidates = mac_dict[self.mac]
        vcap = None

        for ip in ip_candidates:
            vcap = cv.VideoCapture(self.get_url(ip, self.password))

            if vcap.isOpened():
                self.ip = ip
                break

        if not vcap:
            return None, False

        vcap.set(cv.CAP_PROP_BUFFERSIZE, 1)
        vcap.set(cv.CAP_PROP_FPS, 30)

        if self.realtime:
            return FreshestFrame(vcap), vcap.isOpened()
        else:
            return vcap, vcap.isOpened()

    def get_url(self, ip, password):
        return f'rtsp://admin:{password}@{ip}:554/onvif1'

    def new_segment(self):
        self.segment_id+=1
        date = datetime.now().strftime('%d_%m_%Y-%H_%M')
        new_name = f'{self.SEGMENT_NAME}{self.segment_id}-{date}.avi'

        file_path = os.path.join(self.SEGMENT_PATH, new_name)

        self.prev_file = file_path
         
        if self.debug:
            return DummyVideoWriter()
        else:
            return cv.VideoWriter(file_path, 
                                  cv.VideoWriter.fourcc(*'XVID'),
                                  10, self.lowres_size, False)

    def delete_prev_segment(self):
        if os.path.isfile(self.prev_file):
            os.remove(self.prev_file)
        self.segment_id-=1

    def should_reconnect(self):
        if not self.ready or not self.vcap:
            if self.retry_count == 0:
                self.release()
                self.retry_count += 1

            if timer() - self.elapsed_retry >= self.RETRY_INTERVAL:
                self.log(f'retrying connection... {self.retry_count}° try', 'yellow')
                self.retry_count += 1
                self.elapsed_retry = timer()
                self.setup(is_retry=True)

            return True

        ret, self.frame = self.vcap.read()

        if self.frame is None or not ret:
            return True
        return False

    def loop_detection(self):
        if self.should_reconnect() or self.frame is None:
            return
        self.frame_count+=1

        lowres_frame = cv.resize(self.frame, self.lowres_size, interpolation=cv.INTER_AREA)
        lowres_frame = cv.cvtColor(lowres_frame, cv.COLOR_BGR2GRAY)
        self.result.write(lowres_frame)

        if timer() - self.elapsed >= self.SEGMENT_SIZE:
            if not self.should_keep_segment:
                self.log(f'no motion: deleting {self.prev_file}', 'yellow')
                self.delete_prev_segment()
            else:
                self.log(f'saving {self.prev_file}')

            self.should_keep_segment=False
            self.result = self.new_segment()
            self.elapsed = timer()

        frame = self.frame

        if self.frame_count % self.DETECT_NTH_FRAME == 0:
            class_index, confidence, bbox = nn.detect(frame, confThreshold=self.MIN_CONFIDENCE)

            try:
                for index, conf, boxes in zip(class_index.flatten(), confidence.flatten(), bbox):
                    if classLabels[index-1] == 'person':
                        self.should_keep_segment = True

                    cv.rectangle(frame, boxes, (255,0,0), 2)
                    cv.putText(frame, classLabels[index-1], (boxes[0]+10, boxes[1]+40), FONT, fontScale=FONT_SCALE, color=(0,255,0), thickness=3)
            except:
                pass

        return frame

    def release(self):
        self.log('closing stream')
        if self.vcap:
            self.vcap.release()
        self.result.release()
        self.ready = False
        self.ip = ''
