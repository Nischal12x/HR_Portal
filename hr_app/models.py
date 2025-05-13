from django.db import models
import uuid
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, MaxLengthValidator, FileExtensionValidator
from datetime import timedelta


# models.py
from django.db import models
from django.contrib.auth.models import User  # Import the User model

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
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    nationality = models.CharField(max_length=50)
    dob = models.DateField()
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
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

    def __str__(self):
        return f"{self.full_name} - {self.employee_id}"


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
    team_members = models.ManyToManyField(AddEmployee, related_name='team_projects', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    document = models.FileField(upload_to='project_docs/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

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