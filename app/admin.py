from django.contrib import admin
from demo import delete_face

from django.utils.safestring import mark_safe
from .models import *


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'type', 'classes', 'image')
    list_filter = ('type', 'classes')
    search_fields = ('username', 'type', 'classes')
    list_per_page = 10
    actions_on_top = True
    actions_on_bottom = False
    save_on_top = True
    list_display_links = ('username',)
    list_editable = ('type', 'classes')
    list_select_related = ('classes',)


admin.site.register(User, UserAdmin)


class ClassesAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)
    search_fields = ('name',)
    list_per_page = 10
    actions_on_top = True
    actions_on_bottom = False
    save_on_top = True
    list_display_links = ('name',)
    list_editable = ()
    list_select_related = ()


admin.site.register(Classes, ClassesAdmin)


class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'classes', 'start_time',)
    list_filter = ('classes', 'start_time',)
    search_fields = ('name', 'classes', 'start_time',)
    list_per_page = 10
    actions_on_top = True
    actions_on_bottom = False
    save_on_top = True
    list_display_links = ('name',)
    list_editable = ('classes', 'start_time',)
    list_select_related = ('classes',)


admin.site.register(Course, CourseAdmin)


class CheckLogAdmin(admin.ModelAdmin):
    list_display = ('username', 'course', 'status', 'check_time', 'image')
    list_filter = ('username', 'course', 'status', 'check_time')
    search_fields = ('username', 'course', 'status', 'check_time')
    list_per_page = 10
    actions_on_top = True
    actions_on_bottom = False
    save_on_top = True
    list_display_links = ('username',)
    list_editable = ('course', 'status', 'check_time')
    list_select_related = ('course',)


admin.site.register(CheckLog, CheckLogAdmin)


class ApprovalAdmin(admin.ModelAdmin):
    list_display = ('username', 'option_username', 'option', 'course', 'status', 'edit_time', 'result')
    list_filter = ('username', 'option_username', 'option', 'course', 'status', 'edit_time')
    search_fields = ('username', 'option_username', 'option', 'course', 'status', 'edit_time')
    list_per_page = 10
    actions_on_top = True
    actions_on_bottom = False
    save_on_top = True
    list_display_links = ('username',)
    list_editable = ('option_username', 'option', 'course', 'status', 'result')
    list_select_related = ('course',)


admin.site.register(Approval, ApprovalAdmin)


class UserImageAdmin(admin.ModelAdmin):
    list_display = ('username', 'image', 'data')
    list_filter = ('username', 'image', 'data')
    search_fields = ('username', 'image', 'data')
    list_per_page = 10
    actions_on_top = True
    actions_on_bottom = False
    save_on_top = True
    list_display_links = ('username',)
    list_editable = ('image', 'data')
    list_select_related = ()

    def delete_queryset(self,request, queryset):
        for obj in queryset:
            delete_face(f"image_id_{obj.id}")
        super().delete_queryset(request, queryset)


admin.site.register(UserImage, UserImageAdmin)
