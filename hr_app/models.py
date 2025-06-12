from django.db import models
import uuid
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, MaxLengthValidator, FileExtensionValidator
from datetime import timedelta


# models.py
from django.db import models
from django.contrib.auth.models import User  # Import the User model
from dateutil.relativedelta import relativedelta




class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Leave_Type(models.Model):
    LEAVE_CHOICES = [('Paid', 'Paid'), ('Unpaid', 'Unpaid')]
    TIME_UNIT_CHOICES = [('Day', 'Day'), ('Month', 'Month'), ('Year', 'Year')]
    LEAVE_TIME_UNIT_CHOICES = [('Days', 'Days'), ('Hours', 'Hours')]
    ACCRUAL_FREQUENCY_CHOICES = [('Monthly', 'Monthly'), ('Yearly', 'Yearly')]

    is_active = models.BooleanField(default=True)
    leavetype = models.CharField(max_length=50, unique=True)
    leave_code = models.CharField(max_length=50, unique=True, default=None)
    leave_privilege = models.CharField(max_length=20, choices=LEAVE_CHOICES, default='Paid')
    applied_to = models.CharField(max_length=20, default='All')
    # Entitlement settings
    effective_after = models.PositiveIntegerField(null=True, blank=True)
    time_unit = models.CharField(max_length=10, choices=TIME_UNIT_CHOICES, null=True, blank=True)
    from_date_reference = models.CharField(max_length=50, null=True, blank=True)
    accrual_enabled = models.BooleanField(default=False)
    leave_time = models.PositiveIntegerField(null=True, blank=True)
    leave_time_unit = models.CharField(max_length=10, choices=LEAVE_TIME_UNIT_CHOICES, null=True, blank=True)
    accrual_frequency = models.CharField(max_length=10, choices=ACCRUAL_FREQUENCY_CHOICES, null=True, blank=True)

    # Restriction settings
    count_weekends = models.BooleanField(default=True)
    count_holidays = models.BooleanField(default=True)

    # Many-to-Many relationship with User (Individual)

    def __str__(self):
        return self.leavetype

def validate_file_size(value):
    """Ensure file size is below 2MB."""
    limit = 2 * 1024 * 1024  # 2MB
    if value.size > limit:
        raise ValidationError("File size must not exceed 2MB.")


class LeaveApplication(models.Model):
    employee = models.ForeignKey('AddEmployee', on_delete=models.CASCADE, to_field='id', null=False)
    leave_type = models.ForeignKey(Leave_Type, on_delete=models.CASCADE)  # ✅ this is the goal
    from_date = models.DateField()
    till_date = models.DateField()
    reason = models.TextField(
        validators=[
            MinLengthValidator(10, "Reason must be at least 10 characters."),
            MaxLengthValidator(500, "Reason cannot exceed 500 characters."),
        ]
    )
    attachment = models.FileField(
        upload_to="leave_attachments/",
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf", "doc", "docx", "jpg", "png"]),
            validate_file_size
        ]
    )

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Withdrawn', 'Withdrawn'),
    ]
    leave_days = models.FloatField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    approved_by = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.employee.name} - {self.leave_type} ({self.from_date} to {self.till_date})"

    def clean(self):
        if self.till_date < self.from_date:
            raise ValidationError({"till_date": "Till date cannot be earlier than from date."})

    def calculate_total_leave_days(self, half_day_map=None, exclude_sandwich_sundays=False):
        total_days = (self.till_date - self.from_date).days + 1
        leave_count = 0.0

        for i in range(total_days):
            current_date = self.from_date + timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")
            is_sunday = current_date.weekday() == 6  # Sunday is 6

            # Always exclude if from_date or till_date is Sunday
            if (i == 0 or i == total_days - 1) and is_sunday:
                continue

            # Exclude in-between Sundays only if the flag is True
            if is_sunday and exclude_sandwich_sundays:
                continue

            # Handle half-day logic
            if half_day_map and date_str in half_day_map:
                if half_day_map[date_str] in ['first_half', 'second_half']:
                    leave_count += 0.5
                else:
                    leave_count += 1
            else:
                leave_count += 1

        return leave_count

    def save(self, *args, **kwargs):
        half_day_map = kwargs.pop('half_day_map', None)
        sandwich = kwargs.pop('sandwich', False)  # fallback to False if not provided

        leave_days = self.calculate_total_leave_days(half_day_map=half_day_map, exclude_sandwich_sundays=not sandwich)

        super().save(*args, **kwargs)

        return leave_days

