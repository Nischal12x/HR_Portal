from django.db import models
import uuid
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, MaxLengthValidator, FileExtensionValidator
from datetime import timedelta

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Leave_Type(models.Model) :
    leavetype = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.leavetype

def validate_file_size(value):
    """Ensure file size is below 2MB."""
    limit = 2 * 1024 * 1024  # 2MB
    if value.size > limit:
        raise ValidationError("File size must not exceed 2MB.")


class LeaveApplication(models.Model):
    employee = models.ForeignKey('AddEmployee', on_delete=models.CASCADE, to_field='id', null=False)
    leave_type = models.CharField(max_length=50)
    from_date = models.DateField()
    till_date = models.DateField()
    reason = models.TextField(
        validators=[
            MinLengthValidator(10, "Reason must be at least 10 characters."),
            MaxLengthValidator(500, "Reason cannot exceed 500 characters."),
        ]
    )
    applied_at = models.DateTimeField(default=timezone.now, blank=True)
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

    def calculate_total_leave_days(self, half_day_map=None):
        total_days = (self.till_date - self.from_date).days + 1
        leave_count = 0.0

        for i in range(total_days):
            current_date = self.from_date + timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")

            if half_day_map and date_str in half_day_map:
                if half_day_map[date_str] in ['first_half', 'second_half']:
                    leave_count += 0.5
                else:
                    leave_count += 1
            else:
                leave_count += 1

        return leave_count

    def save(self, *args, **kwargs):
        # Optional: receive half-day info from kwargs
        half_day_map = kwargs.pop('half_day_map', None)
        leave_days = self.calculate_total_leave_days(half_day_map)

        super().save(*args, **kwargs)

        # Update employee's leave balance
        self.employee.update_leave_balance(leave_days)
        return leave_days

class AddEmployee(models.Model):
    # Personal Details
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    dob = models.DateField()
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)

    address = models.TextField()

    # Job Details
    employee_id = models.CharField(max_length=20, unique=True)

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

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    total_leaves = models.FloatField(default=12)
    availed_leaves = models.FloatField(default=0)
    available_leaves = models.FloatField(default=12.0)  # 👈 Add this

    def update_leave_balance(self, new_availed):
        self.availed_leaves += new_availed
        self.available_leaves = max(self.total_leaves - self.availed_leaves, 0)
        self.save()

    def __str__(self):
        return f"{self.full_name} - {self.employee_id}"


