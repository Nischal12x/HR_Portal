import re
from datetime import datetime, timezone, date, timedelta

from django.db import models
from django.utils import timezone
from collections import defaultdict
from django.core.paginator import Paginator
from django.core.files.storage import FileSystemStorage
from django.db.models import Sum, Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.shortcuts import render, redirect

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from .models import Project, AddEmployee, Timesheet  # Ensure these models are imported
from .forms import EmployeeForm
from .models import Role, AddEmployee, LeaveApplication, Leave_Type, Task
from django.views.decorators.csrf import csrf_exempt
from .models import Project
from django.utils.dateparse import parse_date

def update_project(request, project_id):
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

def project(request, project_id):
    proj = get_object_or_404(Project, id=project_id)

    # Fetch only tasks associated with this project
    tasks = Task.objects.filter(project=proj)


    return render(request, 'project.html', {
        'proj': proj,
        'tasks': tasks
    })

@csrf_exempt

@csrf_exempt
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

        # Success response for AJAX
        if p_id != 0 :
            return JsonResponse({'success': True, 'message': "Project Updated successfully!"})
        return JsonResponse({'success': True, 'message': "Project saved successfully!"})

    # Context for the form (used in the template)
    context = {
        'leaders': AddEmployee.objects.filter(role_id=2),
        'admins': AddEmployee.objects.filter(role_id=1),
        'team_members': AddEmployee.objects.filter(role_id=3),
    }
    return render(request, 'add_project.html', context)




def toggle_leave_status(request, leave_id):
    if request.method == "POST":
        leave = get_object_or_404(Leave_Type, id=leave_id)
        leave.is_active = not leave.is_active
        leave.save()
        messages.success(request, f"{leave.leavetype} has been {'activated' if leave.is_active else 'deactivated'}.")
    return redirect('leaves_sys')

def leave_details(request, leave_id):
    leave = get_object_or_404(Leave_Type, id=leave_id)

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
        leave_obj = Leave_Type.objects.get(leave_code=leave_code)

        if not leave_obj:
            messages.error(request, "Leave entry not found.")
            return redirect('leave_settings')

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
        leave_obj.accrual_enabled = accrual_enabled
        leave_obj.leave_time = leave_time
        leave_obj.leave_time_unit = leave_time_unit
        leave_obj.accrual_frequency = accrual_frequency
        leave_obj.count_weekends = count_weekends
        leave_obj.count_holidays = count_holidays

        leave_obj.save()
        messages.success(request, "Changes applied successfully.")
        return redirect('leaves_sys')

    return redirect('leave_settings')

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
            return redirect('apply_leave')

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
        if compensation == '1' :
            pass
        else :
            leave.leave_days = leave_days
        leave.save()
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

def add_employee(request):
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
                "errors": errors  # ✅ send field-wise errors
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
        messages.success(request, "Employee added successfully!")
        return redirect('index')

    return render(request, "add_emp.html")







def employee_list(request):
    employees = AddEmployee.objects.all()  # Fetch all employees
    return render(request, "data.html", {"employees": employees})


# Update Employee
from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from django.utils.timezone import now
from datetime import datetime
import re

from .models import AddEmployee, EmployeeHistory

