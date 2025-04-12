import re
from datetime import datetime



from django.core.files.storage import FileSystemStorage
from django.db.models import Sum
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Role, AddEmployee, LeaveApplication, Leave_Type

from .models import LeaveApplication

def leave_dashboard(request, val=0):
    applicants = LeaveApplication.objects.all()
    return render(request,"leave_dashboard.html", {"applicants" : applicants, "val": val})  # Adjust for actual user system

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
            leave_type=leave_type,
            from_date=from_date,
            till_date=till_date,
            reason=reason,
            attachment=attachment
        )
        leave_days = leave.save(half_day_map=half_day_map)
        leave.leave_days = leave_days
        leave.save()
        messages.success(request, "Leave applied successfully!")
        return redirect('index')

    # If GET request, show form
    return render(request, 'index2.html', {
        'employee': employee,
        'leaves': leaves,
        'available_leaves': employee.available_leaves
    })


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
        elif not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', form_data["email"]):
            errors["email"] = "Invalid email format."
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

        if not form_data["employment_type"]:
            errors["employment_type"] = "Employment type is required."

        # If errors exist, return with messages & form data
        if errors:
            for field, error in errors.items():
                messages.error(request, f"{field.capitalize()}: {error}")
            return render(request, "add_emp.html", {"employee": form_data, "roles": roles,})

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

        messages.success(request, "Employee added successfully!")
        return redirect('index')

    return render(request, "add_emp.html")




def employee_list(request):
    employees = AddEmployee.objects.all()  # Fetch all employees
    return render(request, "data.html", {"employees": employees})


# Update Employee
def update_employee(request, id):
    employee = get_object_or_404(AddEmployee, id=id)

    if request.method == 'POST':
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
        # Handle file upload
        if 'attachment' in request.FILES:
            attachment = request.FILES['attachment']
            fs = FileSystemStorage()
            filename = fs.save(attachment.name, attachment)
            employee.attachment = filename  # Save new attachment

        for char in employee.full_name:
            if char.isdigit():
                messages.error(request, "Invalid Name")
                return redirect('employees')
        if not re.match(r'^[A-Za-z\s]+$', employee.full_name):
            messages.error(request, "Name should only contain alphabets and spaces.")
            return redirect('employees')
        if not re.fullmatch(r'^[0-9]{10}$', employee.phone):
            messages.error(request, "Invalid phone number. It must be exactly 10 digits and contain only numbers.")
            return redirect("employees")
        # Convert `dob` string to a date object
        try:
            dob_date = datetime.strptime(employee.dob, "%Y-%m-%d").date()  # Ensure `dob` is in YYYY-MM-DD format
            today_date = datetime.today().date()

            if dob_date > today_date:
                messages.error(request, "Date of Birth cannot be in the future.")
                return redirect("employees")  # Redirect back if the date is invalid
        except ValueError:
            messages.error(request, "Invalid Date of Birth format. Please enter a valid date.")
            return redirect("employees")
        employee.save()
        messages.success(request, "Employee updated successfully!")
        return redirect('employees')  # Redirect back to employee list

    return render(request, 'update_employee.html', {'employee': employee})

def update_employee1(request, id) :
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
            if password == employee.phone:  # Replace 'employee.phone' with 'employee.password' for real passwords
                # Set session variables
                request.session['employee_id'] = employee.id
                request.session['employee_email'] = employee.email
                request.session['is_logged_in'] = True
                request.session['name'] = employee.full_name
                request.session['designation'] = employee.designation
                request.session['department'] = employee.department
                request.session['role'] = employee.role.name if employee.role else 'No Role Assigned'
                if employee.attachment == 1:
                    request.session['attachment'] = employee.attachment.url
                # Redirect to the home page or dashboard
                return render(request, "index.html", {"employee": employee})
            else:
                messages.error(request, "Incorrect password!")
        except AddEmployee.DoesNotExist:
            messages.error(request, "Email does not exist!")

    # Render login page with error messages
    return render(request, "login.html")

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



# Create your views here.


def admins(request) :
    return render(request, 'index.html')
def dash_v2(request) :
    # Total Leave Allocation
    total_sick_leave = 20
    total_casual_leave = 12
    total_lwp = 12
    total_special_leave = 12
    user_leaves = LeaveApplication.objects.filter(employee__full_name=request.session['name'])

    # Total leave_days for sick leaves (leave_type=1) that are approved
    availed_sick_leave = user_leaves.filter(leave_type=1, status="Approved").aggregate(total_days=Sum('leave_days'))['total_days'] or 0
    availed_lwp = user_leaves.filter(leave_type=4, status="Approved").aggregate(total_days=Sum('leave_days'))['total_days'] or 0
    availed_special_leave = user_leaves.filter(leave_type=3, status="Approved").aggregate(total_days=Sum('leave_days'))['total_days'] or 0
    availed_casual_leave = user_leaves.filter(leave_type=2, status="Approved").aggregate(total_days=Sum('leave_days'))['total_days'] or 0
    # Balance Calculation
    balance_casual_leave = total_casual_leave - availed_casual_leave
    balance_sick_leave = total_sick_leave - availed_sick_leave
    balance_lwp = total_lwp - availed_lwp
    balance_special_leave = total_special_leave - availed_special_leave
    leaves = Leave_Type.objects.all()
    context = {
        "total_sick_leave": total_sick_leave,
        "total_lwp": total_lwp,
        "total_special_leave": total_special_leave,
        "availed_sick_leave": availed_sick_leave,
        "availed_lwp": availed_lwp,
        "availed_special_leave": availed_special_leave,
        "balance_sick_leave": balance_sick_leave,
        "balance_lwp": balance_lwp,
        "balance_special_leave": balance_special_leave,
        "leaves": leaves,
        "total_casual_leave": total_casual_leave,
        "availed_casual_leave": availed_casual_leave,
        "balance_casual_leave": balance_casual_leave
    }
    return render(request, 'index2.html', context)
def dash_v3(request) :
    return render(request, 'index3.html')
def widgets(request) :
    return render(request, 'widgets.html')
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
    return render(request, 'configuration/leave_settings.html')

def holiday_list(request):
    return render(request, 'configuration/holiday_list.html')

def upload_handbook(request):
    return render(request, 'configuration/upload_handbook.html')

def assets(request):
    return render(request, 'configuration/assets.html')
