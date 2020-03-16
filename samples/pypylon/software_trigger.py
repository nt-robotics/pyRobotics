import cv2
from threading import Thread
from time import sleep
from datetime import datetime
from pypylon import pylon


class SoftwareTriggerExample(object):

    def __init__(self, cameras_count, is_synchro_trigger=True):
        tlFactory = pylon.TlFactory.GetInstance()
        devices = tlFactory.EnumerateDevices()

        if len(devices) < cameras_count:
            print("Too few cameras. Need two.")
            exit(-100500)

        cameras_list = pylon.InstantCameraArray(min(len(devices), cameras_count))

        # Create grab evens handler
        grab_event_handler = _GrabEventHandler(cameras_list)

        # Create and attach all Pylon Devices and set start parameters
        for cam_index, camera in enumerate(cameras_list):
            camera.Attach(tlFactory.CreateDevice(devices[cam_index]))
            camera.Open()
            # Register handlers
            camera.RegisterImageEventHandler(grab_event_handler, pylon.RegistrationMode_Append, pylon.Cleanup_Delete)
            camera.RegisterConfiguration(_ConfigurationEventPrinter(), pylon.RegistrationMode_Append, pylon.Cleanup_Delete)
            # Trigger mode
            camera.TriggerMode.SetValue('Off')
            # Exposure
            camera.ExposureAuto.SetValue('Off')
            # camera.ExposureAuto.SetValue('Once')
            # camera.ExposureAuto.SetValue('Continuous')
            # camera.AutoExposureTimeLowerLimit.SetValue(100)
            # camera.AutoExposureTimeUpperLimit.SetValue(10000)
            camera.ExposureTime.SetValue(3000)
            # White balance
            camera.BalanceWhiteAuto.SetValue('Off')
            # Gain
            camera.GainAuto.SetValue('Off')
            # Immediate Trigger mode
            camera.BslImmediateTriggerMode.SetValue('On')

            print("Camera # " + str(cam_index), " ", camera.DeviceUserID.GetValue())
            print(" ( Model: ", camera.GetDeviceInfo().GetModelName(), " | Serial: ", camera.DeviceSerialNumber.GetValue(), ")")
            print("USB speed: ", camera.BslUSBSpeedMode.GetValue())
            print("--------------------------")

        # Create software trigger
        trigger = _SoftwareTriggerMultiple(cameras_list)
        if is_synchro_trigger:
            trigger.start()

        cameras_list.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

        while cameras_list.IsGrabbing():
            cameras_list.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

        for camera in cameras_list:
            print("Off trigger mode")
            camera.TriggerMode.SetValue('Off')
        trigger.stop()
        cameras_list.Close()
        cv2.destroyAllWindows()


class _SoftwareTriggerMultiple(Thread):

    def __init__(self, cameras_list):
        super().__init__()
        self.__cameras = cameras_list

        self.__is_started = False

    def stop(self):
        self.__is_started = False

    def run(self) -> None:
        self.__is_started = True

        for camera in self.__cameras:
            camera.AcquisitionMode.SetValue('Continuous')
            camera.TriggerSelector.SetValue('FrameStart')
            camera.TriggerMode.SetValue('On')
            camera.TriggerSource.SetValue('Software')
            camera.TriggerActivation.SetValue('RisingEdge')
            # camera.TriggerActivation.SetValue('FallingEdge')

        while self.__is_started:
            print("********",)
            print("TRIGGER. Time:", datetime.now())
            print("********",)
            for camera in self.__cameras:
                camera.TriggerSoftware.Execute()
            sleep(0.02)


class _GrabEventHandler(pylon.ImageEventHandler):

    def __init__(self, cameras_list):
        super().__init__()
        print("Init")
        self.__prev_cam_index = None
        self.__prev_time = datetime.now()

        self.__cameras_list = cameras_list

        self.__converter = pylon.ImageFormatConverter()
        self.__converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.__converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

    def OnImagesSkipped(self, camera, countOfSkippedImages):
        print("OnImagesSkipped event for device ", camera.DeviceUserID.GetValue())
        print(countOfSkippedImages, " images have been skipped.")

    def OnImageGrabbed(self, camera, grabResult):
        camera_index = grabResult.GetCameraContext()
        frame_rate = camera.ResultingFrameRate.GetValue()
        print("___________________________________________")
        print("Camera #", camera_index, camera.DeviceUserID.GetValue(), "(", camera.GetDeviceInfo().GetModelName(), ")")
        print("FPS: ", frame_rate)

        if grabResult.GrabSucceeded():
            time = datetime.now()
            print("Frame time: ", time)

            if self.__prev_cam_index != camera_index:
                delta = time - self.__prev_time
                self.__prev_time = time
                self.__prev_cam_index = camera_index
                print("Delta: ", delta)
                # print("Size: ", grabResult.GetWidth(), " x ", grabResult.GetHeight())

            camera_index = grabResult.GetCameraContext()
            window_name = "Camera " + str(camera_index)
            pylon_image = self.__converter.Convert(grabResult)
            opencv_image = pylon_image.GetArray()
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, 600, 450)
            cv2.moveWindow(window_name, camera_index * 620, 100)
            cv2.imshow(window_name, opencv_image)
            k = cv2.waitKey(1)
            if k == 27:
                self.__cameras_list.StopGrabbing()
        else:
            print("Error: ", grabResult.GetErrorCode(), grabResult.GetErrorDescription())

        print("===============================================")


class _ConfigurationEventPrinter(pylon.ConfigurationEventHandler):
    def OnAttach(self, camera):
        print("OnAttach event")

    def OnAttached(self, camera):
        print("OnAttached event for device ", camera.DeviceUserID.GetValue())

    def OnOpen(self, camera):
        print("OnOpen event for device ", camera.DeviceUserID.GetValue())

    def OnOpened(self, camera):
        print("OnOpened event for device ", camera.DeviceUserID.GetValue())

    def OnGrabStart(self, camera):
        print("OnGrabStart event for device ", camera.DeviceUserID.GetValue())

    def OnGrabStarted(self, camera):
        print("OnGrabStarted event for device ", camera.DeviceUserID.GetValue())

    def OnGrabStop(self, camera):
        print("OnGrabStop event for device ", camera.DeviceUserID.GetValue())

    def OnGrabStopped(self, camera):
        print("OnGrabStopped event for device ", camera.DeviceUserID.GetValue())

    def OnClose(self, camera):
        print("OnClose event for device ", camera.DeviceUserID.GetValue())

    def OnClosed(self, camera):
        print("OnClosed event for device ", camera)

    def OnDestroy(self, camera):
        print("OnDestroy event for device ", camera.DeviceUserID.GetValue())

    def OnDestroyed(self, camera):
        print("OnDestroyed event")

    def OnDetach(self, camera):
        print("OnDetach event for device ", camera.DeviceUserID.GetValue())

    def OnDetached(self, camera):
        print("OnDetached event for device ", camera.DeviceUserID.GetValue())

    def OnGrabError(self, camera, errorMessage):
        print("OnGrabError event for device ", camera.DeviceUserID.GetValue())
        print("Error Message: ", errorMessage)

    def OnCameraDeviceRemoved(self, camera):
        print("OnCameraDeviceRemoved event for device ", camera.DeviceUserID.GetValue())


if __name__ == "__main__":

    CAMERAS_COUNT = 2
    SoftwareTriggerExample(CAMERAS_COUNT)
