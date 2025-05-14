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
    path('apply-leave/', views.index2, name = 'index2'),
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
    path('holidays/', views.holiday_list, name='holiday_list'),
    path('upload-handbook/', views.upload_handbook, name='upload_handbook'),path('get-employees/', views.get_filtered_employees, name='get_filtered_employees'),
    path('leave-settings/', views.leave_settings_view, name='leave_settings'),
    path('assets/', views.assets, name='assets'),
    path('add-leave/', views.add_leave, name='add_leave'),
    path('leaves_sys/', views.leaves_sys, name='leaves_sys'),
    path('edit/<int:leave_id>/', views.edit_leave, name='edit_leave'),
    path('edit-leave/', views.editing_leaves, name='editing_leaves'),
    path('leave-details/<int:leave_id>/', views.leave_details, name='leave_details'),
    path('toggle-leave-status/<int:leave_id>/', views.toggle_leave_status, name='toggle_leave_status'),
    path('add-project/', views.add_project, name='add_project'),
    path('project/<int:project_id>/', views.project, name='project'),
    path('update-project/<int:project_id>/', views.update_project, name='update_project'),
    path('add_project/<int:p_id>/', views.add_project, name='add_project'),
    path('task/', views.task, name='task'),
    path('task/<int:task_id>/', views.task, name='task'),
    path('tasks/', views.task_list, name='task_list'),
    path('get_team_members/<int:project_id>/', views.get_team_members, name='get_team_members'),
    path('update_task_status/', views.update_task_status, name='update_task_status'),
    path('task_detail/<int:task_id>/', views.task_detail, name='task_detail'),
    path('time_sheet/', views.add_weekly_timesheet, name='time_sheet'),
    path('weeklytimesheet_add/', views.add_weekly_timesheet, name='weeklytimesheet_add'),
    path('timesheet/view/', views.view_timesheet, name='view_timesheet'),
    path('last_week_timesheet/', views.add_last_week_timesheet, name='last_week_timesheet'),
    path('timesheet/daily/', views.add_daily_timesheet, name='add_daily_timesheet'),
    path('get_tasks_by_project/<int:project_id>/', views.get_tasks_by_project, name='get_tasks_by_project'),
    path('add_image_timesheet/', views.add_image_timesheet, name='add_image_timesheet'),
    path('timesheet_record/', views.timesheet_image_records, name='timesheet_image_records'),
    path('employee/<int:id>/history/', views.employee_history, name='employee_history'),
    path('projects/<int:project_id>/history/', views.project_history, name='project_history'),
    path('employee-handbook/', views.employee_handbook_view, name='employee_handbook'),
    path('acknowledge-handbook/', views.acknowledge_handbook, name='acknowledge_handbook'),
    path('handbook/manage/', views.manage_handbooks, name='manage_handbooks'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
