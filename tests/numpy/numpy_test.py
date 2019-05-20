
import numpy as np
import cv2

image = np.zeros((120, 120), np.float32)

image[0:20, 50:80] = 100

window = cv2.namedWindow("Image")

cv2.imshow(window, image)

cv2.waitKey(20000)

