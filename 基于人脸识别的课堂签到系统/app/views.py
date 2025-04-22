"""
Definition of views.
"""
import base64
import traceback
from datetime import datetime
from django.http import HttpRequest, JsonResponse, HttpResponseRedirect
from .forms import RegsiterForm
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
import math
from django.shortcuts import render
import os
from io import BytesIO
from .models import *
from PIL import Image as PIL_Image
from demo import delete_face as delete_face_to_csv
from django.db.models import Count, Sum, Q


def checkLogin(func):
    def check(request, *args, **kwargs):
        if not request.user.is_anonymous:

            return func(request, *args, **kwargs)
        else:
            return HttpResponseRedirect("/login")

    return check


def calculate_neighboring_pages(current_page, total_pages):
    # 限制页码范围在1到总页数之间
    current_page = max(0, min(current_page, total_pages))

    # 计算开始和结束的页码
    start_page = max(0, current_page - 2)
    end_page = min(total_pages, current_page + 2)

    # 如果需要展示5个页码，则根据实际情况调整两端的页码
    while len(range(start_page, end_page + 1)) < 5:
        if start_page > 1:
            start_page -= 1
        elif end_page < total_pages:
            end_page += 1
        else:
            break

    # 获取并返回相邻的5页码列表
    neighboring_pages = list(range(start_page, end_page))

    return neighboring_pages


def changeavatar(request):
    if request.method == "POST":
        username = request.user.username
        image = request.POST["image"].split(",")[1]
        image = base64.b64decode(image)
        image = PIL_Image.open(BytesIO(image))
        if not os.path.exists("app/static/images/avatar/"):
            os.mkdir("app/static/images/avatar/")
        image.save("app/static/images/avatar/" + username + ".jpg")
        request.user.image = "images/avatar/" + username + ".jpg"
        request.user.save()
        return JsonResponse({"code": 200, "msg": "修改成功!"})


def get_user_image(request):
    if request.method == "GET":
        username = request.user.username
        page = request.GET.get('page', 0)
        page = int(page)

        images = UserImage.objects.filter(username=username).order_by("-id")
        count = images.count()

        page_list = calculate_neighboring_pages(page, math.ceil(count / 6))

        page_list.sort()

        return JsonResponse({"code": 200, "msg": "获取成功!",
                             "images": images[page * 6:(page + 1) * 6],
                             "page": page, "count": count,
                             "page_list": page_list,
                             "page_count": page * 6,
                             })


def delete_face(request):
    if request.method == "POST":
        username = request.user.username
        image_id = request.POST.get("id")
        try:
            image = UserImage.objects.get(id=int(image_id), username=username)
            image.image.delete()
            image.delete()
            delete_face_to_csv(f"image_id_{image_id}")
            return JsonResponse({"code": 200, "msg": "删除成功!"})
        except:
            print(traceback.format_exc())
            return JsonResponse({"code": 500, "msg": "删除失败!"})


def ocr_log(request):
    if request.method == "GET":
        username = request.user.username
        page = request.GET.get('page', 0)
        page = int(page)
        if request.user.type == "user":
            logs = CheckLog.objects.filter(username=username).order_by("-id")
        elif request.user.type == "teacher":
            logs = CheckLog.objects.filter(course__classes=request.user.classes).order_by("-id")
        else:
            logs = CheckLog.objects.all().order_by("-id")

        count = logs.count()
        # 生成page附近的几个页码
        page_list = calculate_neighboring_pages(page, math.ceil(count / 15))

        page_list.sort()
        print(page_list, page)
        return render(request, 'ocr_log.html',
                      {"logs": [x.to_dict() for x in logs[page * 15:(page + 1) * 15]],
                       "page": page, "count": count,
                       "page_list": page_list,
                       "title": "签到记录", "page_count": page * 15,
                       "username": username}
                      )
    elif request.method == "DELETE":

        data = json.loads(request.body)
        try:
            log = CheckLog.objects.get(id=int(data["id"]))
            log.delete()
            return JsonResponse({"code": 200, "msg": "删除成功!"})
        except:
            print(traceback.format_exc())
            return JsonResponse({"code": 500, "msg": "删除失败!"})


