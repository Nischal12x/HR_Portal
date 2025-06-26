import re
from datetime import datetime, timezone, date, timedelta
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import models, transaction
from django.db import IntegrityError
from django.utils import timezone
from collections import defaultdict
from django.core.paginator import Paginator
from django.core.files.storage import FileSystemStorage
from django.db.models import Sum, Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.shortcuts import render, redirect
import csv
import io
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required # Optional
# from django.db import transaction # If you save multiple records atomically
# from .models import Employee, SalaryData # Import your actual models
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from .models import Project, AddEmployee, Timesheet, EmployeeHandbook, Notification  # Ensure these models are imported
from .forms import EmployeeForm
from .models import Role, AddEmployee, LeaveApplication, Leave_Type, Task, ProjectHistory
from django.views.decorators.csrf import csrf_exempt
from .models import Project
from django.utils.dateparse import parse_date

from .models import EmployeeHandbook, EmployeeHandbookAcknowledgement, AddEmployee, ActivityLog
import logging # Import Python's logging
# Assuming logging_utils.py is in the same app directory
from .logging_utils import log_user_action, get_user_logger

@login_required
def employee_handbook_view(request):
    employee_id = request.session.get('employee_id')
    name = request.session.get('name')

    if not employee_id:
        return JsonResponse({'error': 'User not logged in'}, status=401)

    handbook = EmployeeHandbook.objects.last()  # Latest uploaded handbook
    acknowledged = EmployeeHandbookAcknowledgement.objects.filter(
        employee_id=employee_id,
        handbook=handbook
    ).exists()
    employee_email = request.session.get('employee_email')
    if employee_id and employee_email:
        log_user_action(employee_id, employee_email, f"{name} Accessed the Handbook.")

    return render(request, 'Handbook.html', {
        'acknowledged': acknowledged,
        'handbook': handbook,
        'employee_name': name
    })


import json
@login_required
def acknowledge_handbook(request):
    employee_id = request.session.get('employee_id')
    try:
        employee = AddEmployee.objects.get(id=employee_id)
    except AddEmployee.DoesNotExist:
        messages.error(request, "Employee not found.")
        return redirect('login')
    if request.method == 'POST':
        employee_id = request.session.get('employee_id')

        if not employee_id:
            return JsonResponse({'error': 'User not logged in'}, status=401)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = {}

        handbook = EmployeeHandbook.objects.last()
        employee = get_object_or_404(AddEmployee, id=employee_id)

        obj, created = EmployeeHandbookAcknowledgement.objects.get_or_create(
            employee=employee,
            handbook=handbook
        )

        employee_email = request.session.get('employee_email')
        if employee_id and employee_email:
            log_user_action(employee_id, employee_email, f" {employee.full_name} Acknowledged the Handbook.")
        return JsonResponse({'status': 'Acknowledged', 'created': created})

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def manage_handbooks(request):
    employee_id = request.session.get('employee_id')
    try:
        employee = AddEmployee.objects.get(id=employee_id)
    except AddEmployee.DoesNotExist:
        messages.error(request, "Employee not found.")
        return redirect('login')
    if request.session.get('role') != 'HR':
        employee_id = request.session.get('employee_id')
        employee_email = request.session.get('employee_email')
        if employee_id and employee_email:
            log_user_action(employee_id, employee_email, "Unauthorized access !")
        return JsonResponse({'error': 'Access denied'}, status=403)

    if request.method == 'POST':
        title = request.POST.get('title')
        version = request.POST.get('version')
        file = request.FILES.get('file')

        if title and version and file:
            EmployeeHandbook.objects.create(
                title=title,
                version=version,
                file=file
            )
            employee_id = request.session.get('employee_id')
            employee_email = request.session.get('employee_email')
            if employee_id and employee_email:
                log_user_action(employee_id, employee_email, f"Added New Handbook.")
            return redirect('manage_handbooks')

    handbooks = EmployeeHandbook.objects.all().order_by('-uploaded_at')
    history = []

    for handbook in handbooks:
        acknowledgements = EmployeeHandbookAcknowledgement.objects.filter(handbook=handbook)
        history.append({
            'handbook': handbook,
            'ack_count': acknowledgements.count(),
            'acknowledged_employees': acknowledgements.select_related('employee')
        })

    return render(request, 'manage_handbooks.html', {
        'history': history
    })

@login_required
def update_project(request, project_id):
    employee_id = request.session.get('employee_id')
    try:
        employee = AddEmployee.objects.get(id=employee_id)
    except AddEmployee.DoesNotExist:
        messages.error(request, "Employee not found.")
        return redirect('login')
    project = get_object_or_404(Project, id=project_id)
    selected_team_member_ids = list(project.team_members.values_list('id', flat=True))
    context = {
        'leaders': AddEmployee.objects.filter(role_id=2),
        'admins': AddEmployee.objects.filter(role_id=1),
        'team_members': AddEmployee.objects.filter(role_id=3),
        'project': project,
        'selected_team_member_ids': selected_team_member_ids
    }
    return render(request, 'add_project.html', context)


from .models import Project, Task  # adjust import if needed
@login_required
def project(request, project_id):
    proj = get_object_or_404(Project, id=project_id)

    # Fetch only tasks associated with this project
    tasks = Task.objects.filter(project=proj)


    return render(request, 'project.html', {
        'proj': proj,
        'tasks': tasks
    })

@csrf_exempt

@login_required
def archive_project(request, project): # added request for log
    # Get the most recent history entry
    last_history = ProjectHistory.objects.filter(project=project).order_by('-created_at').first()

    # Update the 'until' field of the last history record
    if last_history and last_history.until is None:
        last_history.until = timezone.now()
        last_history.save()

    # Create new history record with current data
    ProjectHistory.objects.create(
        project=project,
        name=project.name,
        client=project.client,
        start_date=project.start_date,
        end_date=project.end_date,
        currency=project.currency,
        rate_status=project.rate_status,
        rate=project.rate,
        priority=project.priority,
        leader=project.leader,
        admin=project.admin,
        description=project.description,
        document=project.document,
        created_at=timezone.now(),
    )
    employee_id = request.session.get('employee_id')
    employee_email = request.session.get('employee_email')
    if employee_id and employee_email:
        log_user_action(employee_id, employee_email, f"Project {project.name} history updated")

@csrf_exempt
def add_project(request, p_id=0):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Get form data
        project_name = request.POST.get('project_name')
        client = request.POST.get('client_name')
        start_date = parse_date(request.POST.get('start_date'))
        end_date = parse_date(request.POST.get('end_date'))
        currency = request.POST.get('currency')
        rate_status = request.POST.get('rate_status')
        rate = request.POST.get('rate')
        priority = request.POST.get('priority')
        leader_id = request.POST.get('project_leader')
        admin_id = request.POST.get('admin')
        team_ids = request.POST.getlist('team_members')
        description = request.POST.get('description')
        document = request.FILES.get('file_upload')

        errors = {}
        # Validation
        if not project_name:
            errors['project_name'] = "Project name is required."
        if not client:
            errors['client_name'] = "Client name is required."
        if not start_date:
            errors['start_date'] = "Start date is required."
        if not end_date:
            errors['end_date'] = "End date is required."
        if start_date and end_date and start_date > end_date:
            errors['start_date'] = "Start date cannot be after end date."  # assign to actual form field
        if not leader_id:
            errors['project_leader'] = "Project leader is required."
        if not admin_id:
            errors['admin'] = "Project admin is required."
        if project_name and Project.objects.filter(name__iexact=project_name).exists() and p_id == 0:
            errors['project_name'] = "A project with this name already exists."

        # Rate validation
        if rate:
            try:
                rate = float(rate)
            except ValueError:
                errors['rate'] = "Rate must be a valid number."

        if errors:
            print("FORM VALIDATION ERRORS:", errors)
            return JsonResponse({'success': False, 'errors': errors}, status=400)

        # Create or update project
        if p_id:
            project = get_object_or_404(Project, id=p_id)

        else:
            project = Project()

        # Save the project data (must be saved before setting many-to-many relationships)
        project.name = project_name
        project.client = client
        project.start_date = start_date
        project.end_date = end_date
        project.currency = currency
        project.rate_status = rate_status
        project.rate = rate if rate else None
        project.priority = priority
        project.leader_id = leader_id
        project.admin_id = admin_id
        project.description = description
        project.document = document
        project.save()  # Save project before setting team_members

        # Now you can safely assign the many-to-many relationship
        project.team_members.set(team_ids)
        project.save()  # Make sure to save again after updating the many-to-many field

        # Add to project history (on both create and update)
        archive_project(request, project)
        # Success response for AJAX
        employee_id = request.session.get('employee_id')
        employee_email = request.session.get('employee_email')
        if employee_id and employee_email:
            log_user_action(employee_id, employee_email, f"Project {project.name} accessed or modified.")
        if p_id != 0 :
            if employee_id and employee_email:
                log_user_action(employee_id, employee_email, f"Project {project} Updated")
            return JsonResponse({'success': True, 'message': "Project Updated successfully!"})
        if employee_id and employee_email:
            log_user_action(employee_id, employee_email, f"Project {project} with {p_id} Added")
        return JsonResponse({'success': True, 'message': "Project saved successfully!"})

    # Context for the form (used in the template)
    context = {
        'leaders': AddEmployee.objects.filter(role_id=2),
        'admins': AddEmployee.objects.filter(role_id=1),
        'team_members': AddEmployee.objects.filter(role_id=3),
    }
    return render(request, 'add_project.html', context)

@login_required
def project_history(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    history_qs = ProjectHistory.objects.filter(project=project).order_by('-created_at')

    paginator = Paginator(history_qs, 10)  # 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    employee_id = request.session.get('employee_id')
    employee_email = request.session.get('employee_email')
    if employee_id and employee_email:
        log_user_action(employee_id, employee_email, f"Accessed Project History of {project}.")
    context = {
        'project': project,
        'page_obj': page_obj,
        'total_pages': paginator.num_pages,
    }
    return render(request, 'project_history.html', context)
@login_required
def toggle_leave_status(request, leave_id):
    if request.method == "POST":
        leave = get_object_or_404(Leave_Type, id=leave_id)
        leave.is_active = not leave.is_active
        leave.save()
        messages.success(request, f"{leave.leavetype} has been {'activated' if leave.is_active else 'deactivated'}.")
        employee_id = request.session.get('employee_id')
        employee_email = request.session.get('employee_email')
        if employee_id and employee_email:
            log_user_action(employee_id, employee_email, f"{leave.leavetype} has been {'activated' if leave.is_active else 'deactivated'}")
    return redirect('leaves_sys')
@login_required
def leave_details(request, leave_id):
    leave = get_object_or_404(Leave_Type, id=leave_id)
    employee_id = request.session.get('employee_id')
    employee_email = request.session.get('employee_email')
    if employee_id and employee_email:
        log_user_action(employee_id, employee_email, f"Accessed {leave} related employees.")
    applications = LeaveApplication.objects.filter(
        leave_type=leave.id,
        status='Approved'
    ).select_related('employee').order_by('-id')

    # Prepare the data for display
    data = []
    for app in applications:
        employee = app.employee
        total_availed = LeaveApplication.objects.filter(
            employee=employee,
            leave_type=leave,
            status='Approved'
        ).aggregate(total=Sum('leave_days'))['total'] or 0

        leave_balance = float(leave.leave_time) - total_availed

        data.append({
            "employee_name": employee.full_name,
            "accrual": f"{leave.leave_time} {leave.leave_time_unit}/ Yearly",
            "effective": leave.effective_after,
            "effective_from": leave.from_date_reference,
            "weekend_leave": leave.count_weekends,
            "holiday_leave": leave.count_holidays,
            "leave_balance": leave_balance,
            "leave_availed": app.leave_days,
        })

    # Pagination
    paginator = Paginator(data, 10)  # 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'leave_details.html', {
        'leave': leave,
        'page_obj': page_obj,
    })

@login_required
def edit_leave(request, leave_id):
    leave = get_object_or_404(Leave_Type, id=leave_id)
    departments = AddEmployee.objects.values_list('department', flat=True).distinct()
    employee = None
    if leave.applied_to != 'All':
        try:
            employee = AddEmployee.objects.get(id=leave.applied_to)
        except AddEmployee.DoesNotExist:
            pass

    context = {
        'leave': leave,
        'employee': employee,
        'departments': departments
    }
    return render(request, 'leave_settings.html', context)

from django.shortcuts import get_object_or_404
@login_required
def editing_leaves(request):
    if request.method == 'POST':
        leave_name = request.POST.get('leaveName')
        leave_code = request.POST.get('code')
        code = leave_code
        leave_type_val = request.POST.get('leaveType')
        applied_to = request.POST.get('employeeType')

        gender = request.POST.get('gender') if applied_to == 'individual' else None
        marital_status = request.POST.get('maritalStatus') if applied_to == 'individual' else None
        department = request.POST.get('department') if applied_to == 'individual' else None
        employee_id = request.POST.get('employee') if applied_to == 'individual' else None

        effective_after = request.POST.get('effective_after') or 0
        time_unit = request.POST.get('time_unit')
        from_field = request.POST.get('from_field')
        custom_date = request.POST.get('custom_date')

        from_date_reference = custom_date if from_field == "custom_date" else "date_of_joining"
        accrual_enabled = True if request.POST.get('accrual_enabled') == 'on' else False
        leave_time = request.POST.get('leave_time') or 0
        leave_time_unit = request.POST.get('leave_time_unit')
        accrual_frequency = request.POST.get('accrual_frequency')

        count_weekends = True if request.POST.get('count_weekends') == 'True' else False
        count_holidays = True if request.POST.get('count_holidays') == 'True' else False

        # Fetch existing leave by code or name (choose based on your model)
        try:
            leave_obj = Leave_Type.objects.get(leave_code=leave_code)
        except Leave_Type.DoesNotExist:
            messages.error(request, "Leave entry not found.")
            return redirect('leave_settings')

        old_leave_name = leave_obj.leavetype

        leave_obj.leavetype = leave_name
        leave_obj.leave_code = code
        leave_obj.leave_privilege = leave_type_val
        leave_obj.applied_to = applied_to
        leave_obj.gender = gender
        leave_obj.marital_status = marital_status
        leave_obj.department = department
        leave_obj.employee = AddEmployee.objects.filter(id=employee_id).first() if employee_id else None

        leave_obj.effective_after = effective_after
        leave_obj.time_unit = time_unit
        leave_obj.from_date_reference = from_date_reference
@login_required
def leave_dashboard(request, val=0):
    applicants = LeaveApplication.objects.all()
    applicants = applicants.order_by('-id')  # to reverse the order
    leave_type = Leave_Type.objects.all()
    today = timezone.now().date()
    return render(request,"leave_dashboard.html", {"applicants" : applicants, "val": val, "leave_type" : leave_type, 'today' : today})  # Adjust for actual user system

from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import datetime
from .models import AddEmployee, Leave_Type, LeaveApplication
@login_required
def apply_leave(request):
    employee_id = request.session.get('employee_id')
    if not employee_id:
        messages.error(request, "You must be logged in to apply for leave.")
        return redirect('login')  # or your login view

    try:
        employee = AddEmployee.objects.get(id=employee_id)
    except AddEmployee.DoesNotExist:
        messages.error(request, "Employee not found.")
        return redirect('login')

    leaves = Leave_Type.objects.all()

    if request.method == "POST":
        from_date_str = request.POST.get('from_date')
        till_date_str = request.POST.get('till_date')
        from_date = datetime.strptime(from_date_str, "%Y-%m-%d").date()
        till_date = datetime.strptime(till_date_str, "%Y-%m-%d").date()

        reason = request.POST.get('reason', '').strip()
        leave_type = request.POST.get("leave_type", '').strip()
        attachment = request.FILES.get('attachment')
        compensation = request.POST.get("Compensatory")
        # Half-day data
        half_day_map = {}
        for key, value in request.POST.items():
            if key.startswith('half_day_status_'):
                date_str = key.replace('half_day_status_', '')
                half_day_map[date_str] = value

        if from_date > till_date:
            messages.error(request, "From date cannot be after till date.")
            return redirect('index2')

        leave = LeaveApplication(
            employee=employee,
            leave_type_id=leave_type,
            from_date=from_date,
            till_date=till_date,
            reason=reason,
            attachment=attachment
        )
        lt = Leave_Type.objects.get(id=leave_type)
        leave_days = leave.save(half_day_map=half_day_map, sandwich=lt.count_weekends)
        employee_id = request.session.get('employee_id')
        employee_email = request.session.get('employee_email')
        if compensation == '1' :
            if employee_id and employee_email:
                log_user_action(employee_id, employee_email, f"Applied Compensation Leave for {leave_days}")
            pass
        else :
            if lt.count_holidays == 1:
                # Fetch all holiday dates into a set for fast lookup
                holiday_dates = set(Holiday.objects.values_list('date', flat=True))

                # Iterate through date range and subtract holidays
                current_date = leave.from_date
                while current_date <= leave.till_date:
                    if current_date in holiday_dates:
                        leave_days -= 1
                    current_date += timedelta(days=1)

            leave.leave_days = leave_days
        leave.save()
        if employee_id and employee_email:
            (employee_id, employee_email, f"Applied Leave for {leave_days}")
        messages.success(request, "Leave applied successfully!")
        return redirect('index')

