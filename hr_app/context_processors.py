# hr_app/context_processors.py
from .models import Notification


def notifications_context(request):
    if request.user.is_authenticated:
        # Get the ID of the logged-in employee from the session
        employee_id = request.session.get('employee_id')
        if employee_id:
            # Fetch the 5 most recent unread notifications for the dropdown
            unread_notifications = Notification.objects.filter(user_id=employee_id, is_read=False)[:5]
            # Get the total count of unread notifications for the badge
            unread_count = Notification.objects.filter(user_id=employee_id, is_read=False).count()

            return {
                'unread_notifications': unread_notifications,
                'unread_count': unread_count,
            }
    return {}