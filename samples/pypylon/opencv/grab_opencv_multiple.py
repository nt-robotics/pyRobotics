from pypylon import pylon
import cv2

CAMERAS_COUNT = 2

tlFactory = pylon.TlFactory.GetInstance()
devices = tlFactory.EnumerateDevices()

if len(devices) < CAMERAS_COUNT:
    print("Too few cameras. Need two.")

cameras_list = pylon.InstantCameraArray(min(len(devices), CAMERAS_COUNT))

# Create and attach all Pylon Devices.
for cam_index, camera in enumerate(cameras_list):
    camera.Attach(tlFactory.CreateDevice(devices[cam_index]))
    camera.Open()
    print("Using device ", camera.GetDeviceInfo().GetModelName())

    camera.TriggerMode.SetValue('Off')
    camera.ExposureAuto.SetValue('Off')
    camera.ExposureTime.SetValue(5000)

converter = pylon.ImageFormatConverter()
converter.OutputPixelFormat = pylon.PixelType_BGR8packed
converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

# cameras_list.StartGrabbing()
# cameras_list.StartGrabbing(pylon.GrabStrategy_OneByOne)
cameras_list.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

while cameras_list.IsGrabbing():

    grabResult = cameras_list.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

    if grabResult.GrabSucceeded():
        camera_index = grabResult.GetCameraContext()
        window_name = "Camera " + str(camera_index)
        pylon_image = converter.Convert(grabResult)
        opencv_image = pylon_image.GetArray()
        cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
        cv2.imshow(window_name, opencv_image)
        k = cv2.waitKey(1)
        if k == 27:
            break
    grabResult.Release()

cameras_list.Close()
