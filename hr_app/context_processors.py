# hr_app/context_processors.py
from .models import Notification, AddEmployee

def notifications_context(request):
    """
    Makes notification data available to all templates.
    - Provides 'unread_notifications' and 'unread_count' for EXISTING features.
    - Adds 'recent_notifications' and 'unread_notifications_count' for the NEW navbar dropdown.
    """
    if request.user.is_authenticated:
        try:
            employee_id = request.session.get('employee_id')
            if not employee_id:
                return {}
            
            # --- This is the most efficient way to get the data ---
            # 1. Get ALL notifications for the user just ONCE.
            all_notifications = Notification.objects.filter(user_id=employee_id)
            
            # 2. Get all UNREAD notifications from the main set.
            unread_notifications_qs = all_notifications.filter(is_read=False)

            # --- PREPARE THE DATA FOR YOUR EXISTING FEATURES (No change in behavior) ---
            # Your old feature needs the 5 most recent UNREAD notifications.
            existing_unread_list = unread_notifications_qs[:5]
            # Your old feature needs the count of all unread notifications.
            existing_unread_count = unread_notifications_qs.count()

            # --- PREPARE THE NEW DATA FOR THE NAVBAR DROPDOWN ---
            # The new navbar needs the 5 most RECENT notifications (read or unread).
            navbar_recent_list = all_notifications[:5]
            # The navbar badge just needs the unread count (we can reuse the variable).

            # --- Return ALL variables so nothing breaks ---
            return {
                # For your existing feature (names are unchanged)
                'unread_notifications': existing_unread_list,
                'unread_count': existing_unread_count,

                # For the new navbar dropdown
                'recent_notifications': navbar_recent_list,
                'unread_notifications_count': existing_unread_count,
            }

        except AddEmployee.DoesNotExist:
            return {}
            
    return {}