import re
from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import AddEmployee, Role
from .forms import EmployeeForm
@login_required
def add_employee(request):
    employee_id = request.session.get('employee_id')
    context = {
        'roles': Role.objects.all(),
        'designation_options': AddEmployee.DESIGNATION_CHOICES,  # <-- Add this
        'today': timezone.now().date(),
    }
    try:
        employee = AddEmployee.objects.get(id=employee_id)
    except AddEmployee.DoesNotExist:
        messages.error(request, "Employee not found.")
        return redirect('login')
    if request.method == "POST":

        roles = Role.objects.all()
        # Extract form data
        form_data = {
            "full_name": request.POST.get("full_name", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "phone": request.POST.get("phone", "").strip(),
            "dob": request.POST.get("dob", "").strip(),
            "gender": request.POST.get("gender", "").strip(),
            "address": request.POST.get("address", "").strip(),
            "password": request.POST.get("password", "").strip(),
            "department": request.POST.get("department", "").strip(),
            "designation": request.POST.get("designation", "").strip(),
            "joining_date": request.POST.get("joining_date", "").strip(),
            "salary": request.POST.get("salary", "").strip(),
            "employment_type": request.POST.get("employment_type", "").strip(),
            "employee_id" : request.POST.get("employee_id", "").strip(),
            'role': request.POST.get('role', '')
        }
        attachment = request.FILES.get("attachment")

        # Initialize error flags
        errors = {}

        # **Validations**
        if not form_data["full_name"]:
            errors["full_name"] = "Full Name is required."
        elif not re.match(r'^[A-Za-z\s]+$', form_data["full_name"]):
            errors["full_name"] = "Name should only contain alphabets and spaces."

        if not form_data["email"]:
            errors["email"] = "Email is required."
        elif not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.(com|org|net|edu|gov|mil|biz|info|co|in|us|uk|io|me)$',
                          form_data["email"]):
            errors["email"] = "Invalid email format. Please enter a valid email like example@domain.com."
        elif AddEmployee.objects.filter(email=form_data["email"]).exists():
            errors["email"] = "Email already exists."

        if not form_data["phone"]:
            errors["phone"] = "Phone number is required."
        elif not re.fullmatch(r'^[0-9]{10}$', form_data["phone"]):
            errors["phone"] = "Invalid phone number. Must be exactly 10 digits."
        elif AddEmployee.objects.filter(phone=form_data["phone"]).exists():
            errors["phone"] = "Phone number already exists."

        if not form_data["dob"]:
            errors["dob"] = "Date of Birth is required."
        else:
            try:
                dob = datetime.strptime(form_data["dob"], "%Y-%m-%d")
                age = (datetime.today() - dob).days // 365
                if age < 18:
                    errors["dob"] = "Employee must be at least 18 years old."
            except ValueError:
                errors["dob"] = "Invalid date format. Use YYYY-MM-DD."



        password = form_data.get("password", "").strip()

        if not password:
            errors["password"] = "Password is required."
        elif len(password) < 8:
            errors["password"] = "Password must be at least 8 characters long."
        elif not re.search(r'\d', password):
            errors["password"] = "Password must contain at least one number."
        else:
            form_data["password"] = password  # valid
        if not form_data["department"]:
            errors["department"] = "Department is required."
        if not form_data["designation"]:
            errors["designation"] = "Designation is required."
        if not form_data["joining_date"]:
            errors["joining_date"] = "Joining date is required."
        if not form_data["salary"]:
            errors["salary"] = "Salary is required."
        elif not form_data["salary"].isdigit():
            errors["salary"] = "Salary must be a valid number."
        else:
            salary_value = int(form_data["salary"])
            if salary_value < 10000 or salary_value > 100000:
                errors["salary"] = "Salary must be between 10,000 and 100,000."

        if not form_data["employment_type"]:
            errors["employment_type"] = "Employment type is required."

        # If errors exist, return with messages & form data
        if errors:
            today = timezone.now().date()
            return render(request, "add_emp.html", {
                "employee": form_data,
                "roles": roles,
                "today": today,
                "errors": errors,  # ✅ send field-wise errors
                'designation_options': AddEmployee.DESIGNATION_CHOICES,
            })

        # Save Employee if no errors
        emp = AddEmployee(
            full_name=form_data["full_name"], email=form_data["email"], phone=form_data["phone"],
            dob=form_data["dob"], gender=form_data["gender"], address=form_data["address"],
            employee_id=form_data["password"], department=form_data["department"],
            designation=form_data["designation"], joining_date=form_data["joining_date"],
            salary=form_data["salary"], employment_type=form_data["employment_type"],
            attachment=attachment, role_id = request.POST.get('role')
        )
        print(emp.employee_id)
        user = User.objects.create_user(username=form_data['full_name'], email=form_data['email'], password=form_data['password'])
        emp.user = user
        emp.save()
        # Create new history with current employee data
        employee = get_object_or_404(AddEmployee, id=emp.id)
        EmployeeHistory.objects.create(
            employee=employee,
            full_name=employee.full_name,
            email=employee.email,
            phone=employee.phone,
            nationality=employee.nationality,
            dob=employee.dob,
            role=employee.role,
            marital_status=employee.marital_status,
            gender=employee.gender,
            address=employee.address,
            employee_id=employee.id,
            department=employee.department,
            designation=employee.designation,
            joining_date=employee.joining_date,
            salary=employee.salary,
            employment_type=employee.employment_type,
            attachment=employee.attachment,
            created_at=now(),
            until=None  # this remains null until next update
        )
        employee_id = request.session.get('employee_id')
        employee_email = request.session.get('employee_email')
        if employee_id and employee_email:
            log_user_action(employee_id, employee_email, f" Employee with {emp.employee_id} added successfully!")
        messages.success(request, "Employee added successfully!")
        return redirect('index')

    return render(request, "add_emp.html", context)
@login_required
def employee_list(request):
    employees = AddEmployee.objects.filter(is_active=True)  # Fetch only active employees
    return render(request, "data.html", {"employees": employees})


# Update Employee
from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from django.utils.timezone import now
from datetime import datetime
import re

from .models import AddEmployee, EmployeeHistory

import re
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from .models import AddEmployee, Role, EmployeeHistory  # Make sure to import your models


