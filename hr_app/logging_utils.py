import logging
import os
from django.conf import settings
from django.utils import timezone

# Ensure base user logs directory exists when this module is loaded
os.makedirs(settings.USER_LOGS_BASE_DIR, exist_ok=True)


class UserEmailFilter(logging.Filter):
    """Adds employee_email to the log record if not present."""

    def __init__(self, email="N/A"):
        super().__init__()
        self.email = email

    def filter(self, record):
        if not hasattr(record, 'employee_email'):
            record.employee_email = self.email
        return True


def get_user_logger(employee_id, employee_email="N/A"):
    """
    Configures and returns a logger for a specific employee.
    Logs will go to settings.USER_LOGS_BASE_DIR / <employee_id> / activity.log
    """
    logger_name = f"employee_activity.{employee_id}"
    logger = logging.getLogger(logger_name)

    # Prevent adding handlers multiple times if logger already exists
    if not logger.handlers:
        logger.setLevel(logging.INFO)  # Or your desired default level

        # Create directory for this user's logs if it doesn't exist
        user_log_dir = os.path.join(settings.USER_LOGS_BASE_DIR, str(employee_id))
        os.makedirs(user_log_dir, exist_ok=True)

        log_file_path = os.path.join(user_log_dir, 'activity.log')

        # File Handler
        # Use a simple FileHandler; rotation is handled by the archival script
        fh = logging.FileHandler(log_file_path, encoding='utf-8')

        # Formatter - Ensure it's readable
        # %(asctime)s - %(levelname)s - User: %(employee_email)s - %(message)s
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(employee_email)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Add filter to inject employee_email into records consistently
        # This ensures %(employee_email)s in the formatter works even if not passed in extra
        logger.addFilter(UserEmailFilter(employee_email))

    # If the logger existed, its filter might have the old email if it changed.
    # Update the email in the existing filter.
    for f in logger.filters:
        if isinstance(f, UserEmailFilter):
            f.email = employee_email
            break
    else:  # If no UserEmailFilter found (e.g., if logger was created without it)
        if not any(isinstance(f, UserEmailFilter) for f in logger.filters):
            logger.addFilter(UserEmailFilter(employee_email))

    return logger


def log_user_action(employee_id, employee_email, action_description, level=logging.INFO, **extra_info):
    """
    Convenience function to log an action for a user.
    """
    logger = get_user_logger(employee_id, employee_email)

    # Prepare extra context for structured logging if needed
    log_extra = {'employee_email': employee_email}  # Ensure email is in extra for formatter
    # for key, value in extra_info.items():
    #     log_extra[key] = value

    logger.log(level, action_description, extra=log_extra)