import datetime
import time
import uuid

from demo import check_face, get_face_feature, add_face, ocr
import base64
from io import BytesIO
from PIL import Image
import numpy as np
from .models import *
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.shortcuts import render


def updata_face(request):
    if request.method == "POST":
        user_img_count = UserImage.objects.filter(username=request.user.username).count()
        if user_img_count >= 50:
            return JsonResponse({"status": "error", "msg": "最多上传50张图片"})
        image = request.POST["image"].split(",")[1]
        img_bytes = BytesIO(base64.b64decode(image))
        img = Image.open(img_bytes).convert("RGB")
        img_np = np.array(img)
        face_locations = check_face(img_np)
        if len(face_locations) == 0:
            return JsonResponse({"status": "error", "msg": "未检测到人脸"})
        elif len(face_locations) > 1:
            return JsonResponse({"status": "error", "msg": "检测到多个人脸"})
        det = face_locations[0]
        x1, y1, x2, y2 = det.left(), det.top(), det.right(), det.bottom()

        face_image = img_np[y1:y2, x1:x2]
        face_encoding = list(get_face_feature(img_np, face_locations)[0])
        face_encoding = [float(i) for i in face_encoding]
        pil_image = Image.fromarray(face_image)

        buffer = BytesIO()
        pil_image.save(buffer, format='PNG')  # 或者根据需要选择其他格式
        buffer.seek(0)
        image_file = ContentFile(buffer.getvalue())

        # 使用InMemoryUploadedFile包装ContentFile
        file_name = f"{uuid.uuid4()}.png"  # 或者根据需要生成文件名
        django_file = InMemoryUploadedFile(
            file=image_file,
            field_name='image',
            name=file_name,
            content_type='image/png',
            size=image_file.size,
            charset=None
        )

        image_db = UserImage.objects.create(username=request.user.username, image=django_file,
                                            data=json.dumps(face_encoding))
        add_face(face_encoding, f"image_id_{image_db.id}")
        count = UserImage.objects.filter(username=request.user.username).count()
        return JsonResponse({"code": 200, "msg": "上传成功", "count": count})


def check_in(request):
    if request.method == "GET":
        course_id = request.GET.get("course_id")
        course = Course.objects.get(id=int(course_id))
        return render(request, "check_in.html", {"course": course.to_dict(username=request.user.username)})
    else:
        course_id = request.POST.get("course_id")
        course = Course.objects.get(id=int(course_id))
        image = request.POST["image"].split(",")[1]
        img_bytes = BytesIO(base64.b64decode(image))
        img = Image.open(img_bytes).convert("RGB")
        img_np = np.array(img)
        face_locations = check_face(img_np)
        if len(face_locations) == 0:
            return JsonResponse({"code": 500, "msg": "未检测到人脸"})
        elif len(face_locations) > 1:
            return JsonResponse({"code": 500, "msg": "检测到多个人脸"})
        else:
            det = face_locations[0]
            x1, y1, x2, y2 = det.left(), det.top(), det.right(), det.bottom()
            face_image = img_np[y1:y2, x1:x2]
            face_encoding = list(get_face_feature(img_np, face_locations)[0])
            face_encoding = [float(i) for i in face_encoding]
            result = ocr(face_encoding)
            if not result:
                return JsonResponse({"code": 500, "msg": ""})
            else:
                image_id = UserImage.objects.get(id=int(result.split("_")[-1]))
                user = User.objects.get(username=image_id.username)
                if user.type == "user" and user.classes == course.classes:
                    status = "正常签到"
                    if datetime.datetime.now() > course.start_time:
                        status = "迟到"
                    if CheckLog.objects.filter(username=image_id.username, course=course).count() > 0:
                        return JsonResponse({"status": "error", "msg": f"你好：{image_id.username}，您已经签到过了"})
                    django_file = InMemoryUploadedFile(
                        file=BytesIO(base64.b64decode(image)),
                        field_name='image',
                        name=f"{uuid.uuid4()}.png",
                        content_type='image/png',
                        size=len(image),
                        charset=None
                    )

                    check_log = CheckLog.objects.create(username=image_id.username,
                                                        course=course,
                                                        check_time=time.time(),
                                                        status="正常签到",
                                                        image=django_file)
                    return JsonResponse({"code": 200, "msg": f"你好：{image_id.username}，{status}", "data": check_log.to_dict()})
                else:
                    return JsonResponse({"code": 500, "msg": "签到失败,可能由于您不是该班级学生！"})
