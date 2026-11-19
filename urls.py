from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import AdminLoginView,dashboard,general_timetable,update_timetable,records,record_detail
urlpatterns=[
 path('login/',AdminLoginView.as_view(),name='login'),
 path('logout/',LogoutView.as_view(),name='logout'),
 path('',dashboard,name='dashboard'),
 path('general/',general_timetable,name='general'),
 path('update/',update_timetable,name='update'),
 path('records/',records,name='records'),
 path('records/<int:pk>/',record_detail,name='record_detail'),
]
