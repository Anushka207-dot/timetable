
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from core import views

urlpatterns = [

    # Django Admin
    path('admin/', admin.site.urls),

    # Login
    path('', views.login_view, name='login'),

    # Registration
    path('principal-register/', views.principal_register, name='principal_register'),
    path('vice-principal-register/', views.vice_principal_register, name='vice_principal_register'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Teacher Management
    path('teachers/', views.teacher_management, name='teacher_management'),
    path('teachers/edit/<int:teacher_pk>/', views.edit_teacher, name='edit_teacher'),
    path('teachers/delete/<int:teacher_pk>/', views.delete_teacher, name='delete_teacher'),

    # Create Timetable
    path('create-timetable/', views.create_timetable, name='create_timetable'),

    # General Timetable
    path(
        'general-timetable/',
        TemplateView.as_view(template_name='general_timetable.html'),
        name='general_timetable'
    ),

    # Update Timetable
    path(
        'update-timetable/',
        TemplateView.as_view(template_name='update_timetable.html'),
        name='update_timetable'
    ),

    # Records
    path(
        'records/',
        TemplateView.as_view(template_name='records.html'),
        name='records'
    ),

    # Logout
    path('logout/', views.logout_view, name='logout'),
]
