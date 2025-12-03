import os
from datetime import datetime, date

from django.shortcuts import render, redirect
from django.contrib import messages
from dotenv import load_dotenv
from supabase import create_client
from utils.send_email import send_training_notification_email

from django.http import JsonResponse
from registration.utils import require_official
from registration.models import Resident

# ================== LOAD .ENV AND INIT SUPABASE ==================
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase environment variables missing in .env")

# Single Supabase client used everywhere
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ================== Helpers ==================
def _is_ajax_request(request):
    """
    Detect AJAX/fetch requests by common headers or JSON content type.
    """
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return True
    accept = request.headers.get("Accept", "")
    if "application/json" in accept or request.content_type == "application/json":
        return True
    return False


def _parse_iso_date(value):
    """
    Try to convert common Supabase/JSON date strings into a datetime/date.
    Returns None on failure.
    """
    if not value:
        return None

    # Already a date/datetime
    if isinstance(value, (date, datetime)):
        return value

    if isinstance(value, str):
        s = value.strip()
        # remove trailing 'Z' if present (UTC designator)
        if s.endswith("Z"):
            s = s[:-1]

        # Try ISO parsing (works for YYYY-MM-DD and YYYY-MM-DDTHH:MM:SS[.ffffff])
        try:
            dt = datetime.fromisoformat(s)
            return dt
        except Exception:
            pass

        # Try explicit common formats
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.strptime(s, fmt)
                return dt
            except Exception:
                continue

    return None


# ================== REGISTER FOR TRAINING ==================
def register_training(request, training_id):
    """Resident registers for a training. Uses Resident.id as user_id in training_attendees."""
    # Authentication check
    if not request.user.is_authenticated:
        if _is_ajax_request(request):
            return JsonResponse({"ok": False, "message": "You must be logged in to register."}, status=401)
        messages.error(request, "You must be logged in to register.")
        return redirect("login")

    # Only accept POST
    if request.method != "POST":
        if _is_ajax_request(request):
            return JsonResponse({"ok": False, "message": "Invalid request method."}, status=405)
        messages.error(request, "Invalid request method.")
        return redirect("list_trainings")

    # Load training from Supabase
    try:
        training_resp = supabase.table("training").select("*").eq("id", training_id).single().execute()
        training = training_resp.data
    except Exception as e:
        msg = f"Error loading training: {e}"
        if _is_ajax_request(request):
            return JsonResponse({"ok": False, "message": msg}, status=500)
        messages.error(request, msg)
        return redirect("list_trainings")

    if not training:
        if _is_ajax_request(request):
            return JsonResponse({"ok": False, "message": "Training not found."}, status=404)
        messages.error(request, "Training not found.")
        return redirect("list_trainings")

    # Get logged-in resident from Django DB (used for user_id / full_name)
    try:
        resident = Resident.objects.get(email=request.user.email)
    except Resident.DoesNotExist:
        if _is_ajax_request(request):
            return JsonResponse({"ok": False, "message": "Resident profile not found."}, status=404)
        messages.error(request, "Resident profile not found.")
        return redirect("list_trainings")

    # Build user_id and name to store in Supabase
    try:
        user_id_value = int(resident.id)
    except Exception:
        # fallback - if resident.id isn't convertible
        user_id_value = resident.id

    full_name = f"{resident.first_name} {resident.last_name}".strip()

    # Reliable duplicate registration check using count="exact"
    try:
        existing_resp = (
            supabase.table("training_attendees")
            .select("id", count="exact")
            .eq("training_id", training_id)
            .eq("user_id", user_id_value)
            .execute()
        )
        existing_count = existing_resp.count or 0
    except Exception as e:
        msg = f"Error checking existing registration: {e}"
        if _is_ajax_request(request):
            return JsonResponse({"ok": False, "message": msg}, status=500)
        messages.error(request, msg)
        return redirect("list_trainings")

    if existing_count > 0:
        # Exact duplicate message from spec
        if _is_ajax_request(request):
            return JsonResponse({"ok": False, "message": "You've already registered for this event."}, status=400)
        messages.info(request, "You've already registered for this event.")
        return redirect("list_trainings")

    # Insert into training_attendees
    try:
        insert_resp = supabase.table("training_attendees").insert({
            "training_id": training_id,
            "user_id": user_id_value,
            "full_name": full_name,
            "email": resident.email,
        }).execute()
        # insert_resp.data may contain inserted rows; you can inspect for debugging if needed
    except Exception as e:
        msg = f"Failed to register for training: {e}"
        if _is_ajax_request(request):
            return JsonResponse({"ok": False, "message": msg}, status=500)
        messages.error(request, msg)
        return redirect("list_trainings")

    # Success response
    if _is_ajax_request(request):
        return JsonResponse({"ok": True, "message": "You have successfully registered for this training event."})
    messages.success(request, "You have successfully registered for this training event.")
    return redirect("list_trainings")


