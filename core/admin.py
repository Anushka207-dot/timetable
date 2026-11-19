
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
        ('School Role', {'fields': ('role',)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('School Role', {'fields': ('role',)}),
    )

    list_display = ('username', 'email', 'role', 'is_staff')
from .models import Teacher

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        'teacher_id',
        'full_name',
        'email',
        'phone',
        'department',
        'subjects'
    )
    search_fields = ('teacher_id', 'full_name', 'department')