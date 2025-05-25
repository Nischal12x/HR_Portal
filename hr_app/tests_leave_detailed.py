from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import AddEmployee, Role, Leave_Type, LeaveApplication
from datetime import date

class LeaveManagementDetailedTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.role_employee = Role.objects.create(name='Employee')
        self.role_hr = Role.objects.create(name='HR')

        # Create employee user
        self.employee = AddEmployee.objects.create(
            full_name='Test Employee',
            email='employee@example.com',
            phone='1234567890',
            dob='1990-01-01',
            gender='Male',
            address='123 Employee St',
            employee_id='EMP100',
            department='IT',
            designation='Developer',
            joining_date='2020-01-01',
            salary=50000,
            employment_type='Full-Time',
            role=self.role_employee,
            is_active=True
        )

        # Create HR user
        self.hr = AddEmployee.objects.create(
            full_name='Test HR',
            email='hr@example.com',
            phone='0987654321',
            dob='1985-01-01',
            gender='Female',
            address='456 HR St',
            employee_id='HR001',
            department='HR',
            designation='HR Manager',
            joining_date='2015-01-01',
            salary=70000,
            employment_type='Full-Time',
            role=self.role_hr,
            is_active=True
        )

        # Create leave type
        self.leave_type = Leave_Type.objects.create(
            leavetype='Annual Leave',
            leave_code='AL',
            leave_privilege='Paid',
            applied_to='All',
            leave_time=12,
            leave_time_unit='Months',
            is_active=True
        )

    def test_employee_apply_leave_valid(self):
        """
        Employee applies for leave with valid data.
        """
        self.client.force_login(self.employee.user) if self.employee.user else None
        response = self.client.post(reverse('apply_leave'), {
            'from_date': '2024-07-01',
            'till_date': '2024-07-05',
            'reason': 'Family vacation',
            'leave_type': self.leave_type.id,
        })
        self.assertEqual(response.status_code, 302)  # Redirect on success
        leave_app = LeaveApplication.objects.filter(employee=self.employee).last()
        self.assertIsNotNone(leave_app)
        self.assertEqual(leave_app.status, 'Pending')

    def test_employee_apply_leave_invalid_dates(self):
        """
        Employee applies for leave with from_date after till_date.
        """
        self.client.force_login(self.employee.user) if self.employee.user else None
        response = self.client.post(reverse('apply_leave'), {
            'from_date': '2024-07-10',
            'till_date': '2024-07-05',
            'reason': 'Invalid date test',
            'leave_type': self.leave_type.id,
        })
        self.assertEqual(response.status_code, 302)  # Redirect due to error
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("From date cannot be after till date." in str(m) for m in messages))

    def test_hr_approve_leave(self):
        """
        HR approves a pending leave application.
        """
        leave_app = LeaveApplication.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            from_date=date(2024, 7, 1),
            till_date=date(2024, 7, 5),
            reason='Vacation',
            status='Pending',
            leave_days=5
        )
        self.client.force_login(self.hr.user) if self.hr.user else None
        response = self.client.post(reverse('update_leave_status', args=[leave_app.id]), {
            'status': 'Approved'
        })
        self.assertEqual(response.status_code, 302)
        leave_app.refresh_from_db()
        self.assertEqual(leave_app.status, 'Approved')

    def test_create_new_leave_type(self):
        """
        HR creates a new leave type and verifies it is active.
        """
        self.client.force_login(self.hr.user) if self.hr.user else None
        response = self.client.post(reverse('add_leave'), {
            'leaveName': 'Sick Leave',
            'code': 'SL',
            'leaveType': 'Paid',
            'effective_after': 0,
            'time_unit': 'Month',
            'accrual_enabled': 'on',
            'leave_time': 10,
            'leave_time_unit': 'Days',
            'accrual_frequency': 'Monthly',
            'count_weekends': 'True',
            'count_holidays': 'True',
            'employeeType': 'All'
        })
        self.assertEqual(response.status_code, 302)
        leave_type = Leave_Type.objects.filter(leave_code='SL').first()
        self.assertIsNotNone(leave_type)
        self.assertTrue(leave_type.is_active)

    # Additional detailed test cases can be added here following the same pattern
