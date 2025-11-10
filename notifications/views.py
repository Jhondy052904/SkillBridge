from django.http import JsonResponse
from django.views.decorators.http import require_GET
from skillbridge.supabase_client import supabase

@require_GET
def latest_notification(request):
    """
    Returns the latest visible notification or {"has": False}
    """
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
