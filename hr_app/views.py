import re
from datetime import datetime, timezone, date
from django.utils import timezone

from django.core.files.storage import FileSystemStorage
from django.db.models import Sum
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Role, AddEmployee, LeaveApplication, Leave_Type

from .models import LeaveApplication


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
        lt = Leave_Type.objects.get(id=leave_type)
        leave_days = leave.save(half_day_map=half_day_map, sandwich=lt.count_weekends)
        leave.leave_days = leave_days
        leave.save()
        messages.success(request, "Leave applied successfully!")
        return redirect('index')


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
                today = timezone.now()  # Get today's date and time
                today = today.date()  # Keep only the date part (year-month-day)
            return render(request, "add_emp.html", {"employee": form_data, "roles": roles,'today': today,})

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
        employee.marital_status = request.POST.get('marital_status')
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


def leaves_sys(request):
    leaves = Leave_Type.objects.all()
    employee_data = []
    for leave in leaves:
        applications = LeaveApplication.objects.filter(
            leave_type=leave.id,
            status='Approved'
        )
        employees = AddEmployee.objects.filter(id__in=applications.values_list('employee_id', flat=True))

        for emp in employees:
            total_availed = applications.filter(employee=emp).aggregate(total=Sum('leave_days'))['total'] or 0
            leave_balance = float(leave.leave_time) - total_availed

            employee_data.append({
                "employee_name": emp.full_name,
                "accrual": f"{leave.leave_time} {leave.leave_time_unit}/ Yearly",
                "effective": leave.effective_after,
                "effective_from": "Yes",  # placeholder
                "weekend_leave": leave.count_weekends,
                "holiday_leave": leave.count_holidays,
                "leave_balance": leave_balance,
                "leave_availed": total_availed,
                "uploaded_on": emp.created_at if hasattr(emp, 'created_at') else timezone.now(),
                "leave_type_id": leave.id,
            })

    return render(request, 'leaves_sys.html', {
        'leaves': leaves,
        'employee_leave_data': employee_data,
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


def admins(request) :
    return render(request, 'index.html')

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
    leaves = Leave_Type.objects.all()

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
    return render(request, 'leave_settings.html')

def holiday_list(request):
    return render(request, 'configuration/holiday_list.html')

def upload_handbook(request):
    return render(request, 'configuration/upload_handbook.html')

def assets(request):
    return render(request, 'configuration/assets.html')
