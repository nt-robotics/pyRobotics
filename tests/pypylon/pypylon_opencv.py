from pypylon import pylon
import cv2

tlFactory = pylon.TlFactory.GetInstance()

# 1) Create camera by index
cam_index = 1
max_cameras_number = 2

devices = tlFactory.EnumerateDevices()
cameras = pylon.InstantCameraArray(min(len(devices), max_cameras_number))
camera = cameras[cam_index]
camera.Attach(tlFactory.CreateDevice(devices[cam_index]))

# # 2) Create first camera
# camera = pylon.InstantCamera(tlFactory.CreateFirstDevice())

camera.Open()

# Строковый идентификатор, устанавливается вручную
device_user_id = camera.DeviceUserID.GetValue()
# Лимит пропускной способности
throughput_limit = camera.DeviceLinkThroughputLimit.GetValue()
# Модель камеры
model_name = camera.GetDeviceInfo().GetModelName()


print("Using device ", model_name)
print("throughput_limit ", throughput_limit)
print("device_user_id ", device_user_id)

camera.Width.SetValue(600)
camera.Height.SetValue(300)
camera.DeviceLinkThroughputLimit.SetValue(21000000)
camera.DeviceUserID.SetValue("CAMERA_0")
# camera.Width = 600                            # И так работает
# camera.Height = 300                           # И так работает
# camera.DeviceLinkThroughputLimit = 21000000   # И так работает


# converting to opencv bgr format
converter = pylon.ImageFormatConverter()
converter.OutputPixelFormat = pylon.PixelType_BGR8packed
converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

# Grabing Continusely (video) with minimal delay
camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

camera.ExposureTime = camera.ExposureTime.Min

while camera.IsGrabbing():
    grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

    if grabResult.GrabSucceeded():
        # Access the image data
        image = converter.Convert(grabResult)
        img = image.GetArray()
        cv2.namedWindow('title', cv2.WINDOW_NORMAL)
        cv2.imshow('title', img)
        k = cv2.waitKey(1)
        if k == 27:
            break
    grabResult.Release()

# Releasing the resource
camera.StopGrabbing()

cv2.destroyAllWindows()
