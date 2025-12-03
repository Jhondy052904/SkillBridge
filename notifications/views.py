from django.http import JsonResponse
from django.views.decorators.http import require_GET
from skillbridge.supabase_client import supabase
from django.shortcuts import redirect

@require_GET
def latest_notification(request):
    """
    Returns the latest visible notification or {"has": False}
    Only returns notifications to authenticated users
    """
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({"has": False, "error": "Not authenticated"}, status=401)
    
    # Check if user session is valid
    user_email = request.session.get('user_email')
    user_role = request.session.get('user_role')
    
    if not user_email or not user_role:
        return JsonResponse({"has": False, "error": "Invalid session"}, status=401)
    
    try:
        # Fetch last visible notification (newest by created_at)
        res = supabase.table('notifications').select('*').eq('visible', True).order('created_at', desc=True).limit(1).execute()
        data = res.data or []
        if not data:
            return JsonResponse({"has": False})

        n = data[0]
        # Ensure message is trimmed server-side to 120 chars
        n['message'] = (n.get('message') or '')[:120]

        # Return JSON
        return JsonResponse({
            "has": True,
            "notification": {
                "id": n.get('id'),
                "type": n.get('type'),
                "message": n.get('message'),
                "link_url": n.get('link_url'),
                "created_at": n.get('created_at')
            }
        })
    except Exception as e:
        return JsonResponse({"has": False, "error": str(e)}, status=500)
    
 
def clear_notifications(request):
    if request.method == "POST":
        supabase.table("notifications").update({"visible": False}).eq("visible", True).execute()
    return redirect("home")  #
