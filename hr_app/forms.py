from django import forms
from .models import AddEmployee
import datetime
import re

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = AddEmployee
        fields = [
            'full_name', 'email', 'phone', 'dob', 'gender', 'address',
            'marital_status', 'nationality', 'employee_id', 'department',
            'designation', 'joining_date', 'salary', 'employment_type',
            'attachment', 'role'
        ]

    def clean_full_name(self):
        name = self.cleaned_data.get('full_name')
        if not re.match(r"^[a-zA-Z\s]+$", name):
            raise forms.ValidationError("Full name should only contain letters and spaces.")
        return name

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("Email is required.")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise forms.ValidationError("Enter a valid email address.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.match(r'^\d{10}$', phone):
            raise forms.ValidationError("Phone number must be 10 digits.")
        return phone

    def clean_dob(self):
        dob = self.cleaned_data.get('dob')
        today = datetime.date.today()
        age_in_days = (today - dob).days

        if dob >= today:
            raise forms.ValidationError("Date of birth must be in the past.")
        elif age_in_days < 18 * 365:
            raise forms.ValidationError("Employee must be at least 18 years old.")
        elif age_in_days > 50 * 365:
            raise forms.ValidationError("Employee must not be older than 50 years.")

        return dob

    def clean_gender(self):
        gender = self.cleaned_data.get('gender')
        if gender not in ['Male', 'Female', 'Other']:
            raise forms.ValidationError("Invalid gender selected.")
        return gender

    def clean_address(self):
        address = self.cleaned_data.get('address')
        if len(address) < 10:
            raise forms.ValidationError("Address should be at least 10 characters long.")
        return address

    def clean_marital_status(self):
        status = self.cleaned_data.get('marital_status')
        if status not in ['Single', 'Married']:
            raise forms.ValidationError("Invalid marital status selected.")
        return status

    def clean_nationality(self):
        nationality = self.cleaned_data.get('nationality')
        if not nationality:
            raise forms.ValidationError("Nationality is required.")
        if not re.match(r"^[a-zA-Z\s]+$", nationality):
            raise forms.ValidationError("Nationality must contain only letters and spaces.")
        return nationality

    def clean_salary(self):
        salary = self.cleaned_data.get('salary')
        if salary <= 0:
            raise forms.ValidationError("Salary must be a positive number.")
        return salary

    def clean_joining_date(self):
        joining_date = self.cleaned_data.get('joining_date')
        today = datetime.date.today()
        four_months_ago = today - datetime.timedelta(days=4 * 30)  # approx 4 months

        if joining_date < four_months_ago and joining_date < today:
            raise forms.ValidationError("Joining date must be within the last 4 months or in the future.")

        return joining_date

    def clean_employment_type(self):
        etype = self.cleaned_data.get('employment_type')
        if etype not in ['Full-Time', 'Part-Time', 'Contract']:
            raise forms.ValidationError("Invalid employment type selected.")
        return etype

    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        if not employee_id:
            raise forms.ValidationError("Employee ID (Password) is required.")

        # Password should be at least 8 characters long
        if len(employee_id) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")

        # Password should contain at least one number
        if not re.search(r'\d', employee_id):
            raise forms.ValidationError("Password must contain at least one number.")

        # Password should contain at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', employee_id):
            raise forms.ValidationError("Password must contain at least one special character.")

        return employee_id
