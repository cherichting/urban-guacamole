import os.path

import pandas.errors
from PIL import ImageDraw, ImageFont, Image
import random
import numpy as np
import cv2, dlib
import pandas as pd
from openvino.runtime import Core

core = Core()
if os.path.exists("model.onnx"):
    net = core.read_model(model="model.onnx")
else:
    net = core.read_model(model="net/model.onnx")

model = core.compile_model(model=net, device_name="CPU")

detector = dlib.get_frontal_face_detector()

required_size = (160, 160)
if os.path.exists("face_data.csv"):
    try:
        face_data = pd.read_csv("face_data.csv", header=None, index_col=None)
    except pandas.errors.EmptyDataError:
        face_data = None


else:
    face_data = None

print("face_data shape:", face_data, )


def plot_one_box(x, img, color=None, label=None, line_thickness=3):
    # Plots one bounding box on image img

    tl = line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1  # line/font thickness
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))

    cv2.rectangle(img, c1, c2, color, tl, cv2.LINE_AA)
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
        cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)  # filled

        img = Image.fromarray(img)

        draw = ImageDraw.Draw(img)

        fontText = ImageFont.truetype(
            "simsun.ttc", 20, encoding="utf-8")

        # print((int(c1[0]), int(c1[1] - 2)), color)
        draw.text((int(c1[0]), int(c1[1] - 25)), label, (255, 255, 255), font=fontText)
    return np.array(img)


def dectect(img, dets):
    for xyxy in dets:
        x1, y1, x2, y2 = xyxy.left(), xyxy.top(), xyxy.right(), xyxy.bottom()
        img = plot_one_box([x1, y1, x2, y2], img, )
    return img


def add_face(feature, id_name):
    global face_data
    if face_data is None:
        feature.append(id_name)
        face_data = pd.DataFrame([feature], columns=list(range(0, 129)))
    else:
        feature.append(id_name)
        df = pd.DataFrame([feature], columns=list(range(0, 129)))
        face_data = pd.concat([face_data, df], ignore_index=True)
    face_data.to_csv("face_data.csv", header=False, index=False)

def delete_face(id_name):
    global face_data
    if face_data is None:
        return
    if face_data is not None:
        face_data = face_data[face_data[128] != id_name]
        face_data.to_csv("face_data.csv", header=False, index=False)



def ocr(encodings):
    """ 传入 GBR 图像  """
    """"""
    global face_data
    if os.path.exists("face_data.csv"):
        face_data = pd.read_csv("face_data.csv", header=None, index_col=None)


    else:
        face_data = None
    if face_data is None:
        return
    print("face_data", face_data)
    encodings = np.array([np.array(encodings)]).astype(np.float32)
    print(encodings.shape, encodings.dtype)

    faces = face_data[list(range(0, 128))].values

    face_distances = np.linalg.norm(faces - encodings[0], axis=1)  # 计算距离
    best_match_index = np.argmin(face_distances)  # 找到最相似的人
    print("sorce:", face_distances[best_match_index])
    if face_distances[best_match_index] < 8:  # 对比人脸特征必须  必须小于8 想要更准确的人脸 可以减小这个值
        name = face_data[128].values[best_match_index]
        print(name)
        return name


def get_face_feature(img, dets, YUV=False):
    """ 传入 GBR 图像  """
    face_encodings = []
    for k, d in enumerate(dets):
        x1, y1, x2, y2 = d.left(), d.top(), d.right(), d.bottom()
        im = img[y1:y2, x1:x2][..., ::-1]  ## 切割图片  并将切割出来的图片转 RGB
        if YUV:
            (b, g, r) = cv2.split(im[..., ::-1])
            bH = cv2.equalizeHist(b)
            gH = cv2.equalizeHist(g)
            rH = cv2.equalizeHist(r)
            # 合并每一个通道
            channels = cv2.merge((bH, gH, rH))

            im = channels[..., ::-1]

        face = cv2.resize(im, required_size).astype('float32')  # 转换人脸图片大小为160*160
        mean, std = face.mean(), face.std()

        face_pixels = (face - mean) / std  # 归一化
        samples = np.expand_dims(face_pixels, axis=0)  ## 增加一个图片数量维度

        encodings = model({model.input(0).get_any_name(): samples})

        face_encodings.append(encodings[model.output(0)][0])

    return face_encodings


def check_face(img):
    img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    dets = detector(img_gray, 1)
    if dets:
        return dets

    return []
