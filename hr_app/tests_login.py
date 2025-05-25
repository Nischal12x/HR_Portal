from django.test import TestCase, Client
from django.urls import reverse
from .models import AddEmployee, Role

class LoginTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name='Employee')
        self.employee = AddEmployee.objects.create(
            full_name='Login User',
            email='loginuser@example.com',
            phone='1234567890',
            dob='1990-01-01',
            gender='Male',
            address='123 Login St',
            employee_id='EMP100',
            department='IT',
            designation='Developer',
            joining_date='2020-01-01',
            salary=50000,
            employment_type='Full-Time',
            role=self.role,
            is_active=True
        )
        self.client = Client()

    def test_login_valid(self):
        # Create a user linked to employee for authentication
        user = self.employee.user
        if not user:
            from django.contrib.auth.models import User
            user = User.objects.create_user(username='loginuser', password='TestPass123')
            self.employee.user = user
            self.employee.save()

        login = self.client.login(username='loginuser', password='TestPass123')
        self.assertTrue(login)

    def test_login_invalid_password(self):
        response = self.client.post(reverse('login'), {'email': self.employee.email, 'password': 'WrongPass'})
        self.assertContains(response, "Incorrect password!")

    def test_login_deactivated_user(self):
        self.employee.is_active = False
        self.employee.save()
        response = self.client.post(reverse('login'), {'email': self.employee.email, 'password': 'TestPass123'})
        self.assertContains(response, "Your account has been deactivated.")
