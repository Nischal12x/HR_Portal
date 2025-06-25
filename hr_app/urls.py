from django.contrib import admin
from django.urls import path
from . import views
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import JavaScriptCatalog
from django.contrib import admin

# Removed import of non-existing views update_employee, deactivate_employee, update_employee1
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .views import *
urlpatterns = [
    path('dashboardV2/', views.dashboard, name='dashboardV2'),
    path('deactivate_employee/<int:id>/', views.deactivate_employee, name='deactivate_employee'),
    path('update1/<int:id>',views.update_employee1, name='update_employee1' ),
    path('update/<int:id>/',views.update_employee, name='update_employee'),
    path("employee_records/", views.employee_list, name="employees"),
    path("add-emp/", views.add_employee, name="add-emp"),
    path("", views.admins, name="index"),
    path("a", views.apply_leave, name="apply_leave"),
    path('apply-leave/', views.index2, name = 'index2'),
    path('dashboard_v3/', views.dash_v3, name = 'index3'),
    path('widgets/', views.widgets, name = 'widgets'),
    path('calendar/', views.calendar1, name = 'calendar'),
    path('gallery/', views.gallery, name = 'gallery'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name = 'register'),
    path('add_emp/', views.add_emp, name = 'add_employees'),
    path('login-/', views.check_cred, name='check_cred'),
    path('leave-dashboard/', views.leave_dashboard, name ='leave_dashboard'),
    path('log_in', views.custom_logout, name="log_out"),
    path('withdraw-leave/<int:leave_id>/', views.withdraw_leave, name='withdraw_leave'),
    path('leave-dashboard1/<int:val>/',views.leave_dashboard, name='leave_dashboard1'  ),
    path('update-leave-status/<int:applicant_id>/', views.update_leave_status, name='update_leave_status'),
    # for configuration
    path('payroll-setting/', views.payroll_setting, name='payroll_setting'),
    path('employee-salary/', views.employee_salary, name='employee_salary'),
    # path('employee/add/', views.add_employees, name='add_employees'),
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
    path('my-profile/', views.profile_view, name='my_profile'),
    path('holidays/', views.holiday_dashboard, name='holiday_dashboard'),
    path('holidays/add/', views.add_holiday, name='add_holiday'),
    path('holidays/delete/<int:pk>/', views.delete_holiday, name='delete_holiday'),
    path('holidays/json/', views.holiday_json, name='holiday_json'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('forgot-password/done/', views.forgot_password_done, name='forgot_password_done'),
    path('reset_password/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt'
    ), name='reset_password'),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),

    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
    path('api/employees/', api_employees),
    path('api/leaves/', api_leaves),
    path('api/projects/', api_projects),
    path('api/tasks/', api_tasks),
    path('api/timesheets/week/', api_timesheets_week),
    path('api/timesheets/upload/', api_timesheets_upload),
    path('api/reports/leave-types/', api_reports_leave_types),
    path('api/reports/timesheet-hours/', api_reports_timesheet_hours),
    path('resignation/status/', views.resignation_status, name='resignation_status'),
    path('exit/apply/', views.apply_resignation, name='apply_resignation'),
    path('exit/my-request/', views.view_my_exit_request, name='view_my_exit_request'),
    path('exit/withdraw/<int:request_id>/', views.withdraw_resignation, name='withdraw_resignation'),
    path('resignation_approval/<int:request_id>/', views.resignation_approval_view, name='resignation_approval'),
    # Reporting Manager URLs for Exit Management
    path('exit/team-requests/', views.manage_exit_requests_rm, name='manage_exit_requests_rm'),
    path('exit/approve-rm/<int:request_id>/', views.approve_reject_exit_rm, name='approve_reject_exit_rm'),

    # HR URLs for Exit Management
    path('exit/hr-manage/', views.manage_exit_requests_hr, name='manage_exit_requests_hr'),
    path('exit/hr-process/<int:request_id>/', views.process_exit_request_hr, name='process_exit_request_hr'),
    path('attendance/', views.attendance_overview, name='attendance_overview'),
    path('attendance/update/', views.update_attendance_status, name='update_attendance_status'),
    path('attendance/download/', views.download_attendance_csv, name='download_attendance_csv'),
    path('mark_absent/', views.mark_absent, name='mark_absent'),
    # inactive employees
    path('inactive_employees/', views.inactive_employees, name='inactive_employees'),
    path('activate_employee/<int:id>/', views.activate_employee, name='activate_employee'),
    #calendar
    path('calendar-page/', views.calendar_view, name='calendar_page'),  # URL for the main calendar page
    path('calendar/events/', views.get_events, name='get_calendar_events'),
    path('calendar/add_event/', views.add_event, name='add_calendar_event'),
    path('calendar/update_event/', views.update_event, name='update_calendar_event'),
    path('calendar/delete_event/', views.delete_event, name='delete_calendar_event'),
    # Payroll URLs
    path('salary/details/', views.salary_details_view, name='salary_details'),
    path('payroll/monthly-data/', views.monthly_payroll_data_view, name='monthly_payroll_data'),
    path('payroll/settings/main/', views.payroll_settings_main_view, name='payroll_settings_main'),
    path('salary/upload-csv/', views.upload_salary_csv_view, name='upload_salary_csv'),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path('payroll/download/<int:record_id>/', views.download_payslip_pdf, name='download_payslip_pdf'),
    path('payroll/email/<int:record_id>/', views.email_payslip, name='email_payslip'),
    path('employee/payslips/<int:employee_id>/', views.employee_payslip_list_by_id, name='employee_payslip_list_by_id'),
    path('exit/update-last-working-date/<int:exit_id>/', views.change_last_working_date, name='change_last_working_date'),
    path('payroll/email-all/', views.email_payslips_to_all, name='email_payslips_to_all'),
    path("learning/", learning_videos, name="learning_videos"),
    path('settings/', views.user_settings, name='user_settings'),
    path('notifications/', views.all_notifications, name='all_notifications'),
    path('employee/<int:employee_id>/edit/', views.edit_employee, name='edit_employee'),
    path('attendance/my-record/', views.my_attendance_view, name='my_attendance'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
