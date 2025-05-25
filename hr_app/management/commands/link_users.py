from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hr_app.models import AddEmployee


class Command(BaseCommand):
    help = 'Link AddEmployee to User even for dummy emails and set usable passwords.'

    def handle(self, *args, **kwargs):
        created, linked = 0, 0

        for emp in AddEmployee.objects.all():
            if not emp.user:
                username = emp.email  # Or use emp.employee_id if emails are duplicate
                user, is_new = User.objects.get_or_create(username=username, defaults={'email': emp.email})

                if is_new:
                    user.set_password(emp.employee_id)  # Set to employee_id
                    user.is_active = True
                    user.save()
                    created += 1
                else:
                    # Ensure password is usable
                    if not user.has_usable_password():
                        user.set_password(emp.employee_id)
                        user.is_active = True
                        user.save()

                emp.user = user
                emp.save()
                linked += 1

        self.stdout.write(self.style.SUCCESS(f"{linked} employees linked. {created} new users created."))
