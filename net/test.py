import dlib
import cv2
import matplotlib.pyplot as plt
import numpy as np
import math
import os, glob

detector = dlib.get_frontal_face_detector()
sp = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

facerec = dlib.face_recognition_model_v1("dlib_face_recognition_resnet_model_v1.dat")

cap = cv2.VideoCapture(0)
cap.set(6, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
descriptors = []
index = 0
while True:  # infinite loop for webcam video capture
    index += 1
    ret, frame = cap.read()  # read a frame from the webcam

    frame = cv2.flip(frame, 2)
    if index % 3 != 0:
        cv2.imshow(f"Frame", frame)  # show the frame on screen
        if cv2.waitKey(20) & 0xFF == ord('q'):
            break
        continue
    img_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

    dets = detector(img_gray, 1)
    print(f"Number of faces detected: {len(dets)} {len(descriptors)} {frame.shape}")
    if len(dets) > 1:
        print("多个人脸 请无关人员移除镜头")
        cv2.imshow(f"Frame", frame)  # show the frame on screen
        if cv2.waitKey(20) & 0xFF == ord('q'):
            break
        continue
    for k, d in enumerate(dets):
        # 2.关键点检测
        shape = sp(frame, d)


        # 3.描述子提取，128D向量
        face_descriptor = facerec.compute_face_descriptor(frame, shape)

        # 转换为numpy array
        v = np.array(face_descriptor)
        print(v.shape)
        descriptors.append(v)
    cv2.imshow(f"Frame", frame)  # show the frame on screen

    if cv2.waitKey(20) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
