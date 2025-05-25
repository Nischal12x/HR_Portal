from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import AddEmployee, Role, Leave_Type, LeaveApplication, Project, Task, Timesheet, Holiday
from datetime import date, time

class EmployeeManagementTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name='Employee')
        self.employee = AddEmployee.objects.create(
            full_name='Test User',
            email='testuser@example.com',
            phone='1234567890',
            dob='1990-01-01',
            gender='Male',
            address='123 Test St',
            employee_id='EMP001',
            department='IT',
            designation='Developer',
            joining_date='2020-01-01',
            salary=50000,
            employment_type='Full-Time',
            role=self.role,
            is_active=True
        )
        self.client = Client()

    def test_employee_creation(self):
        self.assertEqual(self.employee.full_name, 'Test User')
        self.assertTrue(self.employee.is_active)

    def test_employee_list_view(self):
        response = self.client.get(reverse('employee_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test User')

class LeaveManagementTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name='Employee')
        self.employee = AddEmployee.objects.create(
            full_name='Leave User',
            email='leaveuser@example.com',
            phone='0987654321',
            dob='1990-01-01',
            gender='Female',
            address='456 Leave St',
            employee_id='EMP002',
            department='HR',
            designation='HR Manager',
            joining_date='2019-01-01',
            salary=60000,
            employment_type='Full-Time',
            role=self.role,
            is_active=True
        )
        self.leave_type = Leave_Type.objects.create(
            leavetype='Annual Leave',
            leave_code='AL',
            leave_privilege='Paid',
            applied_to='All',
            leave_time=12,
            leave_time_unit='Months',
            is_active=True
        )
        self.leave_application = LeaveApplication.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            from_date=date.today(),
            till_date=date.today(),
            reason='Vacation',
            status='Pending',
            leave_days=1
        )
        self.client = Client()

    def test_leave_application_creation(self):
        self.assertEqual(self.leave_application.reason, 'Vacation')
        self.assertEqual(self.leave_application.status, 'Pending')

    def test_leave_dashboard_view(self):
        response = self.client.get(reverse('leave_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Annual Leave')

class ProjectManagementTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name='Project Manager')
        self.leader = AddEmployee.objects.create(
            full_name='Project Leader',
            email='leader@example.com',
            phone='1112223333',
            dob='1985-01-01',
            gender='Male',
            address='789 Project St',
            employee_id='EMP003',
            department='IT',
            designation='Project Manager',
            joining_date='2018-01-01',
            salary=70000,
            employment_type='Full-Time',
            role=self.role,
            is_active=True
        )
        self.project = Project.objects.create(
            name='Test Project',
            client='Test Client',
            start_date=date.today(),
            end_date=date.today(),
            currency='rs',
            rate_status='billable',
            rate=1000,
            priority='high',
            leader=self.leader,
            admin=self.leader,
            description='Test project description'
        )
        self.client = Client()

    def test_project_creation(self):
        self.assertEqual(self.project.name, 'Test Project')
        self.assertEqual(self.project.client, 'Test Client')

    def test_project_view(self):
        response = self.client.get(reverse('project', args=[self.project.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Project')

class TaskManagementTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name='Project Manager')
        self.leader = AddEmployee.objects.create(
            full_name='Task Leader',
            email='taskleader@example.com',
            phone='4445556666',
            dob='1980-01-01',
            gender='Female',
            address='101 Task St',
            employee_id='EMP004',
            department='IT',
            designation='Project Manager',
            joining_date='2017-01-01',
            salary=75000,
            employment_type='Full-Time',
            role=self.role,
            is_active=True
        )
        self.project = Project.objects.create(
            name='Task Project',
            client='Task Client',
            start_date=date.today(),
            end_date=date.today(),
            currency='usd',
            rate_status='non billable',
            rate=0,
            priority='medium',
            leader=self.leader,
            admin=self.leader,
            description='Task project description'
        )
        self.task = Task.objects.create(
            name='Test Task',
            project=self.project,
            assignee=self.leader,
            priority='Medium',
            start_date=date.today(),
            end_date=date.today(),
            status='Pending',
            description='Test task description'
        )
        self.client = Client()

    def test_task_creation(self):
        self.assertEqual(self.task.name, 'Test Task')
        self.assertEqual(self.task.status, 'Pending')

    def test_task_list_view(self):
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Task')

class TimesheetManagementTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name='Employee')
        self.employee = AddEmployee.objects.create(
            full_name='Timesheet User',
            email='timesheetuser@example.com',
            phone='7778889999',
            dob='1992-01-01',
            gender='Male',
            address='202 Timesheet St',
            employee_id='EMP005',
            department='IT',
            designation='Developer',
            joining_date='2021-01-01',
            salary=55000,
            employment_type='Full-Time',
            role=self.role,
            is_active=True
        )
        self.project = Project.objects.create(
            name='Timesheet Project',
            client='Timesheet Client',
            start_date=date.today(),
            end_date=date.today(),
            currency='rs',
            rate_status='billable',
            rate=1200,
            priority='low',
            leader=self.employee,
            admin=self.employee,
            description='Timesheet project description'
        )
        self.task = Task.objects.create(
            name='Timesheet Task',
            project=self.project,
            assignee=self.employee,
            priority='Low',
            start_date=date.today(),
            end_date=date.today(),
            status='Pending',
            description='Timesheet task description'
        )
        self.timesheet = Timesheet.objects.create(
            employee=self.employee,
            day='Monday',
            date=date.today(),
            project=self.project,
            task=self.task,
            start_time=time(9, 0),
            end_time=time(17, 0),
            description='Worked on testing',
        )
        self.client = Client()

    def test_timesheet_creation(self):
        self.assertEqual(self.timesheet.description, 'Worked on testing')
        self.assertEqual(self.timesheet.employee.full_name, 'Timesheet User')

    def test_timesheet_view(self):
        response = self.client.get(reverse('view_timesheet'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Timesheet User')

class HolidayManagementTests(TestCase):
    def setUp(self):
        self.holiday = Holiday.objects.create(
            name='Test Holiday',
            date=date.today(),
            description='Test holiday description'
        )
        self.client = Client()

    def test_holiday_creation(self):
        self.assertEqual(self.holiday.name, 'Test Holiday')
        self.assertEqual(self.holiday.description, 'Test holiday description')

    def test_holiday_dashboard_view(self):
        response = self.client.get(reverse('holiday_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Holiday')