def update_employee(request, id):
    employee = get_object_or_404(AddEmployee, id=id)

    if request.method == 'POST':

        # Fetch the last history entry (if exists)
        last_history = EmployeeHistory.objects.filter(employee=employee).order_by('-created_at').first()

        # Close the previous history period
        if last_history and last_history.until is None:
            last_history.until = now()
            last_history.save()

        # Update employee data from form
        employee.full_name = request.POST.get('full_name', '').strip()
        employee.email = request.POST.get('email', '').strip()
        employee.phone = request.POST.get('phone', '').strip()
        employee.dob = request.POST.get('dob', '').strip()
        employee.gender = request.POST.get('gender', '').strip()
        employee.address = request.POST.get('address', '').strip()
        employee.department = request.POST.get('department', '').strip()
        employee.designation = request.POST.get('designation', '').strip()
        employee.joining_date = request.POST.get('joining_date', '').strip()
        employee.salary = request.POST.get('salary', '').strip()
        employee.employment_type = request.POST.get('employment_type', '').strip()
        employee.marital_status = request.POST.get('marital_status')


        # File upload
        if 'attachment' in request.FILES:
            attachment = request.FILES['attachment']
            fs = FileSystemStorage()
            filename = fs.save(attachment.name, attachment)
            employee.attachment = filename

        # Validations
        if not re.match(r'^[A-Za-z\s]+$', employee.full_name):
            messages.error(request, "Name should only contain alphabets and spaces.")
            return redirect('employees')
        if not re.fullmatch(r'^[0-9]{10}$', employee.phone):
            messages.error(request, "Invalid phone number. It must be 10 digits.")
            return redirect("employees")
        try:
            dob_date = datetime.strptime(str(employee.dob), "%Y-%m-%d").date()
            if dob_date > datetime.today().date():
                messages.error(request, "DOB cannot be in the future.")
                return redirect("employees")
        except ValueError:
            messages.error(request, "Invalid DOB format.")
            return redirect("employees")

        # Save updated data
        employee.save()

        # Create new history with current employee data
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

        messages.success(request, "Employee updated successfully!")
        return redirect('employees')

    return render(request, 'add_emp.html', {'employee': employee})

def employee_history(request, id):
    employee = get_object_or_404(AddEmployee, id=id)
    history_qs = EmployeeHistory.objects.filter(employee=employee).order_by('created_at')

    paginator = Paginator(history_qs, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'employee_history.html', {
        'employee': employee,
        'page_obj': page_obj,
        'total_pages': paginator.num_pages,
    })

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
    return render(request, 'add_emp.html',{'employee': employee, 'roles' : roles} )
# Delete Employee
def delete_employee(request, id):
    employee = get_object_or_404(AddEmployee, id=id)
    employee.delete()
    messages.success(request, "Employee deleted successfully!")
    return redirect('employees')


def check_cred(request):
    if request.method == "POST":
        email = request.POST.get("email", '').strip()
        password = request.POST.get("password", '').strip()

        try:
            # Fetch the employee from the database
            employee = AddEmployee.objects.get(email=email)

            # Validate the password (replace with check_password if hashed)
            if password == employee.employee_id:  # Replace 'employee.phone' with 'employee.password' for real passwords
                # Set session variables
                request.session['employee_id'] = employee.id
                request.session['employee_email'] = employee.email
                request.session['is_logged_in'] = True
                request.session['name'] = employee.full_name
                request.session['designation'] = employee.designation
                request.session['department'] = employee.department
                request.session['role'] = employee.role.name if employee.role else 'No Role Assigned'
                if employee.attachment:
                    request.session['attachment'] = employee.attachment.url
                # Redirect to the home page or dashboard
                return render(request, "index.html", {"employee": employee})
            else:
                messages.error(request, "Incorrect password!")
        except AddEmployee.DoesNotExist:
            messages.error(request, "Email does not exist!")

    # Render login page with error messages
    return render(request, "login.html")



from collections import defaultdict
from django.db.models import Sum
from django.utils import timezone
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

def logout_view(request):
    request.session.flush()  # Clears all session data
    messages.success(request, "You have been logged out successfully!")
    return redirect('login')  # Replace 'login_page' with the appropriate URL


# views.py

def withdraw_leave(request, leave_id):
    leave = get_object_or_404(LeaveApplication, id=leave_id)

    # Optional: check if the current user owns the leave
    # if leave.employee.email == request.session.get('email') and leave.status == 'Pending':
    leave.status = 'Withdrawn'
    leave.save()

    return redirect('leave_dashboard')  # redirect to wherever the leave status is shown

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

def leave_settings_view(request):
    departments = AddEmployee.objects.values_list('department', flat=True).distinct()
    return render(request, 'leave_settings.html', {'departments': departments})
# Create your views here. # Adjust as per your actual model names


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


def admins(request):
    total_employees = AddEmployee.objects.count()
    total_projects = Project.objects.count()
    ongoing_tasks = Task.objects.exclude(status='Completed').count()
    pending_leaves = LeaveApplication.objects.filter(status='Pending').count()
    total_image_timesheets = ImageTimesheet.objects.count()
    context = {
        'total_employees': total_employees,
        'total_projects': total_projects,
        'ongoing_tasks': ongoing_tasks,
        'pending_leaves': pending_leaves,
        'total_image_timesheets': total_image_timesheets,
    }

    return render(request, 'index.html', context)