# Corrected and Refactored View
@login_required
def update_employee(request, id):
    employee = get_object_or_404(AddEmployee, id=id)
    roles = Role.objects.all()

    if request.method == 'POST':
        # --- 1. Extract and Clean Form Data ---
        form_data = {
            "full_name": request.POST.get("full_name", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "phone": request.POST.get("phone", "").strip(),
            "dob": request.POST.get("dob", "").strip(),
            "gender": request.POST.get("gender", "").strip(),
            "marital_status": request.POST.get("marital_status", "").strip(),
            "address": request.POST.get("address", "").strip(),
            "password": request.POST.get("password", "").strip(),  # This is also the employee_id
            "department": request.POST.get("department", "").strip(),
            "designation": request.POST.get("designation", "").strip(),
            "joining_date": request.POST.get("joining_date", "").strip(),
            "salary": request.POST.get("salary", "").strip(),
            "employment_type": request.POST.get("employment_type", "").strip(),
            'role': request.POST.get('role', ''),
        }
        
        # File upload
        if 'attachment' in request.FILES:
            attachment = request.FILES['attachment']
            fs = FileSystemStorage()
            filename = fs.save(attachment.name, attachment)
            employee.attachment = filename
        print(employee.attachment)
        errors = {}

        # --- 2. Consolidated Validation Block ---

        # Password (Employee ID) Validation
        if not form_data["password"]:
            errors["password"] = "Password (Employee ID) is required."
        elif len(form_data["password"]) < 8:
            errors["password"] = "Password must be at least 8 characters long."
        elif not re.search(r'\d', form_data["password"]):
            errors["password"] = "Password must contain at least one number."

        # --- THE FIX: These validations are now correctly un-indented ---

        # Full Name Validation
        if not form_data["full_name"]:
            errors["full_name"] = "Full Name is required."
        elif not re.match(r'^[A-Za-z\s]+$', form_data["full_name"]):
            errors["full_name"] = "Name should only contain alphabets and spaces."

        # Email Validation (with improved uniqueness check for updates)
        if not form_data["email"]:
            errors["email"] = "Email is required."
        elif not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', form_data["email"]):
            errors["email"] = "Invalid email format."
        elif AddEmployee.objects.filter(email=form_data["email"]).exclude(id=id).exists():
            errors["email"] = "This email is already in use by another employee."

        # Phone Validation (with improved uniqueness check for updates)
        if not form_data["phone"]:
            errors["phone"] = "Phone number is required."
        elif not re.fullmatch(r'^[0-9]{10}$', form_data["phone"]):
            errors["phone"] = "Invalid phone number. Must be exactly 10 digits."
        elif AddEmployee.objects.filter(phone=form_data["phone"]).exclude(id=id).exists():
            errors["phone"] = "This phone number is already in use by another employee."

        # Date of Birth Validation
        if not form_data["dob"]:
            errors["dob"] = "Date of Birth is required."
        else:
            try:
                dob = datetime.strptime(form_data["dob"], "%Y-%m-%d").date()
                today = timezone.now().date()
                age = (today - dob).days // 365.25
                if dob > today:
                    errors["dob"] = "Date of Birth cannot be in the future."
                elif age < 18:
                    errors["dob"] = "Employee must be at least 18 years old."
            except ValueError:
                errors["dob"] = "Invalid date format. Use YYYY-MM-DD."

        # Other required field validations
        if not form_data["department"]: errors["department"] = "Department is required."
        if not form_data["designation"]: errors["designation"] = "Designation is required."
        if not form_data["joining_date"]: errors["joining_date"] = "Joining date is required."
        if not form_data["employment_type"]: errors["employment_type"] = "Employment type is required."

        # Salary Validation
        if not form_data["salary"]:
            errors["salary"] = "Salary is required."
        else:
            try:
                salary_value = float(form_data["salary"])
            except ValueError:
                errors["salary"] = "Salary must be a valid number."
            else:
                if salary_value < 10000 or salary_value > 100000:
                    errors["salary"] = "Salary must be between 10,000 and 100,000."


        # --- 3. Handle Validation Results ---
        if errors:
            # Re-render the form with errors and the data the user entered
            # Pass form_data back as 'employee' so the template can repopulate fields
            return render(request, "add_emp.html", {
                "employee": form_data,
                "roles": roles,
                "errors": errors,
                'designation_options': AddEmployee.DESIGNATION_CHOICES,
                'employee_attachment': employee.attachment,
                'employee_id' : id,
            })

        # --- 4. If No Errors, Proceed with Update ---

        # Close the previous history period
        last_history = EmployeeHistory.objects.filter(employee=employee).order_by('-created_at').first()
        if last_history and last_history.until is None:
            last_history.until = timezone.now()
            last_history.save()

        # Update employee object from validated form_data
        employee.full_name = form_data['full_name']
        employee.email = form_data['email']
        employee.phone = form_data['phone']
        employee.dob = form_data['dob']
        employee.gender = form_data['gender']
        employee.address = form_data['address']
        employee.department = form_data['department']
        employee.designation = form_data['designation']
        employee.joining_date = form_data['joining_date']
        employee.salary = form_data['salary']
        employee.employment_type = form_data['employment_type']
        employee.marital_status = form_data['marital_status']
        employee.role_id = form_data['role']
        employee.employee_id = form_data['password']  # Set the new Employee ID

        # Handle file upload
        if 'attachment' in request.FILES:
            attachment = request.FILES['attachment']
            fs = FileSystemStorage()
            filename = fs.save(attachment.name, attachment)
            employee.attachment = filename

        # Update linked User password
        if employee.user:
            employee.user.set_password(employee.employee_id)
            employee.user.save()

        employee.save()

        # Create new history record
        EmployeeHistory.objects.create(
            employee=employee,
            # ... (populate all fields for history as you did before)
            full_name=employee.full_name,
            email=employee.email,
            phone=employee.phone,
            dob=employee.dob,
            role=employee.role,
            gender=employee.gender,
            address=employee.address,
            department=employee.department,
            designation=employee.designation,
            joining_date=employee.joining_date,
            salary=employee.salary,
            # ... etc.
            created_at=timezone.now(),
            until=None,
        )

        messages.success(request, "Employee updated successfully!")
        return redirect('employees')

    # This is for the GET request (initial page load)
    return render(request, 'add_emp.html', {
        'employee': employee,
        'roles': roles,
        'designation_options': AddEmployee.DESIGNATION_CHOICES,
    })
@login_required
def employee_history(request, id):
    employee = get_object_or_404(AddEmployee, id=id)
    history_qs = EmployeeHistory.objects.filter(employee=employee).order_by('-created_at')

    paginator = Paginator(history_qs, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'employee_history.html', {
        'employee': employee,
        'page_obj': page_obj,
        'total_pages': paginator.num_pages,
    })
@login_required
def update_employee1(request, id) :
    # Get the employee object
    emp = get_object_or_404(AddEmployee, id=id)


    if request.method == 'POST':
        # Get the selected action from the form
        action = request.POST.get('action')

        # Based on the selected action, update the corresponding field
        if action == 'department':
            # Update the department
            new_department = request.POST.get('new_department')  # Assuming you have a field for the new department
            emp.department = new_department

        elif action == 'designation':
            # Update the designation
            new_designation = request.POST.get('new_designation')  # Assuming you have a field for the new designation
            emp.designation = new_designation

        elif action == 'salary':
            # Update the salary
            new_salary = request.POST.get('new_salary')  # Assuming you have a field for the new salary
            emp.salary = new_salary

        # Save the updated employee record
        emp.save()

        # Redirect to the employee detail page (or wherever you want)
        return redirect('employees')

        # In case the method is not POST, redirect to some default page
    roles = Role.objects.all()
    employee = get_object_or_404(AddEmployee, id=id)
    return render(request, 'add_emp.html',{'employee': employee, 'roles' : roles,
        'designation_options': AddEmployee.DESIGNATION_CHOICES,} )
# Delete Employee
@login_required
def deactivate_employee(request, id):
    employee = get_object_or_404(AddEmployee, id=id)
    if request.user.is_authenticated and hasattr(request.user, 'addemployee'):
        employee1 = request.user.addemployee
        log_user_action(employee1.id, employee1.email, f"{employee} deactivated ")
    employee.is_active = False
    employee.save()

    # Deactivate login access too
    if employee.user:
        employee.user.is_active = False
        employee.user.save()

    messages.success(request, "Employee deactivated successfully!")
    return redirect('employees')

@login_required
def activate_employee(request, id):
    employee = get_object_or_404(AddEmployee, id=id)
    if request.user.is_authenticated and hasattr(request.user, 'addemployee'):
        employee1 = request.user.addemployee
        log_user_action(employee1.id, employee1.email, f"{employee} activated ")
    employee.is_active = True
    employee.save()

    # Activate login access too
    if employee.user:
        employee.user.is_active = True
        employee.user.save()

    messages.success(request, "Employee activated successfully!")
    return redirect('inactive_employees')
@login_required
def inactive_employees(request):
    employees = AddEmployee.objects.filter(is_active=False)
    return render(request, "activate_employee.html", {"employees": employees})

from django.contrib.auth import authenticate, login

MAX_FAILED_ATTEMPTS = 3
LOCKOUT_DURATION_HOURS = 2


def check_cred(request):
    if request.method == "POST":
        email = request.POST.get("email", '').strip()
        password = request.POST.get("password", '').strip()
        ip_address = request.META.get('REMOTE_ADDR', 'N/A')  # Get IP address
        try:
            employee = AddEmployee.objects.get(email=email)
            user_logger = get_user_logger(employee.id, employee.email)  # Get logger instance

            # 1. Check if account is currently locked
            if employee.is_locked():
                remaining_time = employee.time_until_unlock()
                messages.error(request, f"Your account is locked. Please try again in approximately {remaining_time}.")
                msg = f"Account locked. Try again in {remaining_time}. IP: {ip_address}"
                log_user_action(employee.id, employee.email, f"Login attempt on locked account. IP: {ip_address}",
                                level=logging.WARNING)
                return redirect('login')

            # 2. Check if employee account is active
            if not employee.is_active:
                messages.error(request, "Your account has been deactivated.")
                log_user_action(employee.id, employee.email, f"Login attempt on deactivated account. IP: {ip_address}",
                                level=logging.WARNING)
                return redirect('login')

            # 3. Ensure linked User exists and is active
            if not employee.user or not employee.user.is_active:
                # This case implies an admin might have deactivated the Django User
                # or the link wasn't properly established.
                messages.error(request, "Login is not supported for this account or the linked user is inactive.")
                log_user_action(employee.id, employee.email,
                                f"Login attempt on account with no active linked user. IP: {ip_address}",
                                level=logging.WARNING)
                return redirect('login')

            user = employee.user  # Get the associated Django User

            # 4. Check password
            if user.check_password(password):
                # Successful login: reset failed attempts and lockout
                employee.failed_login_attempts = 0
                employee.lockout_until = None
                employee.save()

                # --- REPLACEMENT CODE ---

                if user.check_password(password):
                    # Successful login: reset failed attempts and lockout
                    employee.failed_login_attempts = 0
                    employee.lockout_until = None
                    employee.save()

                    # Login the Django User
                    login(request, user)
                    log_user_action(employee.id, employee.email, f"Login successful. IP: {ip_address}")

                    # --- Set up all session data in one clean block ---
                    request.session['is_logged_in'] = True
                    request.session['employee_id'] = employee.id
                    request.session['employee_email'] = employee.email
                    request.session['name'] = employee.full_name
                    request.session['designation'] = employee.designation
                    request.session['department'] = employee.department

                    # Correctly set the role name (as a string)
                    request.session['role'] = employee.role.name if employee.role else 'No Role Assigned'

                    # Correctly set the timesheet preference
                    request.session['timesheet_preference'] = employee.timesheet_preference

                    # Handle attachment if it exists
                    if employee.attachment:
                        request.session['attachment'] = employee.attachment.url

                    return redirect('index')

            # ... the rest of the view continues ...
            else:
                # Incorrect password: increment failed attempts
                employee.failed_login_attempts += 1
                if employee.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                    employee.lockout_until = timezone.now() + timedelta(hours=LOCKOUT_DURATION_HOURS)
                    # Optional: You might want to reset failed_login_attempts to 0 here
                    # or leave it, so an admin can see how many times it happened before lockout.
                    # For this logic, resetting is cleaner if the lockout itself is the state.
                    employee.failed_login_attempts = 0  # Reset for next cycle after lockout expires
                    employee.save()
                    msg = f"Incorrect password. Account locked for {LOCKOUT_DURATION_HOURS} hours. IP: {ip_address}"
                    messages.error(request,
                                   f"Incorrect password. Your account has been locked for {LOCKOUT_DURATION_HOURS} hours due to multiple failed attempts.")
                    log_user_action(employee.id, employee.email, msg, level=logging.WARNING)
                else:
                    employee.save()
                    remaining_attempts = MAX_FAILED_ATTEMPTS - employee.failed_login_attempts
                    msg = f"Incorrect password. {remaining_attempts} attempt(s) remaining. IP: {ip_address}"
                    messages.error(request,
                                   f"Incorrect password! You have {remaining_attempts} attempt{'s' if remaining_attempts > 1 else ''} remaining.")
                    log_user_action(employee.id, employee.email, msg, level=logging.INFO)
                # Optional: Log failed login attempt
                # print(f"Failed login attempt for {email} at {timezone.now()}. Attempt: {employee.failed_login_attempts}")
                return redirect('login')

        except AddEmployee.DoesNotExist:
            # To prevent username enumeration, you could log this attempt
            # but give a generic message to the user.
            # For simplicity here, we'll just show the message.
            # print(f"Login attempt for non-existent email: {email} at {timezone.now()}")
            messages.error(request, "Invalid email or password.")  # Generic message
            # messages.error(request, "Email does not exist!") # Specific message (as in original code)
            # Or, if you want to log this under a generic "system" user log:
            log_user_action("system", "N/A", f"Login attempt for non-existent email: {email}. IP: {ip_address}",
                            level=logging.INFO)
            return redirect('login')
    # GET request: generate fresh CSRF token
    get_token(request)
    return render(request, "login.html")


from django.contrib.auth import logout as auth_logout

@login_required
def custom_logout(request):
    if request.user.is_authenticated and hasattr(request.user, 'addemployee'):
        employee = request.user.addemployee
        log_user_action(employee.id, employee.email, "User logged out.")

    # Perform logout
    auth_logout(request)

    # Flush the session to clear all session data
    request.session.flush()

    # Optional: Set a new CSRF token to ensure freshness
    request.META["CSRF_COOKIE_USED"] = True

    # Success message
    messages.success(request, "You have been logged out.")
    return redirect('login')

from collections import defaultdict
from django.db.models import Sum
from django.utils import timezone
@login_required
def leaves_sys(request):
    leaves = Leave_Type.objects.all()
    employee_leave_data = defaultdict(list)
    leave_specific_data = {}

    for leave in leaves:
        applications = LeaveApplication.objects.filter(
            leave_type=leave.id,
            status='Approved'
        ).select_related('employee')

        for app in applications:
            employee = app.employee  # thanks to select_related
            total_availed = LeaveApplication.objects.filter(
                employee=employee,
                leave_type=leave,
                status='Approved'
            ).aggregate(total=Sum('leave_days'))['total'] or 0

            leave_balance = float(leave.leave_time) - total_availed

            employee_leave_data[leave.id].append({
                "employee_name": employee.full_name,
                "accrual": f"{leave.leave_time} {leave.leave_time_unit}/ Yearly",
                "effective": leave.effective_after,
                "effective_from": leave.from_date_reference,
                "weekend_leave": leave.count_weekends,
                "holiday_leave": leave.count_holidays,
                "leave_balance": leave_balance,
                "leave_availed": app.leave_days,
                "uploaded_on": employee.created_at if hasattr(employee, 'created_at') else timezone.now(),
                "application_date": app.created_at if hasattr(app, 'created_at') else timezone.now(),
                "leave_from": app.from_date,
                "leave_to": app.till_date,
            })

        leave_specific_data[leave.id] = applications

    return render(request, 'leaves_sys.html', {
        'leaves': leaves,
        'employee_leave_data': dict(employee_leave_data),
        'leave_specific_data': leave_specific_data
    })
@login_required
def logout_view(request):
    request.session.flush()  # Clears all session data
    messages.success(request, "You have been logged out successfully!")
    return redirect('login')  # Replace 'login_page' with the appropriate URL


# views.py
@login_required
def withdraw_leave(request, leave_id):
    leave = get_object_or_404(LeaveApplication, id=leave_id)

    # Optional: check if the current user owns the leave
    # if leave.employee.email == request.session.get('email') and leave.status == 'Pending':
    leave.status = 'Withdrawn'
    leave.save()

    return redirect('leave_dashboard')  # redirect to wherever the leave status is shown
@login_required
def update_leave_status(request, applicant_id):
    if request.method == 'POST':
        status = request.POST.get('status')
        applicant = get_object_or_404(LeaveApplication, id=applicant_id)

        if request.session.get('role') == 'HR':
            applicant.status = status

            # Record approver or canceller
            if status in ['Approved', 'Cancelled']:
                applicant.approved_by = request.session.get('name')  # or full_name/email
            else:
                applicant.approved_by = None  # Clear it if reverted to 'pending' or others

            applicant.save()
            return redirect("index")
        return redirect("leave_dashboard")
@login_required
def get_filtered_employees(request):
    gender = request.GET.get('gender')
    marital_status = request.GET.get('marital_status')
    department = request.GET.get('department')

    employees = AddEmployee.objects.all()

    if gender:
        employees = employees.filter(gender=gender.capitalize())
    if marital_status:
        employees = employees.filter(marital_status=marital_status.capitalize())
    if department:
        employees = employees.filter(department=department)

    employee_data = [{'id': emp.id, 'name': emp.full_name} for emp in employees]
    return JsonResponse({'employees': employee_data})
@login_required
def leave_settings_view(request):
    departments = AddEmployee.objects.values_list('department', flat=True).distinct()
    return render(request, 'leave_settings.html', {'departments': departments})
# Create your views here. # Adjust as per your actual model names

@login_required
def add_leave(request):
    if request.method == 'POST':
        # Extract fields from the POST data
        leave_name = request.POST.get('leaveName')
        leave_code = request.POST.get('code')
        leave_type = request.POST.get('leaveType')

        # Handle entitlement and restriction logic here
        effective_after = request.POST.get('effective_after')
        time_unit = request.POST.get('time_unit')
        accrual_enabled = request.POST.get('accrual_enabled') == 'on'  # Convert checkbox value
        leave_time = request.POST.get('leave_time')
        leave_time_unit = request.POST.get('leave_time_unit')
        accrual_frequency = request.POST.get('accrual_frequency')

        # Handle applicable users and restrictions
        gender = request.POST.get('gender')
        marital_status = request.POST.get('maritalStatus')
        department = request.POST.get('department')
        employee_id = request.POST.get('employee')
        from_field = request.POST.get('from_field')
        custom_date = request.POST.get('custom_date')
        employeeType = request.POST.get('employeeType')
        if not effective_after:
            effective_after = None
        # You might also need to check for custom_date and convert it if necessary
        if from_field == "custom_date" and custom_date:
            # Do something with the custom date
            pass
        from_value = from_field if from_field == "date_of_joining" else custom_date
        if employee_id:
            employee = AddEmployee.objects.get(id=employee_id)

        # Create a new Leave_Type object
        leave_type_instance = Leave_Type.objects.create(

            leavetype=leave_name,
            leave_code=leave_code,
            leave_privilege=leave_type,
            effective_after=effective_after,
            time_unit=time_unit,
            from_date_reference=from_value,
            accrual_enabled=accrual_enabled,
            leave_time=leave_time,
            leave_time_unit=leave_time_unit,
            accrual_frequency=accrual_frequency,
            count_weekends=True,  # or based on your logic
            count_holidays=True,  # or based on your logic
            applied_to = employee.id if employeeType == 'individual' and employee_id else 'All'
        )
        # If you're associating this leave type with an employee, you'd likely do something like:


        # After saving, you can redirect to a success page
        return redirect('leave_settings')  # Replace with the actual redirect URL

    return render(request, 'index.html')


# from .utils import calculate_remaining_leave  # Assuming the function is in utils.py
from django.db.models import F

from django.db.models import Sum
@login_required
def calculate_leave_details(request, leave):
    # Get the employee's session ID
    employee_id = request.session.get('employee_id')

    if not employee_id:
        return "Employee ID not found in session."

    # Get the leave type from the provided leave row (Leave_Type object)
    leave_type = leave # Leave_Type row is passed as an argument to the function

    # Get all approved leave applications for the employee for this leave type
    approved_leaves = LeaveApplication.objects.filter(
        employee_id=employee_id,
        leave_type=leave.id,
        status="Approved"
    )

    # Calculate total consumed leave days by summing up leave_days from approved leave applications
    total_consumed_leave = approved_leaves.aggregate(Sum('leave_days'))['leave_days__sum'] or 0

    # Initialize the remaining leave to the total leave_time for this leave type
    remaining_leave = leave_type.leave_time - total_consumed_leave

    # Convert remaining leave based on the time unit (Days or Months)
    if leave_type.leave_time_unit == 'Months':
        # If the time unit is Months, we may need to convert it to days (e.g., assuming 30 days per month)
        remaining_leave *= 30  # Assuming 30 days in a month for simplicity
        total_consumed_leave *= 30  # Also convert consumed leave days to days

    return total_consumed_leave, remaining_leave

from django.shortcuts import render
from .models import Leave_Type
# from .utils import calculate_leave_details  # Assuming the function is in utils.py
@login_required
def index2(request):
    # Get all leave types from the Leave_Type model
    leaves = Leave_Type.objects.filter(is_active=True)

    # Initialize a list to store the leave details (consumed and remaining)
    leave_details = []
    holiday_dates = list(Holiday.objects.values_list('date', flat=True))
    holiday_str_dates = [d.strftime("%Y-%m-%d") for d in holiday_dates]

    # Iterate over each leave type and calculate consumed and remaining leave
    for leave in leaves:
        total_consumed_leave, remaining_leave = calculate_leave_details(request, leave)
        leave_details.append({
            'leave_type': leave,
            'total_consumed_leave': total_consumed_leave,
            'remaining_leave': remaining_leave,
            'holiday_dates': holiday_str_dates,
        })

    # Pass the leave details to the template
    return render(request, 'index2.html', {'leave_details': leave_details})
@login_required
def admins(request):

    total_employees = AddEmployee.objects.count()
    total_projects = Project.objects.count()
    total_task = Task.objects.all().count()
    ongoing_tasks = Task.objects.exclude(status='Completed').count()
    total_holidays = Holiday.objects.count()
    employee_id = request.session.get('employee_id')
    if request.session.get('role') != 'HR' :
        total_projects = Project.objects.filter(
            Q(team_members__id=employee_id) |
            Q(leader__id=employee_id) |
            Q(admin__id=employee_id)
        ).distinct().count()

        ongoing_tasks = Task.objects.filter(
            ~Q(status='Completed'),
            Q(assignee__id=employee_id) |
            Q(project__leader__id=employee_id) |
            Q(project__admin__id=employee_id)
        ).distinct().count()

        total_task = Task.objects.filter(
            Q(assignee__id=employee_id) |
            Q(project__leader__id=employee_id) |
            Q(project__admin__id=employee_id)
        ).distinct().count()
    leaves = Leave_Type.objects.filter(
        is_active=True,
        applied_to__in=['All', employee_id]
    )

    # Initialize a list to store the leave details (consumed and remaining)
    leave_details = []

    # Iterate over each leave type and calculate consumed and remaining leave
    for leave in leaves:
        total_consumed_leave, remaining_leave= calculate_leave_details(request, leave)[:2]

        leave_details.append({
            'leave_type': leave,
            'total_consumed_leave': total_consumed_leave,
            'remaining_leave': remaining_leave
        })
    total_leaves = 0
    remaining_leaves = 0
    total_consumed_leaves = 0
    # for leave in leave_details:
    #     total_leaves += leave['total_consumed_leave']+leave['remaining_leave']
    #     remaining_leaves += leave['remaining_leave']
    #     total_consumed_leaves += leave['total_consumed_leave']
    for leave in leave_details:
        try:
            consumed = int(leave['total_consumed_leave'])
        except ValueError:
            print("Invalid consumed leave:", leave['total_consumed_leave'])
            consumed = 0

        try:
            remaining = int(leave['remaining_leave'])
        except ValueError:
            print("Invalid remaining leave:", leave['remaining_leave'])
            remaining = 0

        total_leaves += consumed + remaining
        remaining_leaves += remaining
        total_consumed_leaves += consumed
        leave_data = LeaveApplication.objects.values('leave_type__leavetype').annotate(count=Count('id'))
        leave_labels = [entry['leave_type__leavetype'] for entry in leave_data]
        leave_counts = [entry['count'] for entry in leave_data]

        timesheet_data = Timesheet.objects.values('project__name').annotate(
            total_hours=Sum(
                ExpressionWrapper(
                    F('end_time') - F('start_time'),
                    output_field=DurationField()
                )
            )
        )
        project_labels = [entry['project__name'] or "Unnamed" for entry in timesheet_data]
        project_hours = [round(entry['total_hours'].total_seconds() / 3600, 2) if entry['total_hours'] else 0 for entry
                         in timesheet_data]

    context = {
        'total_employees': total_employees,
        'total_projects': total_projects,
        'ongoing_tasks': ongoing_tasks,
        'remaining_leaves': remaining_leaves,
        'availed_leaves': total_consumed_leaves,
        'total_leaves': total_leaves,
        'total_holidays' : total_holidays,
        'total_task': total_task,
        'leave_labels': leave_labels,
        'leave_counts': leave_counts,
        'project_labels': project_labels,
        'project_hours': project_hours,
    }

    return render(request, 'index.html', context)
@login_required
def get_team_members(request, project_id):
    employee_id = request.session.get('employee_id')
    if request.session.get('role') == 'HR' :
        project = Project.objects.filter(id=project_id).prefetch_related('team_members').first()
    else :
        project = Project.objects.filter(
            id=project_id
        ).filter(
            models.Q(leader_id=employee_id) | models.Q(admin_id=employee_id)
        ).prefetch_related('team_members').first()
    if not project:
        return JsonResponse({'error': 'Unauthorized or project not found'}, status=403)

    members = [{'id': m.id, 'name': m.full_name} for m in project.team_members.all()]
    return JsonResponse({'members': members})
@login_required
def get_current_week_dates():
    # Get the current date
    today = datetime.today()
    # Calculate how many days back to Monday
    days_to_monday = today.weekday()  # Monday is 0 and Sunday is 6
    # Get the date of Monday of this week
    start_of_week = today - timedelta(days=days_to_monday)
    # Get the date of Sunday of this week
    end_of_week = start_of_week + timedelta(days=6)

    # Create a list of dates for each day of the week (Monday to Sunday)
    week_dates = {}
    for i in range(7):
        date = start_of_week + timedelta(days=i)
        week_dates[date.strftime('%A')] = date.strftime('%Y-%m-%d')  # Store as 'Monday', 'Tuesday', etc.

    return week_dates


from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import AddEmployee, Project, Task
@login_required
def add_weekly_timesheet(request):
    employee_id = request.session.get('employee_id')
    try:
        employee = AddEmployee.objects.get(id=employee_id)
    except AddEmployee.DoesNotExist:
        messages.error(request, "Employee record not found.")
        return redirect('login')

    today = timezone.now()
    start_of_week = today - timedelta(days=today.weekday())
    current_week_dates = {
        (start_of_week + timedelta(days=i)).strftime('%A'): (start_of_week + timedelta(days=i)).strftime('%Y-%m-%d')
        for i in range(7)
    }

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    errors = {}
    cleaned_data = {}

    if request.method == 'POST':
        for day in days:
            if day == 'Sunday' and not request.POST.get('description_sunday') and not request.FILES.get('attachment_sunday'):
                continue  # Only include Sunday if checkbox is clicked

            date = request.POST.get(f'date_{day}', '').strip()
            project_id = request.POST.get(f'project_{day}', '').strip()
            task_id = request.POST.get(f'task_{day}', '').strip()
            start_time = request.POST.get(f'start_time_{day}', '').strip()
            end_time = request.POST.get(f'end_time_{day}', '').strip()
            description = request.POST.get(f'description_{day}', '').strip()
            attachment = request.FILES.get(f'attachment_{day}')

            cleaned_data[day] = {
                'date': date,
                'project_id': project_id,
                'task_id': task_id,
                'start_time': start_time,
                'end_time': end_time,
                'description': description,
                'attachment': attachment,
            }

            # Skip if entire row is blank
            if not any([project_id, task_id, start_time, end_time, description, attachment]):
                continue

            errors[day] = {}

            if not project_id:
                errors[day]['project'] = 'Project is required.'
            elif not Project.objects.filter(id=project_id).exists():
                errors[day]['project'] = 'Project not found.'

            if not task_id:
                errors[day]['task'] = 'Task is required.'
            elif not Task.objects.filter(id=task_id).exists():
                errors[day]['task'] = 'Task not found.'

            if not start_time:
                errors[day]['start_time'] = 'Start time is required.'
            if not end_time:
                errors[day]['end_time'] = 'End time is required.'
            if start_time and end_time:
                try:
                    start = datetime.strptime(start_time, '%H:%M')
                    end = datetime.strptime(end_time, '%H:%M')
                    if end <= start:
                        errors[day]['end_time'] = 'End time must be after start time.'
                except ValueError:
                    errors[day]['start_end_time'] = 'Invalid time format.'

            if not description:
                errors[day]['description'] = 'Description is required.'

            if attachment and attachment.size > 5 * 1024 * 1024:
                errors[day]['file'] = 'File too large (max 5MB).'

            if not errors[day]:
                errors.pop(day)

        if errors:
            return render(request, 'Timesheet.html', {
                'employee': employee,
                'projects': Project.objects.all(),
                'tasks': Task.objects.all(),
                'days': days[:-1],
                'current_week_dates': current_week_dates,
                'errors': errors,
                'cleaned_data': cleaned_data,
            })

        # ✅ Save to DB after validation
        # Initialize the list to store skipped duplicate days
        skipped_days = []

        # Loop through each day's data and check for duplicates
        for day, data in cleaned_data.items():
            if not any([data['project_id'], data['task_id'], data['start_time'], data['end_time'], data['description'],
                        data['attachment']]):
                continue  # Skip if no data is provided

            # Duplicate check
            entry_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            project = Project.objects.get(id=data['project_id']) if data['project_id'] else None
            task = Task.objects.get(id=data['task_id']) if data['task_id'] else None

            # Check if a duplicate exists
            duplicate = Timesheet.objects.filter(
                employee=employee,
                date=entry_date,
                project=project,
                task=task
            ).exists()

            if duplicate:
                skipped_days.append(day)  # Add the day to skipped days
                continue  # Skip saving this entry

            # Save the valid timesheet entry if not a duplicate
            Timesheet.objects.create(
                employee=employee,
                day=day,
                date=entry_date,
                project=project,
                task=task,
                start_time=datetime.strptime(data['start_time'], '%H:%M').time(),
                end_time=datetime.strptime(data['end_time'], '%H:%M').time(),
                description=data['description'],
                attachment=data['attachment'] if data['attachment'] else None,
            )

        # If any days were skipped due to duplication, notify the user
        if skipped_days:
            skipped_days_str = ', '.join(skipped_days)
            messages.warning(request, f"The following days were skipped due to duplicate entries: {skipped_days_str}")
        else:
            messages.success(request, "Timesheet submitted successfully!")

        return redirect('view_timesheet')

    # Role-based filtering
    if employee.role_id == 1:
        projects = Project.objects.all()
        tasks = Task.objects.all()
    elif employee.role_id == 2:
        projects = Project.objects.filter(leader=employee)
        tasks = Task.objects.filter(project__leader=employee)
    else:
        projects = Project.objects.filter(team_members=employee)
        tasks = Task.objects.filter(assignee=employee)

    return render(request, 'Timesheet.html', {
        'employee': employee,
        'projects': projects,
        'tasks': tasks,
        'days': days[:-1],
        'current_week_dates': current_week_dates,
    })


@login_required
def task(request, task_id=0):
    employee_id = request.session.get('employee_id')
    employee = AddEmployee.objects.get(id=employee_id)
    print('i run',employee.role )
    # This is always needed — move it here
    if employee.role.name != 'Employee' and  employee.role.name != 'Project Manager' :
        print("123")
        projects = Project.objects.all()

    else :
        projects = Project.objects.filter(
            models.Q(leader_id=employee_id) |
            models.Q(admin_id=employee_id) |
            models.Q(team_members__id=employee_id)
        ).distinct()
        print(project for project in projects)

    if task_id != 0:
        task = get_object_or_404(Task, id=task_id)
        team_members = task.project.team_members.all() if task.project else []
    else:
        task = None
        team_members = []
    if request.method == 'POST':
        task_name = request.POST.get('task_name')
        project_id = request.POST.get('project_id')
        assignee_id = request.POST.get('assignee')
        priority = request.POST.get('priority')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        status = request.POST.get('status')
        description = request.POST.get('description')
        document = request.FILES.get('file_upload')
        #validations
        if not task_name:
            messages.error(request, "Task Name cannot be empty.")
            return redirect(request.path)

        if task:
            task.name = task_name
            task.project_id = project_id
            task.assignee_id = assignee_id
            task.priority = priority
            task.start_date = start_date
            task.end_date = end_date
            task.status = status
            task.description = description
            if document:
                task.document = document

            errors = []

            if start_date and end_date:
                try:
                    start = datetime.strptime(start_date, "%Y-%m-%d").date()
                    end = datetime.strptime(end_date, "%Y-%m-%d").date()

                    if start > end:
                        errors.append("End date must be after or equal to start date.")

                except ValueError:
                    errors.append("Invalid date format.")

            if errors:
                for error in errors:
                    messages.error(request, error)
                return render(request, 'add_task.html', {
                    'task': task,
                    'projects': projects,
                    'team_members': team_members
                })
            task.save()
            messages.success(request, "Task updated successfully.")
        else:
            Task.objects.create(
                name=task_name,
                project_id=project_id,
                assignee_id=assignee_id,
                priority=priority,
                start_date=start_date,
                end_date=end_date,
                status=status,
                description=description,
                document=document
            )
            messages.success(request, "Task created successfully.")
        return redirect('task_list')
    role = request.session.get('role')
    context = {
        'task': task,
        'projects': projects,
        'team_members': team_members,
        'role': role,
    }
    return render(request, 'add_task.html', context)
import json

@login_required
def update_task_status(request):
    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        status = request.POST.get('status')

        try:
            task = Task.objects.get(id=task_id)
            task.status = status
            task.created_at = timezone.now()
            task.save()
            return redirect('project', task.project_id )  # 👈 ensure 'project' matches your URL name


        except Task.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    task_id = request.GET.get('task_id')
    new_status = request.GET.get('status')

    task = get_object_or_404(Task, id=task_id)
    if new_status in dict(Task.STATUS_CHOICES):
        task.status = new_status
        task.save()

    return redirect('task_detail', task_id=task.id)

@login_required
def task_list(request):
    employee_id = request.session.get('employee_id')

    # Get all projects where user is leader or admin
    projects = Project.objects.filter(
        Q(leader_id=employee_id) | Q(admin_id=employee_id) | Q(team_members__id=employee_id)
    ).values_list('id', flat=True)

    # Get all tasks related to those projects
    role_id = request.session.get('role')
    if role_id == 'HR':  # Admin
        tasks = Task.objects.all()

    elif role_id == 'Employee':
        tasks = Task.objects.filter(
            assignee_id=employee_id
        )
    else :
        tasks = Task.objects.filter(project_id__in=projects).all().order_by('-id')  # you can adjust ordering
    paginator = Paginator(tasks, 10)  # Show 10 tasks per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'task_list.html', {'tasks': page_obj})

@login_required
@login_required
def task_detail(request, task_id):
    """
    Fetches the task and all necessary context for the detailed view template.
    """
    # 1. Get the main task object (this is the same as your original code)
    task = get_object_or_404(Task, id=task_id)

    # 2. Get all related activity logs for the timeline, newest first
    #    This is required for the "Activity & Comments" section in the template.
    activity_logs = task.activity_logs.all().order_by('-timestamp')

    # 3. Create the context dictionary with all the data the template needs
    context = {
        'task': task,
        'activity_logs': activity_logs,
        'request': request,  # 👈 This is crucial for checking the user's role in the template
    }

    # 4. Render the template with the complete context
    #    NOTE: Your error message showed 'task_detail.html', but your view had 'task_details.html'.
    #    Ensure the template filename here matches your actual file.
    return render(request, 'task_details.html', context)

@login_required
def dash_v3(request) :
    return render(request, 'index3.html')
@login_required
def widgets(request) :
    employee_id = request.session.get('employee_id')
    role_id = request.session.get('role')
    if role_id == 'HR':  # Admin
        projects = Project.objects.all()
    elif role_id == 'Project Manager':  # Leader
        projects = Project.objects.filter(leader_id=employee_id)
    else:  # Team Member
        projects = Project.objects.filter(team_members__id=employee_id)
    projects = projects.order_by('-id')
    paginator = Paginator(projects, 10)  # Show 10 projects per page
    page_number = request.GET.get('page')  # Get current page number
    page_obj = paginator.get_page(page_number)  # Get the page object
    return render(request, 'widgets.html', {'projects' : page_obj})
@login_required
def calendar1(request) :
    return render(request, 'calendar.html')

def gallery(request) :
    return render(request, 'gallery.html')
def login_view(request):
    return render(request, 'login.html')
def register(request) :
    return render(request, 'register.html')
def add_emp(request):
    roles = Role.objects.all()
    return render(request, 'add_emp.html', {"roles" : roles,
        'designation_options': AddEmployee.DESIGNATION_CHOICES,})
# for_configuration
@login_required
def payroll_setting(request):
    return render(request, 'configuration/payroll_setting.html')
@login_required
def employee_salary(request):
    return render(request, 'configuration/employee_salary.html')
@login_required
def add_employees(request):
    return render(request, 'configuration/add_employees.html')
@login_required
def leave_settings(request):
    return render(request, 'leave_settings.html')

@login_required
def upload_handbook(request):
    return render(request, 'configuration/upload_handbook.html')
@login_required
def assets(request):
    return render(request, 'configuration/assets.html')

@login_required
def view_timesheet(request):
    employee_id = request.session.get('employee_id')
    role = request.session.get('role')
    view_type = request.GET.get('view', 'self')
    search_query = request.GET.get('search', '').strip()

    if role == 'HR' and view_type == 'staff':
        timesheets = Timesheet.objects.exclude(employee__id=employee_id)

        if search_query:
            timesheets = timesheets.filter(
                Q(employee__id__icontains=search_query) |
                Q(employee__full_name__icontains=search_query)
            )
    else:
        timesheets = Timesheet.objects.filter(employee_id=employee_id)

    timesheets = timesheets.order_by('-date')

    # Calculate hours
    for entry in timesheets:
        if entry.start_time and entry.end_time:
            start = datetime.combine(entry.date, entry.start_time)
            end = datetime.combine(entry.date, entry.end_time)
            diff = end - start
            entry.hours = round(diff.total_seconds() / 3600, 2)
        else:
            entry.hours = None

    return render(request, 'Timesheet_records.html', {
        'timesheets': timesheets,
        'view_type': view_type,
        'search_query': search_query,
    })
@login_required
def add_last_week_timesheet(request):
    employee_id = request.session.get('employee_id')
    try:
        employee = AddEmployee.objects.get(id=employee_id)
    except AddEmployee.DoesNotExist:
        messages.error(request, "Employee not found.")
        return redirect('timesheet')

    today = timezone.now()
    start_of_last_week = today - timedelta(days=today.weekday() + 7)
    current_week_dates = {}

    for i in range(7):
        day = start_of_last_week + timedelta(days=i)
        current_week_dates[day.strftime('%A')] = day.strftime('%Y-%m-%d')

    # same logic as current week, reuse or refactor to DRY it
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    if employee.role_id == 1:
        projects = Project.objects.all()
        tasks = Task.objects.all()
    elif employee.role_id == 2:
        projects = Project.objects.filter(leader=employee)
        tasks = Task.objects.filter(project__leader=employee)
    else:
        projects = Project.objects.filter(team_members=employee)
        tasks = Task.objects.filter(assignee=employee)

    return render(request, 'Timesheet.html', {
        'projects': projects,
        'tasks': tasks,
        'employee': employee,
        'days': days,
        'current_week_dates': current_week_dates,
        'is_last_week': True,  # useful flag
    })
@login_required
def get_tasks_by_project(request, project_id):
    tasks = Task.objects.filter(project_id=project_id).values('id', 'name')
    return JsonResponse({'tasks': list(tasks)})

from django.utils.dateparse import parse_date
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Timesheet, Project, Task, AddEmployee
@login_required
def add_daily_timesheet(request):
    employee_id = request.session.get('employee_id')
    try:
        employee = AddEmployee.objects.get(id=employee_id)
    except AddEmployee.DoesNotExist:
        messages.error(request, "Employee not found.")
        return redirect('login')

    today = timezone.localdate()

    if request.method == 'POST':
        project_id = request.POST.get('project')
        task_id = request.POST.get('task')
        timesheet_date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        description = request.POST.get('description')
        attachment = request.FILES.get('attachment')

        errors = []

        if not project_id:
            errors.append("Project selection is required.")
        if not task_id:
            errors.append("Task selection is required.")
        if not timesheet_date:
            errors.append("Date is required.")
        if not start_time:
            errors.append("Start time is required.")
        if not end_time:
            errors.append("End time is required.")
        if not description:
            errors.append("Description is required.")
        if start_time and end_time and start_time >= end_time:
            errors.append("End time must be after start time.")

        if Timesheet.objects.filter(employee=employee, date=timesheet_date).exists():
            errors.append("A timesheet for this date already exists.")

        if not errors:
            try:
                project = Project.objects.get(id=project_id)
                task = Task.objects.get(id=task_id, project_id=project_id)
            except (Project.DoesNotExist, Task.DoesNotExist):
                errors.append("Invalid project or task.")

        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('view_timesheet')

        Timesheet.objects.create(
            employee=employee,
            project=project,
            task=task,
            date=timesheet_date,
            start_time=start_time,
            end_time=end_time,
            description=description,
            attachment=attachment,
            day=parse_date(timesheet_date).strftime('%A')
        )
        messages.success(request, "Timesheet submitted successfully.")
        return redirect('view_timesheet')

    # GET - show form
    if employee.role_id == 1:
        projects = Project.objects.all()
    elif employee.role_id == 2:
        projects = Project.objects.filter(leader=employee)
    else:
        projects = Project.objects.filter(team_members=employee)

    return render(request, 'Daily_Timesheet.html', {
        'projects': projects,
        'today': today.strftime('%Y-%m-%d'),
    })


from django.shortcuts import render
from .models import ImageTimesheet
#
# def add_image_timesheet(request):
#     today = datetime.today()
#     start_of_week = today - timedelta(days=today.weekday())  # Monday
#     end_of_week = start_of_week + timedelta(days=6)  # Sunday
#
#     # Last week's start and end dates
#     last_week_start = start_of_week - timedelta(days=7)
#     last_week_end = end_of_week - timedelta(days=7)
#
#     week_type = request.GET.get('week', 'current')  # Default to current week
#
#     if week_type == "last":
#         start_date = last_week_start
#         end_date = last_week_end
#     else:
#         start_date = start_of_week
#         end_date = end_of_week
#
#     return render(request, 'image_timesheet.html', {
#         'start_date': start_date.strftime('%Y-%m-%d'),
#         'end_date': end_date.strftime('%Y-%m-%d'),
#         'week_type': week_type,
#     })

from .models import ImageTimesheet
from django.contrib.auth.decorators import login_required
@login_required
def add_image_timesheet(request):
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday

    last_week_start = start_of_week - timedelta(days=7)
    last_week_end = end_of_week - timedelta(days=7)

    week_type = request.GET.get('week', 'current')

    if week_type == "last":
        start_date = last_week_start
        end_date = last_week_end
    else:
        start_date = start_of_week
        end_date = end_of_week

    if request.method == "POST":
        image = request.FILES.get('image')

        if not image:
            messages.error(request, "Please upload a valid image.")
            return redirect(request.path)

        # File validation (optional but recommended)
        if image.size > 5 * 1024 * 1024:
            messages.error(request, "File must be less than 5MB.")
            return redirect(request.path)

        valid_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
        if not any(image.name.lower().endswith(ext) for ext in valid_extensions):
            messages.error(request, "Invalid file type. Only jpg, jpeg, png, pdf allowed.")
            return redirect(request.path)

        try:
            employee_id = request.session.get('employee_id')
            employee = AddEmployee.objects.get(id=employee_id)

            ImageTimesheet.objects.create(
                employee=employee,
                start_date=start_date,
                end_date=end_date,
                image=image
            )

            messages.success(request, "Timesheet uploaded successfully.")
            return redirect('view_timesheet')  # Update this to your actual success view name
        except AddEmployee.DoesNotExist:
            messages.error(request, "Employee not found.")
            return redirect(request.path)

    return render(request, 'image_timesheet.html', {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'week_type': week_type,
    })

@login_required
def timesheet_image_records(request):
    employee_id = request.session.get('employee_id')
    role = request.session.get('role', '').lower()
    view_type = request.GET.get('view', 'self')  # default to own timesheet

    if not employee_id:
        return render(request, 'error.html', {"message": "Employee not found in session."})

    if role == 'hr':
        if view_type == 'staff':
            # HR sees others' records (excluding their own)
            timesheets = ImageTimesheet.objects.exclude(employee__id=employee_id)
        else:
            # HR views their own timesheet
            timesheets = ImageTimesheet.objects.filter(employee__id=employee_id)
    else:
        # Regular employee - only their own records
        timesheets = ImageTimesheet.objects.filter(employee__id=employee_id)

    return render(request, 'image_timesheet_records.html', {
        'timesheets': timesheets,
        'view_type': view_type
    })


@login_required
def profile_view(request):
    if not request.session.get('is_logged_in'):
        return redirect('check_cred')  # redirect if not logged in

    try:
        employee_id = request.session.get('employee_id')
        employee = AddEmployee.objects.get(id=employee_id)
    except AddEmployee.DoesNotExist:
        return redirect('check_cred')  # fallback if invalid

    # Fetch associated data
    leaves = LeaveApplication.objects.filter(employee=employee)
    projects = Project.objects.filter(
        models.Q(leader_id=employee_id) |
        models.Q(admin_id=employee_id) |
        models.Q(team_members__id=employee_id)
    )
    tasks = Task.objects.filter(
            assignee_id=employee_id
        )
    timesheets = Timesheet.objects.filter(employee=employee)

    context = {
        'employee': employee,
        'leaves': leaves,
        'projects': projects,
        'tasks': tasks,
        'timesheets': timesheets,
    }
    return render(request, 'Profile.html', context)


from .models import Holiday
@login_required
def holiday_dashboard(request):
    holidays = Holiday.objects.all().order_by('date')
    return render(request, 'holiday/holiday_dashboard.html', {'holidays': holidays})
@login_required
def add_holiday(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        date = request.POST.get('date')
        description = request.POST.get('description')
        Holiday.objects.create(name=name, date=date, description=description)
    return redirect('holiday_dashboard')
@login_required
def delete_holiday(request, pk):
    holiday = get_object_or_404(Holiday, pk=pk)
    holiday.delete()
    return redirect('holiday_dashboard')
@login_required
def holiday_json(request):
    holidays = Holiday.objects.all()
    events = []
    for holiday in holidays:
        events.append({
            'title': holiday.name,
            'start': holiday.date.isoformat(),
            'description': holiday.description,
        })
    return JsonResponse(events, safe=False)

from django.core.mail import send_mail  # or use django.core.mail.EmailMessage
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.urls import reverse

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if not email:
            messages.error(request, "Please enter your email.")
            return redirect('forgot_password')

        try:
            employee = AddEmployee.objects.get(email=email)

            # Ensure User is linked (create if missing)
            if not employee.user:
                # Create a corresponding user object
                username = email.split('@')[0]
                user = User.objects.create_user(username=username, email=email)
                employee.user = user
                employee.save()

            user = employee.user

            # Generate token and reset URL
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = request.build_absolute_uri(
                reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token}))

            # Email content
            subject = 'Password Reset Request'
            message = render_to_string('registration/password_reset_email.html', {
                'user': user,
                'reset_url': reset_url,
            })

            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
            messages.success(request, "Password reset instructions sent to your email.")
            return redirect('forgot_password_done')

        except AddEmployee.DoesNotExist:
            messages.error(request, "No account found with that email.")
            return redirect('forgot_password')

    return render(request, 'forgot_password.html')


