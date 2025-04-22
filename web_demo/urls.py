from datetime import datetime
from django.urls import path
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from app import forms, views, nets

urlpatterns = [
    path('', views.home, name='home'),
    path('register', views.register, name='register'),
    path("add_new_face", nets.updata_face),
    path("changepwd", views.changepwd),
    path("delete_face", views.delete_face),
    path("changeavatar", views.changeavatar),
    path("get_classes", views.get_classes),
    path("courses", views.courses),
    path("classes", views.classess),
    path("users", views.users),
    path("apps", views.approvals),
    path("check_in", nets.check_in),
    path("aggs_data", views.aggs_data),

    path('login',
         views.login_user,
         name='login'),
    path("ocr_log", views.ocr_log, name='ocr_log'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),

    path('admin/', admin.site.urls),
]
