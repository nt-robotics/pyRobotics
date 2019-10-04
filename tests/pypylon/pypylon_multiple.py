
import cv2
from pypylon import pylon


maxCamerasToUse = 2

tlFactory = pylon.TlFactory.GetInstance()

# Get all attached devices and exit application if no device is found.
devices = tlFactory.EnumerateDevices()

for device in devices:
    print(device)
    print(device.GetSerialNumber())

# Create an array of instant cameras for the found devices and avoid exceeding a maximum number of devices.
cameras = pylon.InstantCameraArray(min(len(devices), maxCamerasToUse))

# converting to opencv bgr format
converter = pylon.ImageFormatConverter()
converter.OutputPixelFormat = pylon.PixelType_BGR8packed
converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

# Create and attach all Pylon Devices.
for i, camera in enumerate(cameras):
    camera.Attach(tlFactory.CreateDevice(devices[i]))

    camera.Open()

    # # Print camera info
    # device_user_id = camera.DeviceUserID.GetValue()
    # throughput_limit = camera.DeviceLinkThroughputLimit.GetValue()
    # model_name = camera.GetDeviceInfo().GetModelName()
    # print("Using device ", model_name)
    # print("throughput_limit ", throughput_limit)
    # print("device_user_id ", device_user_id)

    camera.Width.SetValue(600)
    camera.Height.SetValue(300)
    camera.DeviceLinkThroughputLimit.SetValue(21000000)
    camera.DeviceUserID.SetValue("CAMERA_" + str(i))

cameras.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)


while cameras.IsGrabbing():
    grabResult = cameras.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

    # Camera number
    cameraContextValue = grabResult.GetCameraContext()

    if grabResult.GrabSucceeded():
        image_title = 'title' + str(cameraContextValue)
        # Access the image data
        image = converter.Convert(grabResult)
        opencv_frame = image.GetArray()
        cv2.namedWindow(image_title, cv2.WINDOW_NORMAL)
        cv2.imshow(image_title, opencv_frame)
        k = cv2.waitKey(1)
        if k == 27:
            break
    grabResult.Release()


cameras.StopGrabbing()
cv2.destroyAllWindows()