def forgot_password_done(request):
    # Simple page to confirm email sent
    return render(request, 'forgot_password_done.html')
from django.db.models import Q, Count
from django.db.models import Count, Sum
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import F, ExpressionWrapper, DurationField
import json
@login_required
def dashboard(request):
    employee_id = request.session.get('employee_id')
    role = request.session.get('role')

    if not employee_id or not role:
        # Redirect to login or show error if session data missing
        return redirect('login')

    # Total employees count (for HR show all, else show count of accessible employees)
    if role == 'HR':
        total_employees = AddEmployee.objects.count()
        projects = Project.objects.all()
        tasks = Task.objects.all()
        leaves = LeaveApplication.objects.all()
    elif role == 'Project Manager':
        total_employees = AddEmployee.objects.filter(id=employee_id).count()
        projects = Project.objects.filter(leader_id=employee_id)
        tasks = Task.objects.filter(Q(project__leader_id=employee_id) | Q(project__admin_id=employee_id))
        leaves = LeaveApplication.objects.filter(employee_id=employee_id)
    else:
        total_employees = AddEmployee.objects.filter(id=employee_id).count()
        projects = Project.objects.filter(team_members__id=employee_id)
        tasks = Task.objects.filter(assignee_id=employee_id)
        leaves = LeaveApplication.objects.filter(employee_id=employee_id)

    # Pending leaves count for the user (or all if HR)
    if role == 'HR':
        pending_leaves = LeaveApplication.objects.filter(status='Pending').count()
    else:
        pending_leaves = LeaveApplication.objects.filter(employee_id=employee_id, status='Pending').count()

    # Total projects count based on role
    total_projects = projects.count()

    # Total tasks count based on role
    total_tasks = tasks.count()
    # ==== Chart Data ====
    # 1. Leave Types Distribution (pie chart)
    leave_type_data = LeaveApplication.objects.values('leave_type__leavetype').annotate(
        count=Count('id')
    )
    leave_labels = [entry['leave_type__leavetype'] for entry in leave_type_data]
    leave_counts = [entry['count'] for entry in leave_type_data]

    # Calculate total hours per project by subtracting start and end
    timesheet_data = Timesheet.objects.annotate(
        duration=ExpressionWrapper(
            F('end_time') - F('start_time'),
            output_field=DurationField()
        )
    ).values('project__name').annotate(
        total_duration=Sum('duration')
    )

    project_labels = [entry['project__name'] for entry in timesheet_data]
    project_hours = [
        round(entry['total_duration'].total_seconds() / 3600, 2) if entry['total_duration'] else 0
        for entry in timesheet_data
    ]

    context = {
        'total_employees': total_employees,
        'pending_leaves': pending_leaves,
        'total_projects': total_projects,
        'total_tasks': total_tasks,
        'projects': projects,
        'tasks': tasks,
        'leaves': leaves,
        'leave_labels': leave_labels,
        'leave_counts': leave_counts,
        'project_labels': project_labels,
        'project_hours': project_hours,
    }

    return render(request, 'dashboard.html', context)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Sum
