from django import forms
from .models import AddEmployee
import datetime
import re
from django.utils import timezone

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

from django import forms
from .models import ExitRequest

class ResignationApplyForm(forms.ModelForm):
    resignation_apply_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'readonly': 'readonly'}),
        initial=timezone.now().date()
    )

    class Meta:
        model = ExitRequest
        fields = ['resignation_apply_date', 'reason_for_resignation', 'selected_elsewhere', 'bond_over', 'advance_salary', 'any_dues']
        widgets = {
            'reason_for_resignation': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'Please state your reason for resignation.'}),
        }

class ExitChecklistForm(forms.ModelForm):
    """
    Form for HR to manage the offboarding checklist items.
    This will be the 'checklist_form' in your HR view.
    CORRECTED: Removed 'actual_last_working_day' to avoid redundancy.
    """
    class Meta:
        model = ExitRequest
        fields = [
            'company_assets_returned',
            'knowledge_transfer_complete',
            'final_settlement_processed',
            'exit_interview_conducted',
        ]
        # Using CheckboxInput for a cleaner UI
        widgets = {
            'company_assets_returned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'knowledge_transfer_complete': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'final_settlement_processed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'exit_interview_conducted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ExitApprovalFormRM(forms.ModelForm):
    class Meta:
        model = ExitRequest
        fields = ['reporting_manager_remarks']
        widgets = {
            'reporting_manager_remarks': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Provide remarks for HR (optional)...'}),
        }


class ExitApprovalFormHR(forms.ModelForm):
    """
    Form for HR's main approval action: setting remarks and final LWD.
    This will be the 'approval_form' in your HR view.
    """

    class Meta:
        model = ExitRequest
        fields = ['hr_remarks', 'actual_last_working_day']
        widgets = {
            'hr_remarks': forms.Textarea(
                attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Add final HR remarks...'}),
            'actual_last_working_day': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        labels = {
            'actual_last_working_day': 'Actual Last Working Day',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make the date optional as it can be set later
        self.fields['actual_last_working_day'].required = False



from django import forms
from .models import Task

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'name', 'project', 'assignee', 'priority', 'start_date', 
            'end_date', 'description', 'document'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter task name'}),
            'project': forms.Select(attrs={'class': 'form-control select2'}),
            'assignee': forms.Select(attrs={'class': 'form-control select2'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'document': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date must be after or equal to the start date.")
            
        return cleaned_data