# ================== AUDIT LOG FUNCTION ==================
def log_action(action, entity, entity_id, request):
    try:
        supabase.table("audit_logs").insert({
            "entity": entity,
            "entity_id": entity_id,
            "action": action,
            "performed_by": request.session.get("user_email"),
            "timestamp": datetime.now().isoformat()
        }).execute()
    except Exception as e:
        print("Audit log error:", e)


# ================== CREATE TRAINING ==================
def post_training(request):
    if not require_official(request):
        return redirect("login")

    official_id = request.session.get("official_id") or request.session.get("user_email")

    if request.method == "POST":
        data = request.POST
        try:
            result = supabase.table("training").insert({
                "training_name": data["training_name"],
                "description": data["description"],
                "date_scheduled": data["date_scheduled"],
                "slots": data.get("slots") or 20,
                "created_by": official_id,
            }).execute()

            new_id = result.data[0]["id"]

            supabase.table("notifications").insert({
                "type": "training_posted",
                "message": f"New training opportunity: {data['training_name'][:100]} (Scheduled: {data['date_scheduled']})",
                "link_url": f"/training/{new_id}/",
                "visible": True,
                "created_at": datetime.now().isoformat()
            }).execute()

            # Send email notifications to all verified residents
            try:
                # Get all verified residents
                residents_resp = supabase.table("resident").select("email, first_name").eq("verification_status", "Verified").execute()
                residents = residents_resp.data or []

                training_link = f"https://yourdomain.com/training/{new_id}/"  # Replace with actual domain

                for resident in residents:
                    email = resident.get("email")
                    first_name = resident.get("first_name", "")
                    if email:
                        send_training_notification_email(email, data['training_name'], data['description'], data['date_scheduled'], training_link)
                        print(f"Email sent to {email} for training {data['training_name']}")
            except Exception as e:
                print("Error sending training notification emails:", e)

            log_action("create", "training", new_id, request)

            messages.success(request, "Training created successfully!")
            return redirect("official_dashboard")

        except Exception as e:
            messages.error(request, f"Error: {e}")

    return render(request, "training/post_training.html")


# ================== READ TRAININGS ==================
def list_trainings(request):
    user_email = request.session.get("user_email")
    if not user_email:
        messages.error(request, "You must log in first.")
        return redirect("login")

    # Anyone logged-in is allowed to register, so set flag for template
    user_role = request.session.get("user_role", "Resident")
    is_verified_resident = (user_role != "Official")

    try:
        response = supabase.table("training").select("*").order("created_at", desc=True).execute()
        trainings_raw = response.data or []

        for training in trainings_raw:
            # Normalize scheduled date
            try:
                training["date_scheduled"] = _parse_iso_date(training.get("date_scheduled"))
            except Exception:
                training["date_scheduled"] = None

            # Normalize created_at for display
            try:
                training["created_at"] = _parse_iso_date(training.get("created_at"))
            except Exception:
                training["created_at"] = None

            # Calculate available slots
            try:
                attendees_resp = (
                    supabase.table("training_attendees")
                    .select("id", count="exact")
                    .eq("training_id", training["id"])
                    .execute()
                )
                registered_count = attendees_resp.count or 0
                total_slots = training.get("slots", 0) or 0
                available_slots = max(0, total_slots - registered_count)
                training["available_slots"] = available_slots
                training["registered_count"] = registered_count
            except Exception as e:
                print(f"Error calculating slots for training {training.get('id')}: {e}")
                training["available_slots"] = training.get("slots", 0) or 0
                training["registered_count"] = 0

        trainings = trainings_raw
    except Exception as e:
        trainings = []
        messages.error(request, f"Unable to load training list: {e}")

    return render(request, "training/list_trainings.html", {
        "trainings": trainings,
        "user_role": user_role,
        "is_verified_resident": is_verified_resident,
    })


