from django.core.management.base import BaseCommand
from django.utils import timezone
from hr_app.models import ExitRequest  # Make sure to use your app's name


class Command(BaseCommand):
    help = 'Checks for approved exits and deactivates employees whose last working day has passed.'

    def handle(self, *args, **options):
        today = timezone.now().date()
        self.stdout.write(f"[{today}] Running employee deactivation process...")

        # Find all requests that are finally APPROVED but whose employee is still active.
        # This ensures we don't process the same person over and over.
        # Assumes your AddEmployee model links to a User model with `user.is_active`
        requests_to_process = ExitRequest.objects.filter(
            status='APPROVED',
            employee__user__is_active=True
        )

        deactivated_count = 0
        for req in requests_to_process:
            # This logic directly implements your requirement:
            # Use 'actual_last_working_day' if it exists, otherwise fall back to 'expected_last_working_day'.
            last_day = req.actual_last_working_day or req.expected_last_working_day

            if last_day and last_day < today:
                employee_user = req.employee.user
                employee_user.is_active = False
                employee_user.save()

                # If your AddEmployee model also has an active status, update it too.
                # req.employee.is_active = False
                # req.employee.save()

                self.stdout.write(self.style.SUCCESS(
                    f"Deactivated employee: {req.employee.full_name} (User: {employee_user.username}) "
                    f"whose last day was {last_day}."
                ))
                deactivated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Process complete. Deactivated {deactivated_count} user(s)."))