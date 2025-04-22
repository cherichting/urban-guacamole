"""
Definition of net.
"""
import datetime

from django.db import models
from django.contrib.auth.models import AbstractUser
import json
from demo import delete_face

class Classes(models.Model):
    """ 班级 """

    name = models.CharField(max_length=32, db_index=True, unique=True)
    add_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "班级"
        verbose_name_plural = "班级"
        ordering = ['-id']

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "add_time": self.add_time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def __str__(self):
        return self.name


class Course(models.Model):
    """ 课程 """
    name = models.CharField(max_length=32, db_index=True, verbose_name="课程名")
    add_time = models.DateTimeField(auto_now_add=True)
    classes = models.ForeignKey(Classes, on_delete=models.CASCADE, related_name="Course", verbose_name="班级")
    start_time = models.DateTimeField(verbose_name="开始时间")  # 开始时间为浮点数 正常是 时.分

    class Meta:
        verbose_name = "课程"
        verbose_name_plural = "课程"
        ordering = ['-id']

    def __str__(self):
        return f"{self.classes.name}-{self.start_time}-{self.name}"

    def to_dict(self, username=None):
        is_end = False
        if datetime.datetime.now() - self.start_time > datetime.timedelta(days=1):
            is_end = True
        if datetime.datetime.now().date() > self.start_time.date():
            is_end = True
        print(is_end)
        has_check_log = False
        if username:
            if self.checklog.filter(username=username, status__in=["正常签到", "补签","请假"]).count() > 0:
                has_check_log = True
            else:
                if self.checklog.filter(username=username).count() == 0:
                    CheckLog.objects.create(username=username,
                                            course=self, status="缺勤")
        return {
            "id": self.id,
            "name": self.name,
            "add_time": self.add_time.strftime("%Y-%m-%d %H:%M:%S"),
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "is_end": is_end,
            "has_check_log": has_check_log,
            "classes": self.classes.to_dict()
        }


class User(AbstractUser):
    """用户扩展表  默认ID是学生的学号 """
    image = models.ImageField(upload_to='images/avatar/', null=True, blank=True, default="images/faces/1.jpg")
    type = models.CharField(max_length=32, default="user",
                            choices=[('user', '学生'), ('teacher', '教师'), ('superuser', '超级管理员')])
    classes = models.ForeignKey(Classes, on_delete=models.CASCADE, null=True, blank=True, related_name="classes")




    class Meta(AbstractUser.Meta):
        verbose_name = "用戶"
        verbose_name_plural = "用戶"
        ordering = ['-id']

    @property
    def get_user_id(self):
        """ 获取用户学生学号 """
        return f"{self.date_joined.strftime('%Y%m%d')}{self.id}"

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "image": self.image.url,
            "type": self.type,
            "classes": self.classes.to_dict() if self.classes else None,

        }


class UserImage(models.Model):
    """ 用户上传的人脸数据 """
    image = models.ImageField(upload_to='images/faces/', null=True, blank=True)
    data = models.TextField(null=True, blank=True)
    username = models.CharField(max_length=32, db_index=True)
    add_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "人脸数据"
        verbose_name_plural = "人脸数据"
        ordering = ['-id']
    def delete(self, using=None, keep_parents=False):
        id = self.id
        delete_face(f"image_id_{id}")
        super().delete()
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "image": self.image.url,
            "data": json.loads(self.data) if self.data else None,
            "add_time": self.add_time.strftime("%Y-%m-%d %H:%M:%S"),
        }


class CheckLog(models.Model):
    """ 这个是签到记录表  默认只有签到 没有签退"""
    username = models.CharField(max_length=32, db_index=True)
    add_time = models.DateTimeField(auto_now_add=True)
    check_time = models.FloatField(null=True, blank=True)
    image = models.ImageField(upload_to='images/check/', null=True, blank=True)
    status = models.CharField(max_length=32, default="正常签到",
                              choices=[('正常签到', '正常签到'), ('迟到', '迟到'), ('缺勤', '缺勤'), ("请假", "请假"),
                                       ("补签", "补签")])

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="checklog")

    class Meta:
        verbose_name = "签到记录"
        verbose_name_plural = "签到记录"
        ordering = ['-id']

    def to_dict(self):
        has_apps = False
        if Approval.objects.filter(username=self.username, course=self.course).count() > 0:
            has_apps = True
        return {
            "id": self.id,
            "username": self.username,
            "add_time": self.add_time.strftime("%Y-%m-%d %H:%M:%S"),
            "check_time": self.check_time,
            "image": self.image.url if self.image else None,
            "status": self.status,
            "course": self.course.to_dict(),
            "has_apps": has_apps

        }


class Approval(models.Model):
    """ 审批表  用于申请签到的迟到或者缺勤的补签 或者是申请请假"""
    username = models.CharField(max_length=32, db_index=True)

    add_time = models.DateTimeField(auto_now_add=True)
    option = models.CharField(max_length=32, default="补签",
                              choices=[('补签', '补签'), ('请假', '请假')])
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="approval")
    data = models.TextField(null=True, blank=True)  # 申请内容 写请假原因的
    result = models.TextField(null=True, blank=True)  # 审批结果 如果拒绝可以写拒绝原因
    option_username = models.CharField(max_length=32, db_index=True, null=True, blank=True)  # 审批人
    edit_time = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=32, default="待审批",
                              choices=[('待审批', '待审批'), ('已通过', '已通过'), ('已拒绝', '已拒绝')])

    class Meta:
        verbose_name = "审批记录"
        verbose_name_plural = "审批记录"
        ordering = ['-id']

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "add_time": self.add_time.strftime("%Y-%m-%d %H:%M:%S"),
            "option": self.option,
            "course": self.course.to_dict(),
            "data": self.data,
            "result": self.result,
            "option_username": self.option_username,
            "edit_time": self.edit_time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": self.status,

        }