# ================== UPDATE TRAINING ==================
def edit_training(request, training_id):
    if not require_official(request):
        return redirect("login")

    training = supabase.table("training").select("*").eq("id", training_id).single().execute().data
    if not training:
        messages.error(request, "Training not found.")
        return redirect("list_trainings")

    # normalize date for the edit form/template
    training['date_scheduled'] = _parse_iso_date(training.get('date_scheduled'))

    if request.method == "POST":
        updates = {
            "training_name": request.POST.get("training_name"),
            "description": request.POST.get("description"),
            "date_scheduled": request.POST.get("date_scheduled"),
            "slots": request.POST.get("slots"),
        }

        try:
            supabase.table("training").update(updates).eq("id", training_id).execute()
            log_action("edit", "training", training_id, request)
            messages.success(request, "Training updated successfully!")
            return redirect("official_dashboard")

        except Exception as e:
            messages.error(request, f"Error updating training: {e}")

    return render(request, "training/update_training.html", {"training": training})


# ================== DELETE TRAINING ==================
def delete_training(request, training_id):
    if request.method == "POST":
        try:
            response = supabase.table("training").delete().eq("id", training_id).execute()
            if response.data:
                messages.success(request, "Training deleted successfully.")
            else:
                messages.error(request, "Training not found or already deleted.")
        except Exception as e:
            messages.error(request, f"Error deleting training: {e}")
    else:
        messages.error(request, "Invalid request method.")

    return redirect("official_dashboard")


# ================== TRAINING DETAIL ==================
def training_detail(request, training_id):
    user_email = request.session.get("user_email")
    if not user_email:
        messages.error(request, "You must log in first.")
        return redirect("login")

    try:
        training_resp = supabase.table("training").select("*").eq("id", training_id).single().execute()
        training = training_resp.data
    except Exception as e:
        messages.error(request, f"Error loading training: {e}")
        return redirect("list_trainings")

    if not training:
        messages.error(request, "Training not found.")
        return redirect("list_trainings")

    # normalize dates
    training["date_scheduled"] = _parse_iso_date(training.get('date_scheduled'))
    training["created_at"] = _parse_iso_date(training.get('created_at'))

    # Load attendees
    try:
        attendees_resp = supabase.table("training_attendees").select("*").eq("training_id", training_id).execute()
        attendees = attendees_resp.data or []
    except Exception:
        attendees = []

    user_role = request.session.get("user_role", "Resident")
    # Anyone logged-in is allowed to register, so set flag for template
    is_verified_resident = (user_role != "Official")

    return render(request, "training/training_detail.html", {
        "training": training,
        "attendees": attendees,
        "user_role": user_role,
        "is_verified_resident": is_verified_resident,
    })


# ================== TRAINING ATTENDEES (OFFICIAL VIEW) ==================
def training_attendees(request, training_id):
    if not require_official(request):
        return redirect("login")

    try:
        training_resp = supabase.table("training").select("*").eq("id", training_id).single().execute()
        training = training_resp.data
    except Exception as e:
        messages.error(request, f"Error loading training: {e}")
        return redirect("official_dashboard")

    if not training:
        messages.error(request, "Training not found.")
        return redirect("official_dashboard")

    try:
        attendees_resp = supabase.table("training_attendees").select("*").eq("training_id", training_id).execute()
        attendees = attendees_resp.data or []
    except Exception as e:
        messages.error(request, f"Error loading attendees: {e}")
        return redirect("official_dashboard")

    return render(request, "training/training_attendees.html", {
        "training": training,
        "attendees": attendees,
    })


# ================== MARK AS ATTENDED ==================
def mark_attended(request, attendee_id):
    if not require_official(request):
        return redirect("login")

    try:
        supabase.table("training_attendees") \
            .update({"attendance_status": "Attended"}) \
            .eq("id", attendee_id) \
            .execute()
        messages.success(request, "Attendee marked as Attended.")
    except Exception as e:
        messages.error(request, f"Error marking attended: {e}")

    return redirect(request.META.get("HTTP_REFERER", "official_dashboard"))


# ================== MARK AS NOT ATTENDED ==================
def mark_not_attended(request, attendee_id):
    if not require_official(request):
        return redirect("login")

    try:
        supabase.table("training_attendees") \
            .update({"attendance_status": "Not Attended"}) \
            .eq("id", attendee_id) \
            .execute()
        messages.success(request, "Attendee marked as Not Attended.")
    except Exception as e:
        messages.error(request, f"Error marking not attended: {e}")

    return redirect(request.META.get("HTTP_REFERER", "official_dashboard"))
