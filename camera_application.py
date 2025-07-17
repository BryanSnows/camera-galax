# run in the global env (3.10.12)
import filecmp
import cv2

import gxipy as gx

from json_utils import JSONutils

params = {
    "TriggerSelector": "FrameStart",
    "TriggerMode": "On",
    "TriggerSource": "LINE0",
    "TriggerActivation": "FallingEdge",
    "TriggerDelay": 0.0,
    "AcquisitionModeEntry": "Continuous",
    "LineSelector": "Line1",
    "LineMode": "Output",
    "OffsetX": 0.0,
    "OffsetY": 0.0,
    "HeightMax": 3000.0,
    "WidthMax": 4096.0,
    "HeightMin": 1.0,
    "WidthMin": 8.0,
    "Height": 3000.0,
    "Width": 4096.0,
    "ExposureTime": 12500.0,
    "ExposureAuto": "Off",
    "AutoExposureTimeMin": 21.0,
    "AutoExposureTimeMax": 1000000.0,
    "Gain": 0.0,
    "GainSelector": "AnalogAll",
    "GainAuto": "False",
    "BalanceRatioSelectorRed": "Red",
    "BalanceRatioRed": 1.5,
    "BalanceRatioSelectorGreen": "Green",
    "BalanceRatioGreen": 1.0,
    "BalanceRatioSelectorBlue": "Blue",
    "BalanceRatioBlue": 1.75,
    "GammaParam": "False",
    "GammaEnable": "True",
    "Gamma": "False"
}

class Camera:
    def __init__(self):
        self.device_manager = gx.DeviceManager()
        
        self.cam_params = 'cam_params.txt'
        self.cam_params_temp = 'cam_params_temp.txt'
        
        self.cam = self.device_manager.open_device_by_index(1)
        self.cam.stream_on()
        
    def save_acquisition_parameters(self, output_file:str) -> dict:
        '''
        Export the camera_params to some specified file, compatible with Daheng format

        Args:
        output_file: str with dir/file_name.txt

        Return:
        dict with parameters and values
        '''
        self.cam.export_config_file(output_file)
        return JSONutils.cam_to_json(output_file, export=False)

    def load_acquisition_parameters(self, input_file:str) -> None:
        '''
        Import the camera_params from some specified file, compatible with Daheng format

        Args:
        input_file: str with dir/file_name.txt

        Return:
        None
        '''
        try: 
            self.cam.import_config_file(input_file)
            return True
        except:
            return False

    def update_settings(self, input:dict = params) -> bool: #json 
        '''
        Receive new settings in dict format and load to camera. Can check if the settings was applied with 'check_update' flag

        Args:
        input_file: str with dir/file_name.txt

        Return:
        True if the settings was correctly updated, and False if not
        ''' 
        JSONutils.dict_to_cam(input=input, output=self.cam_params)
        self.load_acquisition_parameters(self.cam_params)
        
        # check if the parameters was successfully updated
        self.save_acquisition_parameters(self.cam_params_temp)

        if filecmp.cmp(self.cam_params,
                       self.cam_params_temp,
                       shallow=False):
            return True

        else: return False

    def capture_photo(self) -> bytes: #captura
        raw_image = self.cam.data_stream[0].get_image()
        if raw_image is not None:
            # Ensure that a valid frame was acquired
            if raw_image.get_status() == gx.GxStatusList.SUCCESS:
                raw_image = raw_image.convert('RGB').get_numpy_array()
                _, buf_image = cv2.imencode('.png', raw_image, [cv2.IMWRITE_PNG_COMPRESSION, 5])
                cv2.imwrite('test.png', raw_image, [cv2.IMWRITE_PNG_COMPRESSION, 5])
                return buf_image.tobytes()
        else: 
            # The camera could be bottlenecked with previous instructions
            # Returning error message to avoid crash
            return 'Frame grabbing was not done'.encode(encoding="utf-8")

    def set_for_stream(self, release:bool = False) -> bool:
        '''
        Open or close frame grabbing for connecting in another application
        Args:
        release: True to release, False to lock

        Return True if successful, False otherwise
        '''
        if release:
            try:
                self.cam.stream_off()
                return True
            except: return False
        
        else:
            try:
                self.cam.stream_on()
                return True
            except: return False


if __name__ == "__main__":
    camera = Camera()
    camera.capture_photo()