@checkLogin
def changepwd(request):
    username = request.user.username
    if request.method == "GET":
        return render(request, "change_password.html", {
            "username": username
        })
    else:
        password = request.POST.get("password")
        new_password = request.POST.get("new_password")
        new_password2 = request.POST.get("new_password2")
        if new_password != new_password2:
            return JsonResponse({"code": 500, "msg": "新密碼兩次輸入不一致!"})
        user = authenticate(username=username, password=password)
        if user:
            user.set_password(new_password)
            user.save()
            return JsonResponse({"code": 200, "msg": "修改成功!"})
        else:
            return JsonResponse({"code": 500, "msg": "密码错误!"})


def login_user(request):
    if request.method == "GET":
        return render(request, "login.html", {"title": "登录", })
    else:
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return JsonResponse({"code": 200, "msg": "登录成功!"})

        return JsonResponse({"code": 500, "msg": "用户名或密码错误!"})


def aggs_data(request):
    """ 对签到日志进行各种统计 """
    if request.method == "GET":

        username = request.GET.get("username")
        classes = request.GET.get("classes_id")

        if request.user.type == "user":
            check_logs = CheckLog.objects.filter(username=request.user.username)
        elif request.user.type == "teacher":
            check_logs = CheckLog.objects.filter(course=request.user.course)
            if username:
                check_logs = check_logs.filter(username=username)
        else:

            check_logs = CheckLog.objects.all()
            if username:
                check_logs = check_logs.filter(username=username)
            if classes:
                check_logs = check_logs.filter(course__classes_id=int(classes))

        check_aggs = check_logs.aggregate(
            total=Count("id"),
            late=Count("id", filter=Q(status="迟到")),
            absent=Count("id", filter=Q(status="缺勤")),
            leave=Count("id", filter=Q(status="请假")),
            normal=Count("id", filter=Q(status="正常签到")),
            resing=Count("id", filter=Q(status="补签")), )
        data = [
            {"name": "正常签到", "value": check_aggs["normal"]},
            {"name": "迟到", "value": check_aggs["late"]},
            {"name": "缺勤", "value": check_aggs["absent"]},
            {"name": "请假", "value": check_aggs["leave"]},
            {"name": "补签", "value": check_aggs["resing"]},

        ]
        return JsonResponse({"code": 200, "msg": "获取成功!", "data": data, })


@checkLogin
def courses(request):
    if request.method == "GET":
        username = request.user.username
        if request.user.type == "user":
            courses = Course.objects.filter(classes=request.user.classes,
                                            ).order_by("-id")
            return render(request, "courses.html", {
                "courses": [x.to_dict(request.user.username) for x in courses],
                "username": username,
                "title": "活动管理",
            })
        if request.user.type == "teacher":
            courses = Course.objects.filter(classes=request.user.classes, ).order_by("-id")
            return render(request, "courses.html", {
                "courses": [x.to_dict() for x in courses],
                "username": username,
                "title": "活动管理",
            })
        courses = Course.objects.all().order_by("-id")
        classess = Classes.objects.all().order_by("-id")
        return render(request, "courses.html", {
            "courses": [x.to_dict() for x in courses],
            "username": username,
            "title": "活动管理", "classess": classess

        })
    elif request.method == "POST":
        name = request.POST.get("name")
        classes = request.POST.get("classes")
        start_time = request.POST.get("start_time")
        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
        if request.user.type == "user":
            return JsonResponse({"code": 500, "msg": "权限不足!"})
        course = Course.objects.create(name=name, classes=Classes.objects.get(id=classes),
                                       start_time=start_time)
        return JsonResponse({"code": 200, "msg": "添加成功!"})
    elif request.method == "DELETE":
        data = json.loads(request.body)
        try:
            course = Course.objects.get(id=data.get("id"))
            course.delete()
            return JsonResponse({"code": 200, "msg": "删除成功!"})
        except:
            return JsonResponse({"code": 500, "msg": "删除失败!"})


