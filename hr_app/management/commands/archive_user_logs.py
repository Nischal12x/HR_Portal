import os
import shutil
import zipfile
from datetime import datetime, date, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import EmailMessage  # For sending emails with attachments
from dateutil.relativedelta import relativedelta  # pip install python-dateutil
import logging # <--- ADD THIS LINE

class Command(BaseCommand):
    help = 'Archives user-specific activity logs into ZIP files, prepares for new logging, and optionally emails them.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--period',
            type=str,
            default=settings.LOG_ARCHIVE_PERIOD_DEFAULT,
            choices=['weekly', 'monthly', 'yearly', 'custom_days'],
            help='Archiving period: weekly, monthly, yearly, or custom_days (requires --days)'
        )
        parser.add_argument(
            '--days',
            type=int,
            help='Number of days for custom archive period (used if --period=custom_days)'
        )
        parser.add_argument(
            '--employee_id',
            type=str,
            default='all',
            help='Specific employee ID to archive logs for, or "all".'
        )
        parser.add_argument(
            '--send_email',
            action='store_true',  # Makes this a flag; if present, it's True
            help='Send an email with the archived logs to the configured recipient.'
        )
        parser.add_argument(
            '--recipient_email',
            type=str,
            default=settings.LOG_ARCHIVE_RECIPIENT_EMAIL,
            help='Override the recipient email address from settings.'
        )

    def handle(self, *args, **options):
        period_str = options['period']
        custom_days = options['days']
        target_employee_id_str = options['employee_id']
        should_send_email = options['send_email']
        recipient_email = options['recipient_email']

        if not os.path.exists(settings.USER_LOGS_BASE_DIR):
            self.stdout.write(self.style.WARNING(
                f"User logs directory {settings.USER_LOGS_BASE_DIR} does not exist. Nothing to archive or email."))
            return

        employee_ids_to_process = []
        if target_employee_id_str.lower() == 'all':
            employee_ids_to_process = [d for d in os.listdir(settings.USER_LOGS_BASE_DIR)
                                       if os.path.isdir(os.path.join(settings.USER_LOGS_BASE_DIR, d))]
        elif target_employee_id_str.isdigit():  # Basic check, could be more robust
            if os.path.isdir(os.path.join(settings.USER_LOGS_BASE_DIR, target_employee_id_str)):
                employee_ids_to_process.append(target_employee_id_str)
            else:
                self.stdout.write(
                    self.style.WARNING(f"No log directory found for employee ID {target_employee_id_str}."))
                return
        else:
            self.stdout.write(
                self.style.ERROR(f"Invalid employee_id: {target_employee_id_str}. Must be 'all' or a numeric ID."))
            return

        if not employee_ids_to_process:
            self.stdout.write("No employee log directories found to process.")
            return

        self.stdout.write(
            f"Starting log archival for period: {period_str} (custom days: {custom_days if custom_days else 'N/A'})")

        archived_zip_files = []  # To store paths of successfully created ZIPs

        for employee_id in employee_ids_to_process:
            self.stdout.write(f"Processing logs for employee ID: {employee_id}...")
            user_log_dir = os.path.join(settings.USER_LOGS_BASE_DIR, employee_id)
            current_log_file_path = os.path.join(user_log_dir, 'activity.log')

            if not os.path.exists(current_log_file_path) or os.path.getsize(current_log_file_path) == 0:
                self.stdout.write(f"  No activity.log found or it's empty for employee {employee_id}. Skipping.")
                continue

            today = date.today()
            period_name_for_file = ""  # For file naming and email subject
            if period_str == 'weekly':
                # e.g., week_ending_2023-10-29 (Sunday)
                period_name_for_file = f"week_ending_{today.strftime('%Y-%m-%d')}"
            elif period_str == 'monthly':
                period_name_for_file = f"month_{today.strftime('%Y-%m')}"
            elif period_str == 'yearly':
                period_name_for_file = f"year_{today.strftime('%Y')}"
            elif period_str == 'custom_days' and custom_days:
                period_name_for_file = f"custom_{custom_days}days_ending_{today.strftime('%Y-%m-%d')}"
            else:
                self.stdout.write(
                    self.style.ERROR(f"  Invalid period configuration for employee {employee_id}. Skipping."))
                continue

            archives_dir = os.path.join(user_log_dir, 'archives')
            os.makedirs(archives_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            log_to_archive_name = f"activity_archiving_{timestamp}.log"
            log_to_archive_path = os.path.join(user_log_dir, log_to_archive_name)

            try:
                logger_instance = logging.getLogger(f"employee_activity.{employee_id}")
                for handler in list(logger_instance.handlers):
                    if isinstance(handler, logging.FileHandler) and handler.baseFilename == current_log_file_path:
                        handler.close()
                        logger_instance.removeHandler(handler)

                shutil.move(current_log_file_path, log_to_archive_path)
                self.stdout.write(f"  Moved {current_log_file_path} to {log_to_archive_path} for archiving.")
            except FileNotFoundError:
                self.stdout.write(self.style.WARNING(
                    f"  {current_log_file_path} not found for employee {employee_id}. Skipping move."))
                continue
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  Error preparing log file for employee {employee_id}: {e}"))
                continue

            zip_filename = f"employee_{employee_id}_logs_{period_name_for_file}_{timestamp}.zip"
            zip_filepath = os.path.join(archives_dir, zip_filename)

            try:
                with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(log_to_archive_path, arcname=f"activity_log_{period_name_for_file}.log")  # Name inside zip
                self.stdout.write(self.style.SUCCESS(f"  Successfully created archive: {zip_filepath}"))
                archived_zip_files.append(zip_filepath)  # Add to list for emailing

                os.remove(log_to_archive_path)
                self.stdout.write(f"  Removed temporary log file: {log_to_archive_path}")
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  Error creating ZIP for employee {employee_id}: {e}"))
                self.stderr.write(
                    self.style.WARNING(f"  The log file {log_to_archive_path} was not zipped. Manual check needed."))

        # After processing all users, send email if requested and there are files
        if should_send_email and archived_zip_files:
            self.stdout.write(self.style.HTTP_INFO(
                f"Preparing to send email with {len(archived_zip_files)} archive(s) to {recipient_email}..."))

            email_subject = f"BISP HR Portal - User Activity Log Archives - {date.today().strftime('%Y-%m-%d')}"
            email_body = (
                f"Dear Admin,\n\n"
                f"Attached are the user activity log archives generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.\n\n"
                f"Period covered (based on script run): {period_str.capitalize()}\n\n"
                f"The following archive files are attached:\n"
            )
            for zip_file in archived_zip_files:
                email_body += f"- {os.path.basename(zip_file)}\n"

            email_body += "\nThese files are organized by employee ID within their names.\n\nRegards,\nBISP HR Portal System"

            try:
                email = EmailMessage(
                    subject=email_subject,
                    body=email_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,  # From "BISP" as configured in settings
                    to=[recipient_email],
                    # cc=['other@example.com'], # Optional CC
                )

                total_attachment_size = 0
                for zip_filepath in archived_zip_files:
                    total_attachment_size += os.path.getsize(zip_filepath)
                    email.attach_file(zip_filepath)

                # Gmail limit is ~25MB. Many other providers have similar or smaller limits.
                if total_attachment_size > 20 * 1024 * 1024:  # Roughly 20MB
                    self.stdout.write(self.style.WARNING(
                        f"Total attachment size ({total_attachment_size / (1024 * 1024):.2f} MB) is large. "
                        "Email delivery might fail. Consider archiving fewer users at once or an alternative delivery method."
                    ))

                email.send()
                self.stdout.write(self.style.SUCCESS(f"Successfully sent email with archives to {recipient_email}."))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed to send email: {e}"))
                self.stderr.write(
                    self.style.WARNING("Archive files remain locally in their respective user directories."))

        elif should_send_email and not archived_zip_files:
            self.stdout.write(self.style.WARNING("Email sending was requested, but no new log archives were created."))
            # Optionally, send an email stating no new logs if that's desired
            # ... (add logic here if you want a "no logs" email) ...

        self.stdout.write(self.style.SUCCESS("Log archival process finished."))