class AddEmployee(models.Model):
    # Personal Details
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    nationality = models.CharField(max_length=50)
    dob = models.DateField()
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    failed_login_attempts = models.IntegerField(default=0)
    lockout_until = models.DateTimeField(null=True, blank=True)
    reporting_manager = models.ForeignKey(
        User,  # Assuming managers are also Users
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reportees',
        help_text="The manager this employee reports to."
    )
    MARITAL_CHOICES = [
        ('Single', 'Single'),
        ('Married', 'Married'),
    ]
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    marital_status = models.CharField(
    max_length=10,
    choices=MARITAL_CHOICES,
    default='Single'
    )
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)

    address = models.TextField()

    # Job Details
    employee_id = models.CharField(max_length=50, unique=True)

    DEPARTMENT_CHOICES = [
        ('IT', 'IT'),
        ('HR', 'HR'),
        ('Marketing', 'Marketing'),
        ('Finance', 'Finance'),
    ]
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES)

    designation = models.CharField(max_length=50)
    joining_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    EMPLOYMENT_TYPE_CHOICES = [
        ('Full-Time', 'Full-Time'),
        ('Part-Time', 'Part-Time'),
        ('Contract', 'Contract'),
    ]
    employment_type = models.CharField(max_length=15, choices=EMPLOYMENT_TYPE_CHOICES)
    attachment = models.FileField(upload_to="attachments/", null=True, blank=True)
    marital_status = models.CharField(
        choices=[('Single', 'Single'), ('Married', 'Married')],
        default='Single',
        max_length=10
    )
    is_active = models.BooleanField(default=True)

    def is_locked(self):
        """Checks if the account is currently locked."""
        if self.lockout_until and self.lockout_until > timezone.now():
            return True
        return False

    def time_until_unlock(self):
        """Returns a human-readable string of how long until unlock, or None."""
        if self.is_locked():
            remaining_time = self.lockout_until - timezone.now()
            # Format remaining_time as needed (e.g., "1 hour 30 minutes")
            total_seconds = int(remaining_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            parts = []
            if hours > 0:
                parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
            if minutes > 0:
                parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
            if not parts and seconds > 0:  # Only show seconds if no hours/minutes
                parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")
            if not parts:  # Should not happen if is_locked is true, but as a fallback
                return "soon"
            return ", ".join(parts)
        return None
    def __str__(self):
        return f"{self.full_name} - {self.employee_id}"


# employee/models.py (continued)

class ExitRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING_RM_APPROVAL', 'Pending Reporting Manager Approval'),
        ('PENDING_HR_APPROVAL', 'Pending HR Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED_BY_RM', 'Rejected by Reporting Manager'),
        ('REJECTED_BY_HR', 'Rejected by HR'),
        ('WITHDRAWN', 'Withdrawn by Employee'),
    ]

    employee = models.ForeignKey(AddEmployee, on_delete=models.CASCADE, related_name='exit_requests')
    email_subject = models.CharField(max_length=255, null=True, blank=True,
                                     help_text="The subject line of the resignation email.")
    resignation_apply_date = models.DateField(default=timezone.now)
    reason_for_resignation = models.TextField()
    expected_last_working_day = models.DateField()  # Calculated on submission
    actual_last_working_day = models.DateField(null=True, blank=True)  # Can be adjusted by HR/Manager

    notice_period_months = models.PositiveIntegerField(default=3, help_text="Default notice period in months")

    # Checklist items (can be expanded)
    company_assets_returned = models.BooleanField(default=False,
                                                  verbose_name="Company Assets Returned (Laptop, ID, etc.)")
    knowledge_transfer_complete = models.BooleanField(default=False,
                                                      verbose_name="Knowledge Transfer / Handover Complete")
    final_settlement_processed = models.BooleanField(default=False, verbose_name="Final Settlement Processed")
    exit_interview_conducted = models.BooleanField(default=False, verbose_name="Exit Interview Conducted")
    # Add more checklist items as needed
    # Example: access_revoked = models.BooleanField(default=False, verbose_name="System Access Revoked")

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING_RM_APPROVAL')

    # Approval tracking
    reporting_manager_remarks = models.TextField(null=True, blank=True)
    reporting_manager_approved_at = models.DateTimeField(null=True, blank=True)
    hr_remarks = models.TextField(null=True, blank=True)
    hr_approved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    #form submission
    selected_elsewhere = models.BooleanField(default=False)
    bond_over = models.BooleanField(default=False)
    advance_salary = models.BooleanField(default=False)
    any_dues = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk and not self.expected_last_working_day:  # If creating and LWD not set
            # Calculate last working day: apply date + notice period
            self.expected_last_working_day = self.resignation_apply_date + relativedelta(
                months=+self.notice_period_months)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Exit Request for {self.employee.full_name} - {self.status}"

    class Meta:
        ordering = ['-created_at']

