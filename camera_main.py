import numpy as np
import cv2

from camera_application import Camera
from json_utils import JSONutils

import profilemeter_application

class FrameGrabber:
    def __init__(self):
        self.camera = Camera
        self.profilemeter = profilemeter_application # TODO!!
    
    def grab_from_device(self, device:bool = False) -> bytes:
        '''
        Frame grabber for both devices (camera and profilemeter)

        Args:
        device: False for camera, True for profilemeter

        Return:
        list with [nd.array(w, h, 3), nd.array(1)] for camera
        and [nd.array(w, h, 3), nd.array(w, h, 1)] for profilemeter
        '''    
        if device: return self.camera.capture_photo()
        else: return self.profilemeter.main() # TODO!!

    def _rgb_hist(self, photo: np.ndarray) -> list[dict, dict, dict]:
        '''
        Convert hist from opencv to dict format

        Args:
        hist: np.ndarray in histogram format

        Returns a dict with bins represented as the keys
        '''
        # separate the planes from the original input photo
        rgb_planes = cv2.split(photo)

        r_hist = cv2.calcHist([rgb_planes], [0], None, [256], [0, 256])
        g_hist = cv2.calcHist([rgb_planes], [1], None, [256], [0, 256])
        b_hist = cv2.calcHist([rgb_planes], [2], None, [256], [0, 256])

        # 'x_hist' is a NumPy array. To conceptually view it as a dictionary:
        # Create a dictionary from the histogram data

        r_dict = {i: int(r_hist[i][0]) for i in range(256)}
        g_dict = {i: int(g_hist[i][0]) for i in range(256)}
        b_dict = {i: int(b_hist[i][0]) for i in range(256)}

        return [r_dict, g_dict, b_dict]

    def grab_for_calibration(self,TODO) -> list[bytes, list[dict, dict, dict]]:
        '''
        Complete function for image grabbing and histogram calculation

        Args:

        Return a list with [0] = image as bytes, [1] = list of R, G and B histograms  
        '''
        raw_photo = self.camera.capture_photo()
        hist_photo = raw_photo.decode()
        hist_photo = cv2.imdecode(raw_photo)

        return [raw_photo, self._rgb_hist(hist_photo)]
    
    def streaming(self, TODO):
        pass

if __name__ == '__main__':
    utils = JSONutils()
    print(utils.json_to_cam(export=True))