@checkLogin
def classess(request):
    if request.method == "GET":
        username = request.user.username
        page = request.GET.get('page', 0)
        page = int(page)

        clss = Classes.objects.all().order_by("-id")

        count = clss.count()

        page_list = calculate_neighboring_pages(page, math.ceil(count / 5))

        page_list.sort()

        return render(request, "classess.html", {

            "username": username,
            "title": "班级管理", "classess": [x.to_dict() for x in clss],
            "page": page, "count": count, "page_list": page_list,
            "page_count": page * 5,

        })
    elif request.method == "POST":
        name = request.POST.get("name")

        if request.user.type == "user" or request.user.type == "teacher":
            return JsonResponse({"code": 500, "msg": "权限不足!"})

        classes = Classes.objects.create(name=name)
        return JsonResponse({"code": 200, "msg": "添加成功!"})
    elif request.method == "DELETE":
        data = json.loads(request.body)
        try:
            cls = Classes.objects.get(id=data.get("id"))
            cls.delete()
            return JsonResponse({"code": 200, "msg": "删除成功!"})
        except:
            return JsonResponse({"code": 500, "msg": "删除失败!"})


@checkLogin
def users(request):
    if request.method == "GET":
        username = request.user.username
        page = request.GET.get('page', 0)
        page = int(page)

        users = User.objects.all().order_by("-id")

        count = users.count()

        page_list = calculate_neighboring_pages(page, math.ceil(count / 5))

        page_list.sort()

        return render(request, "users.html", {

            "username": username,
            "title": "用户管理", "users": users,
            "page": page, "count": count, "page_list": page_list,
            "page_count": page * 5,

        })
    elif request.method == "POST":
        name = request.POST.get("name")

        if request.user.type == "user" or request.user.type == "teacher":
            return JsonResponse({"code": 500, "msg": "权限不足!"})

        classes = Classes.objects.create(name=name)
        return JsonResponse({"code": 200, "msg": "添加成功!"})
    elif request.method == "DELETE":
        data = json.loads(request.body)
        try:
            cls = Classes.objects.get(id=data.get("id"))
            cls.delete()
            return JsonResponse({"code": 200, "msg": "删除成功!"})
        except:
            return JsonResponse({"code": 500, "msg": "删除失败!"})


def approvals(request):
    if request.method == "GET":
        if request.user.type == "user":
            apps = Approval.objects.filter(username=request.user.username,
                                           ).order_by("-id")
            return render(request, "apps.html", {
                "approvals": apps,
                "title": "审批审核",
            })
        if request.user.type == "teacher":
            apps = Approval.objects.filter(course__classes=request.user.classes, ).order_by("-id")
            return render(request, "apps.html", {
                "approvals": apps,
                "title": "审批审核",
            })
        apps = Approval.objects.all().order_by("-id")

        return render(request, "apps.html", {
            "approvals": apps,
            "title": "审批审核",

        })
    elif request.method == "POST":
        option = request.POST.get("option")
        data = request.POST.get("data")
        course = Course.objects.get(id= int(request.POST.get("course_id")))
        apps = Approval.objects.create(option=option,
                                       data=data,
                                       username=request.user.username,
                                       course=course,
                                       status="待审批")

        return JsonResponse({"code": 200, "msg": "添加成功!", "data": apps.to_dict()})
    elif request.method == "PUT":
        """ 通过/不通过 审批"""
        data = json.loads(request.body)
        apps_id = data.get("id")
        status = data.get("status")
        result = data.get("result")
        apps = Approval.objects.get(id=apps_id)
        apps.status = status
        apps.result = result
        apps.option_username = request.user.username
        apps.save()
        if status == "已通过":
            check_log = CheckLog.objects.get(username=apps.username, course=apps.course)
            check_log.status = apps.option
            check_log.save()

        return JsonResponse({"code": 200, "msg": "审批成功!", "data": apps.to_dict()})

    elif request.method == "DELETE":
        data = json.loads(request.body)
        try:
            course = Course.objects.get(id=data.get("id"))
            course.delete()
            return JsonResponse({"code": 200, "msg": "删除成功!"})
        except:
            return JsonResponse({"code": 500, "msg": "删除失败!"})