class Holiday(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField(unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.date})"

class EmployeeHistory(models.Model):
    employee = models.ForeignKey(AddEmployee, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    nationality = models.CharField(max_length=50)
    dob = models.DateField()
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    marital_status = models.CharField(max_length=10, choices=[('Single', 'Single'), ('Married', 'Married')])
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    address = models.TextField()
    employee_code = models.CharField(max_length=50)  # ← renamed from employee_id
    department = models.CharField(max_length=20)
    designation = models.CharField(max_length=50)
    joining_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    employment_type = models.CharField(max_length=15)
    attachment = models.FileField(upload_to="attachments/", null=True, blank=True)

    # History fields
    created_at = models.DateTimeField()
    until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"History for {self.employee.full_name} (from {self.created_at} until {self.until or 'now'})"



class Project(models.Model):
    RATE_STATUS = [
        ('billable', 'Billable'),
        ('non billable', 'Non Billable')
    ]

    CURRENCY_CHOICES = [
        ('rs', 'Rs'),
        ('usd', 'USD ($)'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    name = models.CharField(max_length=255)
    client = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='rs')
    rate_status = models.CharField(max_length=50, choices=RATE_STATUS, default="non billable")
    rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    leader = models.ForeignKey(AddEmployee, on_delete=models.SET_NULL, related_name='leading_projects', null=True)
    admin = models.ForeignKey(AddEmployee, on_delete=models.SET_NULL, related_name='admin_projects', null=True)
    team_members = models.ManyToManyField(AddEmployee, related_name='team_projects', blank=True)
    description = models.TextField(blank=True, null=True)
    document = models.FileField(upload_to='project_docs/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# models.py
class ProjectHistory(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    client = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    currency = models.CharField(max_length=3)
    rate_status = models.CharField(max_length=50)
    rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    priority = models.CharField(max_length=10)
    leader = models.ForeignKey(AddEmployee, on_delete=models.SET_NULL, related_name='project_history_leader', null=True)
    admin = models.ForeignKey(AddEmployee, on_delete=models.SET_NULL, related_name='project_history_admin', null=True)
    description = models.TextField(blank=True, null=True)
    document = models.FileField(upload_to='project_history_docs/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)  # When this version became active
    until = models.DateTimeField(null=True, blank=True)   # When this version was replaced

    def __str__(self):
        return f"{self.name} - History @ {self.created_at}"


from django.db import models
from django.utils import timezone

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Claimed Completed', 'Claimed Completed'),
    ]

    name = models.CharField(max_length=255)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='tasks')
    assignee = models.ForeignKey('AddEmployee', on_delete=models.SET_NULL, null=True, related_name='tasks')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    description = models.TextField(blank=True, null=True)
    document = models.FileField(upload_to='tasks/documents/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Timesheet(models.Model):
    WEEKDAYS = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]

    employee = models.ForeignKey(AddEmployee, on_delete=models.CASCADE, related_name='timesheets')
    day = models.CharField(max_length=10, choices=WEEKDAYS)
    date = models.DateField()
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, related_name='timesheet_entries')
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, related_name='timesheet_entries')
    start_time = models.TimeField()
    end_time = models.TimeField()
    description = models.TextField()
    attachment = models.FileField(
        upload_to='attachments/',
        null=True,
        blank=True,
        validators=[validate_file_size]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} - {self.project.name if self.project else 'No Project'}"

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")

    class Meta:
        verbose_name = 'Timesheet Entry'
        verbose_name_plural = 'Timesheet Entries'
        ordering = ['-date']

class ImageTimesheet(models.Model):
    employee = models.ForeignKey(AddEmployee, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    image = models.FileField(upload_to='timesheet_images/')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.start_date} to {self.end_date}"

from django.db import models
from django.contrib.auth.models import User

class EmployeeHandbook(models.Model):
    title = models.CharField(max_length=255, default='Employee Handbook')
    file = models.FileField(upload_to='handbooks/')
    version = models.CharField(max_length=20, unique=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} (v{self.version})"


class EmployeeHandbookAcknowledgement(models.Model):
    employee = models.ForeignKey(AddEmployee, on_delete=models.CASCADE)
    handbook = models.ForeignKey(EmployeeHandbook, on_delete=models.CASCADE)
    acknowledged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'handbook')

    def __str__(self):
        return f"{self.employee.full_name} acknowledged {self.handbook.version} on {self.acknowledged_at}"