# from .utils import calculate_remaining_leave  # Assuming the function is in utils.py
from django.db.models import F

from django.db.models import Sum
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

def index2(request):
    # Get all leave types from the Leave_Type model
    leaves = Leave_Type.objects.filter(is_active=True)

    # Initialize a list to store the leave details (consumed and remaining)
    leave_details = []

    # Iterate over each leave type and calculate consumed and remaining leave
    for leave in leaves:
        total_consumed_leave, remaining_leave = calculate_leave_details(request, leave)
        leave_details.append({
            'leave_type': leave,
            'total_consumed_leave': total_consumed_leave,
            'remaining_leave': remaining_leave
        })

    # Pass the leave details to the template
    return render(request, 'index2.html', {'leave_details': leave_details})

def get_team_members(request, project_id):
    employee_id = request.session.get('employee_id')
    project = Project.objects.filter(
        id=project_id
    ).filter(
        models.Q(leader_id=employee_id) | models.Q(admin_id=employee_id)
    ).prefetch_related('team_members').first()

    if not project:
        return JsonResponse({'error': 'Unauthorized or project not found'}, status=403)

    members = [{'id': m.id, 'name': m.full_name} for m in project.team_members.all()]
    return JsonResponse({'members': members})
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

def add_weekly_timesheet(request):
    employee_id = request.session.get('employee_id')
    try:
        employee = AddEmployee.objects.get(id=employee_id)
    except AddEmployee.DoesNotExist:
        messages.error(request, "Employee record not found.")
        return redirect('timesheet')

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


def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    return render(request, 'task_details.html', {'task': task})


def dash_v3(request) :
    return render(request, 'index3.html')
def widgets(request) :
    employee_id = request.session.get('employee_id')
    print("Session Data:", request.session.items())

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
def calendar(request) :
    return render(request, 'calendar.html')
def gallery(request) :
    return render(request, 'gallery.html')
def login(request) :
    return render(request, 'login.html')
def register(request) :
    return render(request, 'register.html')
def add_emp(request):
    roles = Role.objects.all()
    return render(request, 'add_emp.html', {"roles" : roles})
# for_configuration

def payroll_setting(request):
    return render(request, 'configuration/payroll_setting.html')

def employee_salary(request):
    return render(request, 'configuration/employee_salary.html')

def add_employees(request):
    return render(request, 'configuration/add_employees.html')

def leave_settings(request):
    return render(request, 'leave_settings.html')

def holiday_list(request):
    return render(request, 'configuration/holiday_list.html')

def upload_handbook(request):
    return render(request, 'configuration/upload_handbook.html')

def assets(request):
    return render(request, 'configuration/assets.html')


def view_timesheet(request):
    employee_id = request.session.get('employee_id')
    timesheets = Timesheet.objects.filter(employee_id=employee_id).order_by('-date')

    # Calculate hours difference
    for entry in timesheets:
        if entry.start_time and entry.end_time:
            start = datetime.combine(entry.date, entry.start_time)
            end = datetime.combine(entry.date, entry.end_time)
            diff = end - start
            entry.hours = round(diff.total_seconds() / 3600, 2)  # hours as float
        else:
            entry.hours = None

    return render(request, 'Timesheet_records.html', {'timesheets': timesheets})

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

def get_tasks_by_project(request, project_id):
    tasks = Task.objects.filter(project_id=project_id).values('id', 'name')
    return JsonResponse({'tasks': list(tasks)})

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

        if not all([project_id, task_id, timesheet_date, start_time, end_time, description]):
            errors.append("All fields except attachment are required.")

        if start_time >= end_time:
            errors.append("End time must be after start time.")

        try:
            project = Project.objects.get(id=project_id)
            task = Task.objects.get(id=task_id)
        except (Project.DoesNotExist, Task.DoesNotExist):
            errors.append("Invalid project or task.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
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
            return redirect('add_daily_timesheet')

    # GET - fetch project list depending on role
    if employee.role_id == 1:  # HR
        projects = Project.objects.all()
    elif employee.role_id == 2:  # PM
        projects = Project.objects.filter(leader=employee)
    else:  # Team member
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
