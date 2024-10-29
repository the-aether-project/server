import cv2

cap = cv2.VideoCapture("./vid.mp4")
if cap.isOpened():
    print("Video opened successfully")
else:
    print("Failed to open video")
cap.release()


print(__file__)
