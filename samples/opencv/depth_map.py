
import cv2 as cv
from matplotlib import pyplot as plt

# imgL = cv.imread('/home/user/Изображения/calibrateCameras/Tsukuba_L-300x225.png', 0)
# imgR = cv.imread('/home/user/Изображения/calibrateCameras/Tsukuba_R-300x225.png', 0)
imgL = cv.imread('C:/Users/039174/Projects/PycharmProjects/pyRobotics/samples/opencv/Tsukuba_L-300x225.png', 0)
imgR = cv.imread('C:/Users/039174/Projects/PycharmProjects/pyRobotics/samples/opencv/Tsukuba_R-300x225.png', 0)

stereo = cv.StereoBM_create(numDisparities=16, blockSize=15)
disparity = stereo.compute(imgL, imgR)
# plt.subplot(1)
plt.imshow(disparity, 'gray')
plt.show()
