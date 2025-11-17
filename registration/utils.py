from django.contrib import messages
from django.shortcuts import redirect


def require_official(request):
    if not request.session.get("user_email"):
        messages.error(request, "You must log in first.")
        return False

    if request.session.get("user_role") != "Official":
        messages.error(request, "Access denied: Officials only.")
        return False

    return True