@login_required
def api_employees(request):
    employee_id = request.session.get('employee_id')
    role = request.session.get('role')

    if role == 'HR':
        employees = AddEmployee.objects.all()
    else:
        employees = AddEmployee.objects.filter(id=employee_id)

    data = [{
        'id': emp.id,
        'full_name': emp.full_name,
        'email': emp.email,
        'department': emp.department,
        'designation': emp.designation,
    } for emp in employees]

    return JsonResponse(data, safe=False)
@login_required
def api_leaves(request):
    employee_id = request.session.get('employee_id')
    role = request.session.get('role')

    if role == 'HR':
        leaves = LeaveApplication.objects.all()
    else:
        leaves = LeaveApplication.objects.filter(employee_id=employee_id)

    data = [{
        'id': leave.id,
        'employee_name': leave.employee.full_name,
        'leave_type': leave.leave_type.leavetype if leave.leave_type else '',
        'from_date': leave.from_date.strftime('%Y-%m-%d') if leave.from_date else '',
        'till_date': leave.till_date.strftime('%Y-%m-%d') if leave.till_date else '',
        'status': leave.status,
        'reason': leave.reason,
    } for leave in leaves]

    return JsonResponse(data, safe=False)
@login_required
def api_projects(request):
    employee_id = request.session.get('employee_id')
    role = request.session.get('role')

    if role == 'HR':
        projects = Project.objects.all()
    elif role == 'Project Manager':
        projects = Project.objects.filter(leader_id=employee_id)
    else:
        projects = Project.objects.filter(team_members__id=employee_id)

    data = [{
        'id': project.id,
        'name': project.name,
        'status': getattr(project, 'status', 'N/A'),
        'priority': project.priority,
        'leader_name': project.leader.full_name if project.leader else '',
        'team_count': project.team_members.count(),
    } for project in projects]

    return JsonResponse(data, safe=False)
@login_required
def api_tasks(request):
    employee_id = request.session.get('employee_id')
    role = request.session.get('role')

    assignee_filter = request.GET.get('assignee')
    status_filter = request.GET.get('status')

    if role == 'HR':
        tasks = Task.objects.all()
    elif role == 'Project Manager':
        tasks = Task.objects.filter(
            Q(project__leader_id=employee_id) | Q(project__admin_id=employee_id)
        )
    else:
        tasks = Task.objects.filter(assignee_id=employee_id)

    if assignee_filter:
        tasks = tasks.filter(assignee_id=assignee_filter)
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    data = [{
        'id': task.id,
        'project_name': task.project.name if task.project else '',
        'name': task.name,
        'assignee_name': task.assignee.full_name if task.assignee else '',
        'status': task.status,
        'priority': task.priority,
    } for task in tasks]

    return JsonResponse(data, safe=False)
@login_required
def api_timesheets_week(request):
    employee_id = request.session.get('employee_id')
    role = request.session.get('role')

    from datetime import datetime, timedelta
    from django.utils import timezone

    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    if role == 'HR':
        timesheets = Timesheet.objects.filter(date__range=[start_of_week, end_of_week])
    else:
        timesheets = Timesheet.objects.filter(employee_id=employee_id, date__range=[start_of_week, end_of_week])

    # Group timesheets by date
    grouped = {}
    for ts in timesheets:
        day_name = ts.date.strftime('%A')
        date_str = ts.date.strftime('%Y-%m-%d')
        if date_str not in grouped:
            grouped[date_str] = {
                'date': date_str,
                'day': day_name,
                'entries': []
            }
        grouped[date_str]['entries'].append({
            'task_name': ts.task.name if ts.task else '',
            'hours': round((ts.end_time.hour + ts.end_time.minute/60) - (ts.start_time.hour + ts.start_time.minute/60), 2) if ts.start_time and ts.end_time else 0,
            'attachment': ts.attachment.url if ts.attachment else ''
        })

    data = list(grouped.values())
    return JsonResponse(data, safe=False)

@csrf_exempt
def api_timesheets_upload(request):
    if request.method == 'POST':
        employee_id = request.session.get('employee_id')
        if not employee_id:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        employee = AddEmployee.objects.get(id=employee_id)
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'error': 'No file uploaded'}, status=400)

        # Save the file as a Timesheet entry (simplified)
        Timesheet.objects.create(
            employee=employee,
            date=timezone.now().date(),
            description='Uploaded timesheet file',
            attachment=file
        )
        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Invalid method'}, status=405)
@login_required
def api_reports_leave_types(request):
    # Aggregate leave types count
    leave_counts = Leave_Type.objects.annotate(
        total=Count('leaveapplication')
    ).values('leavetype', 'total')

    labels = [item['leavetype'] for item in leave_counts]
    data = [item['total'] for item in leave_counts]

    return JsonResponse({'labels': labels, 'data': data})
@login_required
def api_reports_timesheet_hours(request):
    # Aggregate timesheet hours by project
    from django.db.models import F, ExpressionWrapper, DurationField
    from django.db.models.functions import ExtractHour, ExtractMinute

    timesheets = Timesheet.objects.all()
    project_hours = {}

    for ts in timesheets:
        if ts.start_time and ts.end_time:
            start = ts.start_time.hour + ts.start_time.minute / 60
            end = ts.end_time.hour + ts.end_time.minute / 60
            hours = end - start
            project_name = ts.project.name if ts.project else 'Unknown'
            project_hours[project_name] = project_hours.get(project_name, 0) + hours

    labels = list(project_hours.keys())
    data = [round(h, 2) for h in project_hours.values()]

    return JsonResponse({'labels': labels, 'data': data})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import AddEmployee, ExitRequest, Role  # Assuming Role model exists
from .forms import ResignationApplyForm, ExitChecklistForm, ExitApprovalFormRM, ExitApprovalFormHR
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Attendance, LeaveApplication, Holiday

# your_app/views.py

from datetime import datetime, timedelta
import calendar
import csv

from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Attendance, LeaveApplication, Holiday, AddEmployee


# Helper function for role check

def is_hr(user):
    # Replace this with your actual role checking logic
    try:
        return AddEmployee.objects.get(user=user)
    except AddEmployee.DoesNotExist:
        return None

    return user.is_authenticated and user.session.get('role') == 'HR'
    # Or if you have a profile model:
    # return user.is_authenticated and user.userprofile.role == 'HR'


