import cv2

camera = cv2.VideoCapture(0)

window = cv2.namedWindow("Camera")

while True:

    read, frame = camera.read()

    if read:
        cv2.imshow("Camera", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()
cv2.destroyAllWindows()