# models.py
import uuid
from django.utils import timezone

class PasswordResetToken(models.Model):
    employee = models.ForeignKey(AddEmployee, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(hours=1)

from django.db import models
import uuid
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, MaxLengthValidator, FileExtensionValidator
from datetime import timedelta

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('P', 'Present'),
        ('A', 'Absent'),
        ('L', 'Leave'),
        ('H', 'Holiday'),
    ]
    leave_days = models.FloatField(default=0)
    approved_by = models.CharField(max_length=100, null=True, blank=True)

    employee = models.ForeignKey('AddEmployee', on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} - {self.project.name if self.project else 'No Project'}"

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

from django.db import models
from django.conf import settings # To link to the User model

class CalendarEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True) # Optional end time
    all_day = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True) # Optional description
    color = models.CharField(max_length=20, default='#3c8dbc') # Increased max_length to 20 to fix Data too long error

    def __str__(self):
        return f"{self.title} ({self.user.username})"

    class Meta:
        verbose_name = "Calendar Event"
        verbose_name_plural = "Calendar Events"

from django.db import models
from decimal import Decimal


class SalaryData(models.Model):
    # If you have an Employee model and want a ForeignKey relationship
    employee_identifier = models.ForeignKey(AddEmployee, on_delete=models.CASCADE, related_name='salary_records')

    # If you are just storing the employee identifier from the CSV directly
    # employee_identifier = models.CharField(max_length=100) # Match this with employee_id_str

    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    payslip_code = models.CharField(max_length=50, blank=True, null=True)
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    hra = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    da = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_salary = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    present_days = models.PositiveSmallIntegerField(default=0)
    paid_leaves = models.PositiveSmallIntegerField(default=0)
    unpaid_leaves = models.PositiveSmallIntegerField(default=0)
    # Earnings and deductions
    project_incentive = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    variable_pay = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    esi = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    pf = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tds = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        unique_together = ('employee_identifier', 'month', 'year') # Ensures one record per employee per month/year
        verbose_name = "Salary Data"
        verbose_name_plural = "Salary Data"

    def __str__(self):
        return f"Salary for {self.employee_identifier} - {self.month:02d}/{self.year}"

# You will need a new model to track activity on a request.
# Add this to your models.py
class ExitActivityLog(models.Model):
    exit_request = models.ForeignKey(ExitRequest, on_delete=models.CASCADE, related_name='activity_logs')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.action} on {self.exit_request.employee.full_name} at {self.timestamp}'