from django.contrib import admin
from django.urls import path
from . import views

from django.contrib import admin

from .views import update_employee, delete_employee, update_employee1
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('update1/<int:id>',update_employee1, name='update_employee1' ),
    path('update/<int:id>/',update_employee, name='update_employee'),
    path('employees/delete/<int:id>/', delete_employee, name='delete_employee'),
    path("employee_records/", views.employee_list, name="employees"),
    path("add-emp/", views.add_employee, name="add-emp"),
    path("", views.admins, name="index"),
    path("a", views.apply_leave, name="apply_leave"),
    path('apply-leave/', views.dash_v2, name = 'index2'),
    path('dashboard_v3/', views.dash_v3, name = 'index3'),
    path('widgets/', views.widgets, name = 'widgets'),
    path('calendar/', views.calendar, name = 'calendar'),
    path('gallery/', views.gallery, name = 'gallery'),
    path('login/', views.login , name = 'login' ),
    path('register/', views.register, name = 'register'),
    path('add_emp/', views.add_emp, name = 'add_employees'),
    path('login-/', views.check_cred, name='check_cred'),
    path('leave-dashboard/', views.leave_dashboard, name ='leave_dashboard'),
    path('log_in', views.logout_view, name="log_out"),
    path('withdraw-leave/<int:leave_id>/', views.withdraw_leave, name='withdraw_leave'),
    path('leave-dashboard1/<int:val>/',views.leave_dashboard, name='leave_dashboard1'  ),
    path('update-leave-status/<int:applicant_id>/', views.update_leave_status, name='update_leave_status'),
    # for configuration
    path('payroll-setting/', views.payroll_setting, name='payroll_setting'),
    path('employee-salary/', views.employee_salary, name='employee_salary'),
    # path('employee/add/', views.add_employees, name='add_employees'),
    path('leave-settings/', views.leave_settings, name='leave_settings'),
    path('holidays/', views.holiday_list, name='holiday_list'),
    path('upload-handbook/', views.upload_handbook, name='upload_handbook'),
    path('assets/', views.assets, name='assets'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
