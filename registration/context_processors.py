from .views import get_all_notifications

def notifications_processor(request):
    """
    Context processor to add notifications to all templates.
    Only adds notifications for authenticated users.
    """
    if request.user.is_authenticated and request.session.get('user_email'):
        notifications = get_all_notifications(request)
    else:
        notifications = []
    return {'notifications': notifications}