@login_required
def attendance_overview(request):
    # --- 1. Get Date and Navigation ---
    try:
        month = int(request.GET.get('month', timezone.now().month))
        year = int(request.GET.get('year', timezone.now().year))
        # Prevent invalid month/year values
        if not (1 <= month <= 12):
            month = timezone.now().month
        current_date = datetime(year, month, 1)
    except (ValueError, TypeError):
        current_date = timezone.now()
        month = current_date.month
        year = current_date.year
        current_date = datetime(year, month, 1)

    # Calculate previous and next month/year for navigation links
    prev_month_date = current_date - timedelta(days=1)
    next_month_date = (current_date + timedelta(days=32)).replace(day=1)

    # --- 2. Efficient Data Fetching (Avoid N+1 queries) ---
    all_employees = AddEmployee.objects.filter(is_active=True).order_by('full_name')

    # Get all relevant records for the month in single queries
    holidays = set(Holiday.objects.filter(date__year=year, date__month=month).values_list('date', flat=True))

    leaves = LeaveApplication.objects.filter(
        status='Approved',
        from_date__year__lte=year,
        till_date__year__gte=year,
        from_date__month__lte=month,
        till_date__month__gte=month,
    )

    manual_attendance = Attendance.objects.filter(
        employee__in=all_employees,
        date__year=year,
        date__month=month
    )

    # Pre-process data into fast-lookup dictionaries
    leaves_map = {}
    for leave in leaves:
        current_date_in_leave = leave.from_date
        while current_date_in_leave <= leave.till_date:
            if current_date_in_leave.year == year and current_date_in_leave.month == month:
                if leave.employee.id not in leaves_map:
                    leaves_map[leave.employee.id] = set()
                leaves_map[leave.employee.id].add(current_date_in_leave)
            current_date_in_leave += timedelta(days=1)

    attendance_map = {(rec.employee.id, rec.date): rec.get_status_display() for rec in manual_attendance}

    # --- 3. Prepare Data for Template ---
    _, days_in_month = calendar.monthrange(year, month)
    days_with_weekdays = [
        {'day': day, 'weekday': calendar.day_name[datetime(year, month, day).weekday()][:3]}
        for day in range(1, days_in_month + 1)
    ]

    table_rows = []
    for employee in all_employees:
        statuses = []

        summary = {'P': 0, 'A': 0, 'L': 0, 'H': 0, 'W': 0}  # Present, Absent, Leave, Holiday, Weekend

        for day in range(1, days_in_month + 1):
            date = datetime(year, month, day).date()
            status_key = 'P'  # Default to Present

            # Logic is ordered by precedence
            if date > timezone.now().date():
                status_key = '-'  # Future date
            elif date in holidays:
                status_key = 'H'
            elif date.weekday() >= 5:  # Saturday or Sunday
                status_key = 'W'

            # Employee-specific checks
            if employee.id in leaves_map and date in leaves_map[employee.id]:
                status_key = 'L'

            # Manual attendance overrides everything
            if (employee.id, date) in attendance_map:
                status_display = attendance_map[(employee.id, date)]
                status_key = {
                    'Present': 'P',
                    'Absent': 'A',
                    'Leave': 'L',
                    'Holiday': 'H',
                    'Weekend': 'W'
                }.get(status_display, 'P')  # Default to 'P' if unknown
                if status_key != '-':
                    summary[status_key] = summary.get(status_key, 0) + 1

            # A day without any record that is not a weekend or holiday is an Absence
            # if status_key == 'P' and (employee.id, date) not in attendance_map:
            #     # This assumes no explicit 'Present' record is created.
            #     # If you have check-in/out, 'P' would come from there.
            #     # For a manual system, an unmarked day is Absent.
            #     status_key = 'A'

            statuses.append(status_key)
            if status_key != '-':
                summary[status_key] += 1

        table_rows.append({'employee': employee, 'statuses': statuses, 'summary': summary})

    # --- 4. Pagination ---
    paginator = Paginator(table_rows, 25)  # Show 25 employees per page
    page = request.GET.get('page')
    try:
        paginated_rows = paginator.page(page)
    except PageNotAnInteger:
        paginated_rows = paginator.page(1)
    except EmptyPage:
        paginated_rows = paginator.page(paginator.num_pages)

    context = {
        'paginated_rows': paginated_rows,
        'month': month,
        'year': year,
        'month_name': calendar.month_name[month],
        'days_in_month_with_weekdays': days_with_weekdays,
        'prev_month': prev_month_date.month,
        'prev_year': prev_month_date.year,
        'next_month': next_month_date.month,
        'next_year': next_month_date.year,
        'is_hr': is_hr(request.user),  # Pass HR status to template
        'legend': {
            'P': 'Present', 'A': 'Absent', 'L': 'Leave',
            'H': 'Holiday', 'W': 'Weekend'
        }
    }
    return render(request, 'attendance_overview.html', context)