@checkLogin
def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    if request.method == "GET":
        if request.user.type == "user":
            page = request.GET.get('page', 0)
            page = int(page)

            images = UserImage.objects.filter(username=request.user.username).order_by("-id")
            count = images.count()

            page_list = calculate_neighboring_pages(page, math.ceil(count / 5))

            page_list.sort()

            check_log = CheckLog.objects.filter(username=request.user.username, image__isnull=False).order_by(
                "-id")[:10]

            succ_check_log = CheckLog.objects.filter(username=request.user.username,
                                                     status__in=["正常签到", "请假", "补签"])
            return render(request, "user_index.html", {
                "images_count": images.count(),

                "images": images[page * 5:(page + 1) * 5],
                "page": page, "count": count,
                "page_list": page_list,
                "page_count": page * 5,
                "check_log": check_log,
                "check_log_count": check_log.count(),
                "succ_check_log_count": succ_check_log.count(),

            })
        classes = request.GET.get("classes_id")
        if request.user.type == "teacher":
            check_log = CheckLog.objects.filter(course__classes=request.user.classes, image__isnull=False)
        else:
            check_log = CheckLog.objects.filter(image__isnull=False)
            if classes:
                check_log = check_log.filter(course__classes_id=int(classes))

        username = request.GET.get("username")
        if username:
            check_log = check_log.filter(username=username)

        return render(
            request,
            'index.html',
            {
                'title': '首页',
                "check_log": check_log.order_by("-id")[:10]

            }
        )


def get_classes(request):
    if request.method == "GET":
        classes = Classes.objects.all()
        return JsonResponse({"code": 200, "msg": "获取成功!", "classes": [i.to_dict() for i in classes]})


def register(request):
    """Renders the contact page."""
    if request.method == "GET":
        classes = Classes.objects.all()
        return render(
            request,
            'register.html',
            {
                'title': '用户注册',
                "form": RegsiterForm(),
                "classes": classes,
            }
        )
    if request.method == "POST":
        form = RegsiterForm(request.POST)

        if form.is_valid():

            if form.cleaned_data["password"] != form.cleaned_data["password2"]:
                return JsonResponse({
                    "code": 500,
                    "msg": "两次密码不一致"
                })
            try:
                user = User.objects.get(username=form.cleaned_data["username"])
                return JsonResponse({"code": 500, "msg": "账号已存在!"})
            except:
                class_name = form.cleaned_data["class_name"]
                try:
                    classes = Classes.objects.get(name=class_name)
                except:
                    return JsonResponse({"code": 500, "msg": "班级不存在!"})
                User.objects.create_user(username=form.cleaned_data["username"],
                                         password=form.cleaned_data["password2"],
                                         type=form.cleaned_data["user_type"],
                                         classes=classes)
                user = User.objects.get(username=form.cleaned_data["username"])
                login(request, user)
                return JsonResponse({"code": 200, "msg": "注册成功！"})
            return JsonResponse({"code": 200, "msg": "注册成功!请登录查看"})
        else:
            return JsonResponse({"code": 500, "msg": "请输入正确的信息"})
    return render(
        request,
        'register.html',
        {
            'title': '用户注册',
            "form": RegsiterForm(),

            'year': datetime.now().year,
        }
    )