@login_required
def update_attendance_status(request):
    """
    AJAX view to mark attendance. Restricted to HR.
    """
    if not is_hr(request.user):
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        try:
            employee_id = request.POST.get('employee_id')
            date_str = request.POST.get('date')
            status = request.POST.get('status', 'A').upper()  # Ensure uppercase like 'P', 'A', etc.

            valid_statuses = ['P', 'A', 'L', 'H', 'W']
            if status not in valid_statuses:
                return JsonResponse({'status': 'error', 'message': 'Invalid attendance status.'}, status=400)

            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            employee = AddEmployee.objects.get(id=employee_id)

            if date > timezone.now().date():
                return JsonResponse({'status': 'error', 'message': 'Cannot mark attendance for a future date.'}, status=400)

            attendance_record, created = Attendance.objects.update_or_create(
                employee=employee,
                date=date,
                defaults={'status': status}
            )

            return JsonResponse({
                'status': 'success',
                'message': f"Marked {employee.full_name} as '{attendance_record.get_status_display()}' on {date}.",
                'new_status': attendance_record.get_status_display()
            })

        except (ValueError, AddEmployee.DoesNotExist, TypeError):
            return JsonResponse({'status': 'error', 'message': 'Invalid data received.'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

# individual employee attendance
@login_required
def my_attendance_view(request):
    # --- Get the specific employee for the logged-in user ---
    try:
        employee = AddEmployee.objects.get(user=request.user, is_active=True)
    except AddEmployee.DoesNotExist:
        messages.error(request, "Your employee profile could not be found.")
        return redirect('index')  # Or your main dashboard URL

    # --- 1. Get Date and Navigation (This logic is the same) ---
    try:
        month = int(request.GET.get('month', timezone.now().month))
        year = int(request.GET.get('year', timezone.now().year))
        if not (1 <= month <= 12):
            month = timezone.now().month
        current_date = datetime(year, month, 1)
    except (ValueError, TypeError):
        current_date = timezone.now()
        month, year = current_date.month, current_date.year
        current_date = datetime(year, month, 1)

    prev_month_date = current_date - timedelta(days=1)
    next_month_date = (current_date + timedelta(days=32)).replace(day=1)

    # --- 2. Efficient Data Fetching (Filtered for one employee) ---
    holidays = set(Holiday.objects.filter(date__year=year, date__month=month).values_list('date', flat=True))
    leaves = LeaveApplication.objects.filter(
        employee=employee, status='Approved',
        from_date__month__lte=month, till_date__month__gte=month,
        from_date__year__lte=year, till_date__year__gte=year,
    )
    # Manual attendance is not needed if you assume unmarked days are Absent/Present
    # If you do need it for overrides:
    # attendance_map = {(rec.date): rec.get_status_display()
    #                   for rec in Attendance.objects.filter(employee=employee, date__year=year, date__month=month)}

    # Pre-process leaves into a fast-lookup set
    leaves_set = set()
    for leave in leaves:
        d = leave.from_date
        while d <= leave.till_date:
            if d.year == year and d.month == month:
                leaves_set.add(d)
            d += timedelta(days=1)

    # --- 3. Prepare Data for Template (For the single employee) ---
    _, days_in_month = calendar.monthrange(year, month)
    days_with_weekdays = [
        {'day': day, 'weekday': calendar.day_name[datetime(year, month, day).weekday()][:3]}
        for day in range(1, days_in_month + 1)
    ]

    statuses = []
    summary = {'P': 0, 'A': 0, 'L': 0, 'H': 0, 'W': 0}

    for day in range(1, days_in_month + 1):
        date = datetime(year, month, day).date()
        status_key = 'P'  # Default to Present

        if date > timezone.now().date():
            status_key = '-'
        elif date in holidays:
            status_key = 'H'
        elif date.weekday() >= 5:  # Saturday or Sunday
            status_key = 'W'
        elif date in leaves_set:
            status_key = 'L'
        # elif (date) in attendance_map and attendance_map[(date)] == 'Absent':
        #    status_key = 'A'
        # This is a simple model. An unmarked weekday is Present.
        # If you want to default to absent, change the default status_key to 'A'

        statuses.append(status_key)
        if status_key != '-':
            summary[status_key] += 1

    # We create a list with one item to match the structure the template expects
    table_row = [{'employee': employee, 'statuses': statuses, 'summary': summary}]

    context = {
        'table_row': table_row,  # Pass the single row of data
        'month': month,
        'year': year,
        'month_name': calendar.month_name[month],
        'days_in_month_with_weekdays': days_with_weekdays,
        'prev_month': prev_month_date.month,
        'prev_year': prev_month_date.year,
        'next_month': next_month_date.month,
        'next_year': next_month_date.year,
        'legend': {
            'P': 'Present', 'A': 'Absent', 'L': 'Leave',
            'H': 'Holiday', 'W': 'Weekend'
        }
    }
    return render(request, 'my_attendance.html', context)  # Render the new template

# your_app/views.py

@login_required
def download_attendance_csv(request):
    """
    View to download the attendance data for a given month/year as a CSV file.
    This version is corrected to handle future dates and provides a clean CSV output.
    """
    # --- 1. Get and Validate Date ---
    try:
        month = int(request.GET.get('month', timezone.now().month))
        year = int(request.GET.get('year', timezone.now().year))
        # Validate that the month and year form a real date
        datetime(year, month, 1)
    except (ValueError, TypeError):
        # Default to current month/year on invalid input
        current_time = timezone.now()
        month = current_time.month
        year = current_time.year

    # --- 2. Efficient Data Fetching (same as overview) ---
    all_employees = AddEmployee.objects.filter(is_active=True).order_by('full_name')
    holidays = set(Holiday.objects.filter(date__year=year, date__month=month).values_list('date', flat=True))
    leaves = LeaveApplication.objects.filter(
        status='Approved',
        from_date__year__lte=year,
        till_date__year__gte=year,
        from_date__month__lte=month,
        till_date__month__gte=month,
    )
    manual_attendance = Attendance.objects.filter(
        employee__in=all_employees,
        date__year=year,
        date__month=month
    )

    # Pre-process data into fast-lookup dictionaries
    leaves_map = {}
    for leave in leaves:
        d = leave.from_date
        while d <= leave.till_date:
            if d.year == year and d.month == month:
                if leave.employee.id not in leaves_map:
                    leaves_map[leave.employee.id] = set()
                leaves_map[leave.employee.id].add(d)
            d += timedelta(days=1)

    attendance_map = {(rec.employee.id, rec.date): rec.get_status_display() for rec in manual_attendance}

    # --- 3. CSV Generation ---
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_{year}-{month:02d}.csv"'

    writer = csv.writer(response)

    # Write header row
    _, days_in_month = calendar.monthrange(year, month)
    header = ['Employee Name', 'Employee ID'] + [str(d) for d in range(1, days_in_month + 1)] + ['Total Present',
                                                                                                 'Total Absent',
                                                                                                 'Total Leave',
                                                                                                 'Total Holiday',
                                                                                                 'Total Weekend']
    writer.writerow(header)

    # Write data rows for each employee
    for employee in all_employees:
        # Use getattr for safety in case employee_id field doesn't exist on the model
        employee_data_row = [employee.full_name, getattr(employee, 'employee_id', 'N/A')]

        daily_statuses = []
        summary = {'P': 0, 'A': 0, 'L': 0, 'H': 0, 'W': 0}

        for day in range(1, days_in_month + 1):
            date = datetime(year, month, day).date()
            status_key = 'A'  # Default to Absent for a working day

            # Determine status with clear precedence
            if date > timezone.now().date():
                status_key = '-'  # Future date, not counted in summary
            elif date in holidays:
                status_key = 'H'
            elif date.weekday() >= 5:  # Saturday or Sunday
                status_key = 'W'

            # Employee-specific overrides
            if employee.id in leaves_map and date in leaves_map[employee.id]:
                status_key = 'L'

            if (employee.id, date) in attendance_map:
                # Manual attendance overrides everything else
                status_key = attendance_map[(employee.id, date)]

            # A day that is not a weekend/holiday/leave and has no manual record is 'Absent'
            # Our default 'A' already covers this. If you had a check-in system,
            # you'd set default to 'A' and override with 'P' if a check-in exists.

            daily_statuses.append(status_key)

            # *** THE FIX IS HERE ***
            # Only increment the summary if the status_key is a valid counter.
            # This safely ignores '-', which would have caused a KeyError.
            if status_key in summary:
                summary[status_key] += 1

        # Now extend the row with the collected data
        employee_data_row.extend(daily_statuses)
        employee_data_row.extend([summary['P'], summary['A'], summary['L'], summary['H'], summary['W']])

        # Write the complete row to the CSV
        writer.writerow(employee_data_row)

    return response

@login_required
def mark_absent(request):
    if request.session.get('role') != 'HR':
        messages.error(request, "Unauthorized access.")
        return redirect('attendance_overview')

    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        date_str = request.POST.get('date')
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            employee = AddEmployee.objects.get(id=employee_id)
        except (ValueError, AddEmployee.DoesNotExist):
            messages.error(request, "Invalid data.")
            return redirect('attendance_overview')

        # Create or update attendance record as Absent
        attendance_record, created = Attendance.objects.update_or_create(
            employee=employee,
            date=date,
            defaults={'status': 'A'}
        )
        messages.success(request, f"Marked {employee.full_name} as absent on {date}.")
        return redirect('attendance_overview')

    # For GET request, show form to mark absent
    employees = AddEmployee.objects.filter(is_active=True).order_by('full_name')
    context = {
        'employees': employees,
        'today': timezone.now().date(),
    }
    return render(request, 'mark_absent.html', context)
from .models import Leave_Type

# Helper function (you might have this elsewhere)

def get_employee_profile(user):
    try:
        return AddEmployee.objects.get(user=user)
    except AddEmployee.DoesNotExist:
        return None


from django.contrib.auth.decorators import login_required
from django.utils import timezone
@login_required
def resignation_status(request):
    employee_id = request.session.get('employee_id')
    if not employee_id:
        messages.error(request, "Session expired. Please log in again.")
        return redirect('login')

    employee = AddEmployee.objects.get(id=employee_id)
    exit_request = ExitRequest.objects.filter(employee=employee).order_by('-created_at').first()

    return render(request, 'employee/resignation_status.html', {
        'employee': employee,
        'exit_request': exit_request
    })

from django.utils.dateparse import parse_date
from dateutil.relativedelta import relativedelta

from .models import ExitRequest

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
@login_required
def apply_resignation(request):
    employee_id = request.session.get('employee_id')
    if not employee_id:
        messages.error(request, "Session expired. Please log in again.")
        return redirect('login')

    employee = get_object_or_404(AddEmployee, id=employee_id)

    # Prevent duplicate requests
    if ExitRequest.objects.filter(employee=employee, status='PENDING_RM_APPROVAL').exists():
        messages.warning(request, "You have already submitted a resignation request.")
        return redirect('resignation_status')
    elif ExitRequest.objects.filter(employee=employee, status='PENDING_HR_APPROVAL').exists():
        messages.warning(request, "You Resignation is already Confirmed.")
        return redirect('resignation_status')
    elif ExitRequest.objects.filter(employee=employee, status='Approved').exists():
        messages.warning(request, "You Resignation is already Confirmed.")
        return redirect('resignation_status')

    if request.method == 'POST':
        print("POST received")  # Debug
        step = request.POST.get('resignation_submit_step')
        print("Step:", step)  # Debug

        if step == 'send_email':
            # Final submit: Save and send email
            resignation_apply_date = timezone.now().date()
            reason = request.POST.get('reason')
            subject = request.POST.get('subject')
            message_body = request.POST.get('message')
            selected_elsewhere = request.POST.get('selected_elsewhere') == 'yes'
            bond_over = request.POST.get('bond_over') == 'yes'
            advance_salary = request.POST.get('advance_salary') == 'yes'
            any_dues = request.POST.get('any_dues') == 'yes'
            to_email = request.POST.get('to')
            cc = request.POST.get('cc')
            bcc = request.POST.get('bcc')
            #Validate email
            if not to_email or not subject or not message_body:
                messages.error(request, "To, Subject, and Message fields are required.")
                return redirect('resignation_status')

            exit_request = ExitRequest.objects.create(
                employee=employee,
                resignation_apply_date=resignation_apply_date,
                reason_for_resignation=reason,
                selected_elsewhere=selected_elsewhere,
                bond_over=bond_over,
                advance_salary=advance_salary,
                any_dues=any_dues,
                status='PENDING_RM_APPROVAL',
                company_assets_returned=False,
                email_subject=subject
            )

            email = EmailMessage(
                subject=subject,
                body=message_body,
                from_email=employee.email,
                to=[to_email],
                cc=[cc] if cc else [],
                bcc=[bcc] if bcc else [],
            )
            email.content_subtype = "html"
            email.send()

            messages.success(request, "Resignation request submitted and email sent.")
            return redirect('resignation_status')

        elif step == 'show_email_form':
            # Intermediate step: show email form with pre-filled data
            context = {
                'employee': employee,
                'reason': request.POST.get('reason'),
                'resignation_apply_date': request.POST.get('resignation_apply_date'),
                'last_working_date': request.POST.get('last_working_date'),
                'selected_elsewhere': request.POST.get('selected_elsewhere'),
                'bond_over': request.POST.get('bond_over'),
                'advance_salary': request.POST.get('advance_salary'),
                'any_dues': request.POST.get('any_dues'),
            }
            return render(request, 'employee/resignation_email_form.html', context)

    return render(request, 'employee/apply_resignation.html', {'employee': employee})


@login_required
def view_my_exit_request(request):
    employee_profile = get_employee_profile(request.user)
    if not employee_profile:
        messages.error(request, "Employee profile not found.")
        return redirect('index')

    exit_request = ExitRequest.objects.filter(employee=employee_profile).order_by('-created_at').first()
    context = {
        'exit_request': exit_request,
        'content_title': 'My Exit Request Status',
    }
    return render(request, 'employee/view_my_exit_request.html', context)


@login_required
def withdraw_resignation(request, request_id):
    employee_profile = get_employee_profile(request.user)
    exit_request = get_object_or_404(ExitRequest, id=request_id, employee=employee_profile)

    # Allow withdrawal only if in certain states (e.g., before final HR approval)
    if exit_request.status not in ['PENDING_RM_APPROVAL', 'PENDING_HR_APPROVAL']:
        messages.error(request, "Resignation cannot be withdrawn at this stage.")
        return redirect('view_my_exit_request')

    if request.method == 'POST':  # Confirmation step
        exit_request.status = 'WITHDRAWN'
        exit_request.save()
        messages.success(request, "Your resignation request has been withdrawn.")
        # TODO: Notify relevant parties (RM, HR)
        return redirect('resignation_status')

    context = {
        'exit_request': exit_request,
        'content_title': 'Confirm Resignation Withdrawal'
    }
    return render(request, 'employee/confirm_withdraw_resignation.html', context)


# --- Views for Reporting Manager ---

def manage_exit_requests_rm(request):
    """
       Displays a list of all exit requests for the employees
       reporting to the currently logged-in manager.
       """
    # Get the current logged-in user, who is the manager
    manager = request.user
    print(request.session.get('employee_id'))
    # Fetch all exit requests for employees who report to this manager
    # The lookup `employee__reporting_manager` traverses the foreign key relationship
    team_requests = ExitRequest.objects.filter(employee__reporting_manager_id=request.session.get('employee_id')).select_related('employee')

    # Separate requests that need the manager's immediate attention
    pending_requests = team_requests.filter(status='PENDING_RM_APPROVAL')

    # Get all other requests (approved, rejected, etc.)
    other_requests = team_requests.exclude(status='PENDING_RM_APPROVAL')

    context = {
        'pending_requests': pending_requests,
        'other_requests': other_requests,
        'content_title': 'Team Exit Requests'  # For the breadcrumb/title
    }
    return render(request, 'employee/manage_exit_requests_rm.html', context)


def approve_reject_exit_rm(request, request_id):
    manager_profile = get_employee_profile(request.user)
    # Add robust permission checks: is this user the RM for this request?
    exit_request = get_object_or_404(ExitRequest, id=request_id, employee__reporting_manager=request.user)

    if exit_request.status != 'PENDING_RM_APPROVAL':
        messages.error(request, "This request is not pending your approval or has already been processed.")
        return redirect('manage_exit_requests_rm')

    form = ExitApprovalFormRM(request.POST or None, instance=exit_request)
    action = request.POST.get("action")  # 'approve' or 'reject'

    if request.method == 'POST' and form.is_valid() and action:
        exit_req = form.save(commit=False)
        if action == "approve":
            exit_req.status = 'PENDING_HR_APPROVAL'
            messages.success(request, f"Exit request for {exit_req.employee.full_name} approved and sent to HR.")
        elif action == "reject":
            exit_req.status = 'REJECTED_BY_RM'
            messages.warning(request, f"Exit request for {exit_req.employee.full_name} rejected.")

        exit_req.reporting_manager_approved_at = timezone.now()  # Or cleared if rejected
        exit_req.save()
        # TODO: Notify employee and HR
        return redirect('manage_exit_requests_rm')

    context = {
        'form': form,
        'exit_request': exit_request,
        'content_title': 'Approve/Reject Exit Request'
    }
    return render(request, 'employee/approve_reject_exit_form.html', context)  # Generic form template

from django.contrib.auth.decorators import login_required


from .models import ExitRequest, ExitActivityLog, AddEmployee # Make sure to import your models


def resignation_approval_view(request, request_id):
    """
    View for a Reporting Manager to review and FORWARD or REJECT a resignation request.
    """
    exit_request = get_object_or_404(ExitRequest, id=request_id)

    # Permission Check (your existing logic is good)
    manager_profile = get_employee_profile(request.user)
    if not manager_profile or manager_profile.id != exit_request.employee.reporting_manager_id:
        messages.error(request, "You do not have permission to process this request.")
        return redirect('index')

    # Manager can only act on requests pending their approval
    if exit_request.status != 'PENDING_RM_APPROVAL':
        messages.info(request, "This request is not awaiting your action.")
         # Or wherever managers see their list

    form = ExitApprovalFormRM(request.POST or None, instance=exit_request)

    if request.method == 'POST':
        if 'approve' in request.POST and form.is_valid():
            exit_req = form.save(commit=False)
            exit_req.status = 'PENDING_HR_APPROVAL'
            exit_req.reporting_manager_approved_at = timezone.now()
            exit_req.save()
            exit_request.status = 'PENDING_HR_APPROVAL'
            exit_request.save()

            # Log the approval action
            ExitActivityLog.objects.create(
                exit_request=exit_request,
                actor=request.user,
                action=f"Resignation approved by {request.user.get_full_name()}"
            )

            # TODO: Send email notifications to HR and the employee
            messages.success(request, f"Resignation for {exit_request.employee.full_name} has been approved.")


        elif 'reject' in request.POST and form.is_valid():

            exit_req = form.save(commit=False)

            exit_req.status = 'REJECTED_BY_RM'

            exit_req.save()

            messages.warning(request, f"Resignation for {exit_req.employee.full_name} has been rejected.")

            exit_request.status = 'REJECTED'
            exit_request.save()

            # Log the rejection action
            ExitActivityLog.objects.create(
                exit_request=exit_request,
                actor=request.user,
                action=f"Resignation rejected by {request.user.get_full_name()}"
            )

            # TODO: Send email notification to the employee
            messages.warning(request, f"Resignation for {exit_request.employee.full_name} has been rejected.")

        return redirect('resignation_approval', request_id=exit_request.id)

    # Fetch all activity logs for the timeline
    activity_logs = exit_request.activity_logs.order_by('timestamp')

    context = {
        'form': form,
        'exit_request': exit_request,
        'activity_logs': activity_logs, # Uncomment when you have the model
        'content_title': 'Exit Approval'
    }
    return render(request, 'employee/resignation_approval.html', context)

# modal for changing exit request actual_last_wking_day

def change_last_working_date(request, exit_id):
    if request.method == 'POST':
        actual_last_working_day = request.POST.get('actual_last_working_day')
        if actual_last_working_day:
            exit_request = get_object_or_404(ExitRequest, id=exit_id)
            exit_request.actual_last_working_day = actual_last_working_day
            exit_request.save()
            messages.success(request, "Actual last working day updated successfully.")
            print(exit_request.employee.full_name)
        else:
            messages.error(request, "Please select a valid date.")
    print(exit_request.employee.full_name)
    return redirect('resignation_approval', request_id=exit_request.id)  # Adjust this redirect as needed
# --- Views for HR ---

def manage_exit_requests_hr(request):
    # Implement HR role check
    hr_profile = get_employee_profile(request.user)
    if not hr_profile or hr_profile.role.name != 'HR':  # Example role name
        messages.error(request, "You are not authorized to view this page.")
        return redirect('index')

    pending_hr_approval = ExitRequest.objects.filter(status='PENDING_HR_APPROVAL')
    all_other_requests = ExitRequest.objects.exclude(status='PENDING_HR_APPROVAL')

    context = {
        'pending_hr_approval': pending_hr_approval,
        'all_other_requests': all_other_requests,
        'content_title': 'Manage All Exit Requests (HR)',
    }
    return render(request, 'employee/manage_exit_requests_hr.html', context)


# in your views.py


def process_exit_request_hr(request, request_id):
    """
    View for HR to give FINAL approval, manage the checklist, and set the last working day.
    This view's logic is already correct for the new workflow.
    """
    hr_profile = get_employee_profile(request.user)
    if not hr_profile or hr_profile.role.name != 'HR':
        messages.error(request, "Unauthorized.")
        return redirect('index')

    exit_request = get_object_or_404(ExitRequest, id=request_id)

    # This condition correctly allows HR to act on requests sent from the manager
    # or to update checklists on already-approved requests.
    if exit_request.status not in ['PENDING_HR_APPROVAL', 'APPROVED']:
        messages.info(request, "This request is not in a state for HR to process.")

    # These forms are correct based on your forms.py
    approval_form = ExitApprovalFormHR(request.POST or None, instance=exit_request, prefix="approval")
    checklist_form = ExitChecklistForm(request.POST or None, instance=exit_request, prefix="checklist")
    action = request.POST.get("action")

    if request.method == 'POST':
        # This block correctly handles the final approval step
        if action == "approve_hr" and approval_form.is_valid() and exit_request.status == 'PENDING_HR_APPROVAL':
            exit_req = approval_form.save(commit=False)
            exit_req.status = 'APPROVED'  # This is the FINAL approved status.
            exit_req.hr_approved_at = timezone.now()
            exit_req.save()  # Saves hr_remarks and actual_last_working_day from the form
            messages.success(request, f"Exit request for {exit_req.employee.full_name} has been finally approved.")
            return redirect('manage_exit_requests_hr')

        # Other actions (reject, update checklist) remain the same and are correct.
        elif action == "reject_hr" and approval_form.is_valid() and exit_request.status == 'PENDING_HR_APPROVAL':
            exit_req = approval_form.save(commit=False)
            exit_req.status = 'REJECTED_BY_HR'
            exit_req.save()
            messages.warning(request, f"Exit request for {exit_req.employee.full_name} has been rejected by HR.")
            return redirect('manage_exit_requests_hr')

        elif action == "update_checklist" and checklist_form.is_valid():
            checklist_form.save()
            messages.success(request, f"Exit checklist for {exit_request.employee.full_name} updated.")
            return redirect('process_exit_request_hr', request_id=exit_request.id)

        # ... error handling ...

    context = {
        'approval_form': approval_form,
        'checklist_form': checklist_form,
        'exit_request': exit_request,
        'content_title': f'Process Exit: {exit_request.employee.full_name}',
        'can_approve_reject': exit_request.status == 'PENDING_HR_APPROVAL',
    }
    return render(request, 'employee/process_exit_request_hr.html', context)

from .models import CalendarEvent
import json
@login_required
def calendar_view(request): # Assuming 'calendar' is the name of your calendar page URL
    # You can pass initial events here if needed, but we'll load them via AJAX
    return render(request, 'calendar.html') # Replace with your actual template name

@login_required
def get_events(request):
    events = CalendarEvent.objects.filter(user=request.user)
    event_list = []
    for event in events:
        event_list.append({
            'id': event.id,
            'title': event.title,
            'start': event.start.isoformat(),
            'end': event.end.isoformat() if event.end else None,
            'allDay': event.all_day,
            'color': event.color,
            'description': event.description or ''
        })
    return JsonResponse(event_list, safe=False)

@login_required
@csrf_exempt # Ensure you understand CSRF implications for production
def add_event(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title')
            start_str = data.get('start')
            end_str = data.get('end')
            all_day = data.get('allDay', False)
            color = data.get('color', '#3c8dbc') # Default color

            # Basic validation
            if not title or not start_str:
                return JsonResponse({'status': 'error', 'message': 'Title and start date are required.'}, status=400)

            # Parse dates
            # FullCalendar might send ISO 8601 strings or just date for allDay events
            try:
                start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00')) # Handle 'Z' for UTC
                end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00')) if end_str else None
            except ValueError:
                 return JsonResponse({'status': 'error', 'message': 'Invalid date format.'}, status=400)


            event = CalendarEvent.objects.create(
                user=request.user,
                title=title,
                start=start_dt,
                end=end_dt,
                all_day=all_day,
                color=color
            )
            return JsonResponse({'status': 'success', 'event_id': event.id, 'message': 'Event added successfully', 'reload': True})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

@login_required
@csrf_exempt # Ensure you understand CSRF implications for production
def update_event(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            event_id = data.get('id')
            start_str = data.get('start')
            end_str = data.get('end')
            all_day = data.get('allDay', False) # FullCalendar might send this if allDay status changes

            event = CalendarEvent.objects.get(id=event_id, user=request.user)

            if start_str:
                event.start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            if end_str:
                event.end = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
            else: # If end is not provided, it might mean it's an all-day event or it was cleared
                event.end = None

            event.all_day = all_day
            # You might also want to update title or color if your UI allows it during update
            # event.title = data.get('title', event.title)
            # event.color = data.get('color', event.color)

            event.save()
            return JsonResponse({'status': 'success', 'message': 'Event updated successfully'})
        except CalendarEvent.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Event not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


@login_required
@csrf_exempt # Ensure you understand CSRF implications for production
def delete_event(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            event_id = data.get('id')
            event = CalendarEvent.objects.get(id=event_id, user=request.user)
            event.delete()
            return JsonResponse({'status': 'success', 'message': 'Event deleted successfully'})
        except CalendarEvent.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Event not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

from calendar import month_name

@property
def month_year_display(self):
    return f"{month_name[self.month]} {self.year}"


@login_required
def salary_details_view(request):
    month_choices = [(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)]
    year_choices = list(range(2020, datetime.now().year + 1))

    selected_month = int(request.GET.get('month', datetime.now().month))
    selected_year = int(request.GET.get('year', datetime.now().year))

    salary_data = SalaryData.objects.filter(month=selected_month, year=selected_year)
    month_year_display = f"{datetime(2000, selected_month, 1).strftime('%B')} {selected_year}"

    context = {
        'salary_data': salary_data,
        'month_year_display': month_year_display,
        'month_choices': month_choices,
        'year_choices': year_choices,
        'selected_month': selected_month,
        'selected_year': selected_year,
    }
    return render(request, 'salary_details.html', context)


# return HttpResponse("<h1>Salary Details Page</h1><p>This page will show employee salary information.</p>")

# @login_required
from django.shortcuts import render

from django.shortcuts import render
from django.db.models import Sum
from .models import SalaryData
from django.shortcuts import render
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib import messages
from .models import SalaryData
from django.db.models import Sum
import tempfile
from weasyprint import HTML
def send_monthly_report_email(payroll_data):
    subject = "May 2025 Payroll Summary"
    to_email = "kataranischal@gmail.com"  # Update to the head's email
    html_content = render_to_string('emails/monthly_report_email.html', {
        'payroll_data': payroll_data,
        'month_year_display': 'May, 2025 Payroll'
    })

    email = EmailMessage(subject, html_content, to=[to_email])
    email.content_subtype = "html"
    email.send()


# def send_monthly_report_pdf(payroll_data):
#     subject = "May 2025 Payroll PDF"
#     to_email = "kataranischal@gmail.com"  # Update as needed
#
#     # Render HTML for PDF
#     html_string = render_to_string('emails/monthly_report_pdf.html', {
#         'payroll_data': payroll_data,
#         'month_year_display': 'May, 2025 Payroll'
#     })
#
#     # Generate PDF using WeasyPrint
#     with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as pdf_file:
#         HTML(string=html_string).write_pdf(pdf_file.name)
#         pdf_file.seek(0)
#         email = EmailMessage(subject, "Attached is the payroll PDF for May 2025.", to=[to_email])
#         email.attach('May_2025_Payroll.pdf', pdf_file.read(), 'application/pdf')
#         email.send()
import logging
from celery import shared_task
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from weasyprint import HTML
from .models import SalaryData
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task(name="hr_app.send_individual_payslip_email")
def send_individual_payslip_email(record_id):
    try:
        record = SalaryData.objects.select_related('employee_identifier').get(id=record_id)

        html_string = render_to_string('payslip_template.html', {
            'record': record,
            'logo_url': settings.STATIC_URL + 'images/company_logo.png'  # adjust if needed
        })
        pdf = HTML(string=html_string).write_pdf()

        employee_email = record.employee_identifier.email
        employee_name = record.employee_identifier.full_name
        month_year = record.month_year_display

        email = EmailMessage(
            subject=f"Payslip for {month_year}",
            body="Please find your attached payslip.",
            from_email="hr@yourcompany.com",
            to=[employee_email],
        )
        email.attach(f"Payslip_{employee_name}.pdf", pdf, 'application/pdf')
        email.send()
        logger.info(f"Payslip email sent to {employee_email}")

    except Exception as e:
        logger.error(f"Failed to send payslip to ID {record_id}: {str(e)}")


from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile
def send_monthly_report_pdf(payroll_data):
    if not payroll_data.exists():
        return

    # Determine month/year label for filenames and subject
    sample = payroll_data.first()
    month = sample.month
    year = sample.year
    month_year_display = f"{sample.created_at.strftime('%B, %Y')}" if hasattr(sample, 'created_at') else f"{month:02d}/{year}"
    subject = f"{month_year_display} Payslip"

    # Get unique employees
    employees = payroll_data.values_list('employee_identifier', 'employee_identifier__email', 'employee_identifier__full_name').distinct()

    for emp_id, email, name in employees:
        employee_data = payroll_data.filter(employee_identifier_id=emp_id)

        if not email:
            continue  # skip if email missing

        # Render HTML for this employee
        html_string = render_to_string('emails/monthly_report_pdf.html', {
            'payroll_data': employee_data,
            'month_year_display': f'{month_year_display} Payslip',
            'employee_name': name
        })

        # Generate individual PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as pdf_file:
            HTML(string=html_string).write_pdf(pdf_file.name)
            pdf_file.seek(0)
            pdf_data = pdf_file.read()

        # Send email
        email_msg = EmailMessage(
            subject=subject,
            body=f"Dear {name},\n\nPlease find attached your payslip for {month_year_display}.\n\nRegards,\nHR Department",
            to=[email]
        )
        email_msg.attach(f"{name.replace(' ', '_')}_{month_year_display.replace(',', '').replace(' ', '_')}_Payslip.pdf", pdf_data, 'application/pdf')

        email_msg.send()




@login_required
def monthly_payroll_data_view(request):

    from datetime import datetime
    now = datetime.now()
    month = request.GET.get('month', f"{now.year}-{now.month:02d}")

    try:
        year, month = map(int, month.split('-'))
    except ValueError:
        year, month = now.year, now.month

    # Query salary data
    payroll_data = SalaryData.objects.filter(month=month, year=year)

    # Aggregated totals
    totals = payroll_data.aggregate(
        total_basic=Sum('basic_salary'),
        total_hra=Sum('hra'),
        total_da=Sum('da'),
        total_salary=Sum('total_salary'),
        total_present=Sum('present_days'),
        total_paid_leave=Sum('paid_leaves'),
        total_unpaid_leave=Sum('unpaid_leaves'),
        total_incentive=Sum('project_incentive'),
        total_variable=Sum('variable_pay'),
        total_esi=Sum('esi'),
        total_pf=Sum('pf'),
        total_tds=Sum('tds'),
    )
    
    if request.method == "POST":
        if 'send_report_email' in request.POST:
            print(payroll_data)
            send_monthly_report_email(payroll_data)
            messages.success(request, "Monthly report sent to Head via email.")
        elif 'send_pdf_email' in request.POST:
            send_monthly_report_pdf(payroll_data)
            messages.success(request, "Monthly PDF payroll sent via email.")
    context = {
        'payroll_data': payroll_data,
        'totals': totals,
        'month_year_display': datetime(year, month, 1).strftime('%B, %Y'),
        'selected_month': f"{year}-{month:02d}",
        'page_title': 'Monthly Payroll'
    }

    return render(request, 'monthly_payroll_data.html', context)


@login_required
def payroll_settings_main_view(request):
    # Your logic for main payroll settings (distinct from the one in Configuration if needed)
    return HttpResponse("<h1>Payroll Settings Page (Main)</h1><p>This page will allow configuration of payroll settings.</p>")


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal, InvalidOperation
from .models import SalaryData, AddEmployee  # adjust import path if needed
import csv
import io

@login_required
def upload_salary_csv_view(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        month_year_str = request.POST.get('payroll_month')  # updated field name

        if not csv_file:
            messages.error(request, "No CSV file selected.")
            return redirect('upload_salary_csv')

        if not csv_file.name.endswith('.csv'):
            messages.error(request, "Invalid file type. Please upload a .csv file.")
            return redirect('upload_salary_csv')

        if csv_file.size > 100 * 1024:
            messages.error(request, "File size exceeds 100KB limit.")
            return redirect('upload_salary_csv')

        if not month_year_str:
            messages.error(request, "Month and Year not selected.")
            return redirect('upload_salary_csv')

        try:
            year_str, month_str = month_year_str.split('-')
            year = int(year_str)
            month = int(month_str)
        except ValueError:
            messages.error(request, "Invalid Month/Year format.")
            return redirect('upload_salary_csv')

        try:
            decoded_file = csv_file.read().decode('utf-8-sig')
            io_string = io.StringIO(decoded_file)
            reader = csv.reader(io_string)
            header = next(reader, None)

            records_processed = 0
            errors_in_rows = []

            for row_number, row in enumerate(reader, start=2):
                if not any(field.strip() for field in row):
                    continue

                try:
                    (
                        employee_name, employee_email,
                        basic_salary_str, hra_str, da_str,
                        present_days_str, paid_leaves_str, unpaid_leaves_str,
                        project_incentive_str, variable_pay_str,
                        esi_str, pf_str, tds_str
                    ) = [field.strip() for field in row[:13]]

                    # Find employee by email
                    try:
                        employee = AddEmployee.objects.get(email=employee_email)
                    except AddEmployee.DoesNotExist:
                        errors_in_rows.append(f"Row {row_number}: Employee with email '{employee_email}' not found.")
                        continue
                    except AddEmployee.MultipleObjectsReturned:
                        errors_in_rows.append(f"Row {row_number}: Multiple employees found with email '{employee_email}'.")
                        continue

                    payslip_code = f"{employee.id}-{year:04d}{month:02d}"

                    SalaryData.objects.update_or_create(
                        employee_identifier=employee,
                        month=month,
                        year=year,
                        defaults={
                            'payslip_code': payslip_code,
                            'basic_salary': Decimal(basic_salary_str or 0),
                            'hra': Decimal(hra_str or 0),
                            'da': Decimal(da_str or 0),
                            'total_salary': (
                                Decimal(basic_salary_str or 0) +
                                Decimal(hra_str or 0) +
                                Decimal(da_str or 0)
                            ),
                            'present_days': int(present_days_str or 0),
                            'paid_leaves': int(paid_leaves_str or 0),
                            'unpaid_leaves': int(unpaid_leaves_str or 0),
                            'project_incentive': Decimal(project_incentive_str or 0),
                            'variable_pay': Decimal(variable_pay_str or 0),
                            'esi': Decimal(esi_str or 0),
                            'pf': Decimal(pf_str or 0),
                            'tds': Decimal(tds_str or 0),
                        }
                    )

                    records_processed += 1

                except (ValueError, InvalidOperation) as e:
                    errors_in_rows.append(f"Row {row_number}: Invalid data format - {str(e)}")
                except Exception as e:
                    errors_in_rows.append(f"Row {row_number}: Unexpected error - {str(e)}")

            if errors_in_rows:
                for error in errors_in_rows:
                    messages.warning(request, error)
                messages.error(request, f"{records_processed} rows processed with some errors.")
            elif records_processed == 0:
                messages.warning(request, "No valid records found.")
            else:
                messages.success(request, f"{records_processed} salary records processed successfully.")

            return redirect('upload_salary_csv')

        except UnicodeDecodeError:
            messages.error(request, "CSV decoding failed. Please use UTF-8 encoding.")
        except csv.Error as e:
            messages.error(request, f"CSV reading error: {str(e)}")
        except Exception as e:
            messages.error(request, f"Unexpected error: {str(e)}")

        return redirect('upload_salary_csv')

    return render(request, 'upload_salary_csv.html', {'page_title': 'Upload Salary CSV'})

# --- Views for existing items in Configuration (if they are different from the new ones) ---
# If 'payroll_setting' and 'employee_salary' from the Configuration menu point to
# DIFFERENT pages than the new 'Employee Salary' dropdown items, you'll have separate views.
# If they are meant to be the SAME, then you'd reuse the views above and ensure the
# URL names match in the template.

# For example, if the 'payroll_setting' in "Configuration" is different:
# @login_required
@login_required
def configuration_payroll_setting_view(request):
    return HttpResponse("<h1>Payroll Setting Page (from Configuration)</h1>")

# If the 'employee_salary' in "Configuration" is different:
@login_required
def configuration_employee_salary_view(request):
    return HttpResponse("<h1>Employee Salary Page (from Configuration)</h1>")


from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from weasyprint import HTML
from .models import SalaryData
@login_required
def download_payslip_pdf(request, record_id):
    record = get_object_or_404(SalaryData, id=record_id)
    logo_url = request.build_absolute_uri('/static/img/logo1.png')
    html_string = render_to_string('payslip_template.html', {
        'record': record,
        'logo_url': logo_url,
    })
    html = HTML(string=html_string)
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=payslip_{record.employee_identifier}.pdf'
    return response


from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from weasyprint import HTML
from django.contrib import messages
from .models import SalaryData
from calendar import month_name
@login_required
def email_payslip(request, record_id):
    print("email_payslip view triggered")  # ✅ Debug

    if request.method == 'POST':
        print("POST method confirmed")  # ✅ Debug
        record = get_object_or_404(SalaryData, id=record_id)
        logo_url = request.build_absolute_uri('/static/img/logo1.png')

        html_string = render_to_string('payslip_template.html', {'record': record, 'logo_url': logo_url,})
        pdf = HTML(string=html_string).write_pdf()

        employee_email = record.employee_identifier.email
        employee_name = record.employee_identifier.full_name

        month_year = f"{month_name[record.month]} {record.year}"
        email = EmailMessage(
            subject=f"Payslip for {month_year}",
            body="Please find your attached payslip.",
            from_email="kataranischal@gmail.com",
            to=[employee_email],
        )
        email.attach(f"Payslip_{employee_name}.pdf", pdf, 'application/pdf')
        email.send()

        print(f"Sent email to {employee_email}")  # ✅ Debug
        messages.success(request, f"Payslip sent to {employee_email}")
    else:
        print("Not a POST request!")  # ❌ Most common issue
    return redirect('salary_details')


@login_required
def email_payslips_to_all(request):
    if request.method == 'POST':
        month = int(request.POST.get('month'))
        year = int(request.POST.get('year'))

        salary_records = SalaryData.objects.filter(month=month, year=year)
        logo_url = request.build_absolute_uri('/static/img/logo1.png')

        for record in salary_records:
            html_string = render_to_string('payslip_template.html', {'record': record, 'logo_url': logo_url})
            pdf = HTML(string=html_string).write_pdf()

            employee_email = record.employee_identifier.email
            employee_name = record.employee_identifier.full_name
            month_year = f"{datetime(2000, month, 1).strftime('%B')} {year}"

            email = EmailMessage(
                subject=f"Payslip for {month_year}",
                body="Please find your attached payslip.",
                from_email="hr@yourcompany.com",
                to=[employee_email],
            )
            email.attach(f"Payslip_{employee_name}.pdf", pdf, 'application/pdf')
            try:
                email.send()
                messages.success(request, f"Payslip sent to {employee_email}")
            except Exception as e:
                messages.error(request, f"Failed to send to {employee_email}: {e}")

        return redirect('salary_details')


@login_required
def employee_payslip_list_by_id(request, employee_id):
    employee = get_object_or_404(AddEmployee, id=employee_id)
    payslip_records = SalaryData.objects.filter(employee_identifier=employee).order_by('-year', '-month')

    context = {
        'employee': employee,
        'payslip_records': payslip_records,
    }
    return render(request, 'employee_payslip_list.html', context)


# learning/views.py
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from . import services  # Import our new services

# You can put the URL in your settings.py for better configuration
# from django.conf import settings
# YOUTUBE_CHANNEL_URL = settings.YOUTUBE_CHANNEL_URL
# hr_app/views.py
# hr_app/views.py
# hr_app/views.py

# hr_app/views.py

from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator  # <-- Import the Paginator
from . import services

YOUTUBE_CHANNEL_URL = "https://www.youtube.com/@bispsolutions/playlists"


# The cache will still work, but it will cache each page individually (e.g., ?page=1, ?page=2)
@cache_page(60 * 60)
def learning_videos(request):
    # 1. Get the FULL list of all playlists from the service
    all_playlists = services.get_youtube_playlists(YOUTUBE_CHANNEL_URL)

    # 2. Set up the Paginator
    # We choose 9 items per page because it works perfectly with a 3-column grid (3 rows of 3).
    paginator = Paginator(all_playlists, 9)

    # 3. Get the current page number from the URL's GET parameters (e.g., /learning/?page=2)
    page_number = request.GET.get('page')

    # 4. Get the Page object for the requested page number.
    #    'get_page' handles invalid page numbers gracefully (e.g., text, out of range).
    page_obj = paginator.get_page(page_number)

    # 5. Update the context to pass the 'page_obj' instead of the full list
    context = {
        'page_obj': page_obj,  # Pass the paginated object to the template
        'channel_url': YOUTUBE_CHANNEL_URL.rsplit('/', 1)[0],
    }

    return render(request, "learning/playlist_index.html", context)


# ... your other views ...
@login_required
def user_settings(request):
    employee = AddEmployee.objects.get(id=request.session['employee_id'])

    if request.method == 'POST':
        # Handle the form submission for changing the preference
        new_preference = request.POST.get('timesheet_preference')

        # Simple validation
        allowed_preferences = [choice[0] for choice in AddEmployee.TIMESHEET_CHOICES]
        if new_preference in allowed_preferences:
            employee.timesheet_preference = new_preference
            employee.save()

            # IMPORTANT: Update the session immediately!
            request.session['timesheet_preference'] = new_preference

            messages.success(request, 'Your timesheet preference has been updated successfully!')
        else:
            messages.error(request, 'Invalid preference selected.')

        return redirect('user_settings')  # Redirect back to the same page

    # For GET request, just render the page
    context = {'current_preference': employee.timesheet_preference}
    return render(request, 'profile/user_settings.html', context)
# latest updates
# hr_app/views.py
@login_required
def all_notifications(request):
    employee_id = request.session.get('employee_id')

    # Get all notifications for the user, newest first
    notifications = Notification.objects.filter(user_id=employee_id)

    # Mark all unread notifications as read when the user visits this page
    # This is an efficient way to handle it
    Notification.objects.filter(user_id=employee_id, is_read=False).update(is_read=True)

    context = {'notifications': notifications}
    return render(request, 'notifications/all_notifications.html', context)


# hr_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import AddEmployee  # Make sure your Employee model is imported

@login_required
def edit_employee(request, employee_id):
    # Get the specific employee object, or return a 404 error if not found
    employee = get_object_or_404(AddEmployee, id=employee_id)

    # Handle the form submission
    if request.method == 'POST':
        # Get the submitted data from the form
        full_name = request.POST.get('full_name')
        designation = request.POST.get('designation')
        # ... get other fields you want to edit ...

        # Update the employee object with the new data
        employee.full_name = full_name
        employee.designation = designation
        # ... update other fields ...

        employee.save()  # Save the changes to the database

        # Provide feedback to the user and redirect
        messages.success(request, f"Details for {employee.full_name} updated successfully!")
        return redirect('edit_employee', employee_id=employee.id)

    # For a GET request (when the user just visits the page)
    context = {
        'employee': employee,
        # Pass the designation choices to the template for the dropdown
        'designation_options': AddEmployee.DESIGNATION_CHOICES,
    }
    return render(request, 'hr_app/edit_employee.html', context)


def csrf_failure(request, reason=""):
    return render(request, "csrf_error.html", {"reason": reason})
    # NEW and REQUIRED view for comments

@login_required
def add_task_comment(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        comment_text = request.POST.get('comment')
        if comment_text:
            # Use the same log_activity helper
            action_text = "added a comment"
            log_activity(task, request.user, action_text, comment=comment_text)
            messages.success(request, "Your comment has been posted.")
        else:
            messages.error(request, "Comment cannot be empty.")
    
    return redirect('task_detail', task_id=task.id)
# This helper function is essential for the timeline
def log_activity(task, user, action, comment=None):
    # (Same helper function from my previous answer)
    # ... logic to create ActivityLog object ...
    icon_map = {
        'Pending': ('fas fa-clock', 'warning'),
        'Claimed Completed': ('fas fa-flag-checkered', 'info'),
        'Completed': ('fas fa-check-circle', 'success'),
    }
    icon, color = icon_map.get(task.status, ('fas fa-info', 'secondary'))

    ActivityLog.objects.create(
        task=task, user=user, action=action,
        comment=comment, icon_class=icon, color=color
    )
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification, AddEmployee

@login_required
def mark_notification_as_read(request, notification_id):
    current_employee = get_object_or_404(AddEmployee, id=request.session.get('employee_id'))
    notification = get_object_or_404(Notification, id=notification_id, user=current_employee)
    
    notification.is_read = True
    notification.save()
    
    return redirect(notification.link) if notification.link else redirect('dashboard')
# hr_app/views.py

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    activity_logs = task.activity_logs.all().order_by('-timestamp')
    
    # --- ADD THIS ---
    # Fetch all messages related to this task to display the conversation
    task_messages = task.task_messages.all()

    context = {
        'task': task,
        'activity_logs': activity_logs,
        'task_messages': task_messages,  # Pass messages to the template
        'request': request,
    }
    return render(request, 'task_details.html', context)
# hr_app/views.py

@login_required
def post_task_message(request, task_id):
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id)
        message_content = request.POST.get('message')
        
        # Get the sender's AddEmployee profile
        sender_profile = get_object_or_404(AddEmployee, id=request.session.get('employee_id'))

        if message_content:
            TaskMessage.objects.create(
                task=task,
                sender=sender_profile,
                message=message_content
            )
            # The signal will automatically handle creating the notification
        else:
            messages.error(request, "Message cannot be empty.")
            
    # Redirect back to the task detail page to see the new message
    return redirect('task_detail', task_id=task_id)