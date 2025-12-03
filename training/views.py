import os
from datetime import datetime, date

from django.shortcuts import render, redirect
from django.contrib import messages
from dotenv import load_dotenv
from supabase import create_client
from utils.send_email import send_training_notification_email

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


# ================== Helper: parse date strings from Supabase ==================
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
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to register.")
        return redirect("login")

    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect("list_trainings")


    # Load training from Supabase
    try:
        training_resp = supabase.table("training").select("*").eq("id", training_id).single().execute()
        training = training_resp.data
    except Exception as e:
        messages.error(request, f"Error loading training: {e}")
        return redirect("list_trainings")


    if not training:
        messages.error(request, "Training not found.")
        return redirect("list_trainings")

    # Get logged-in resident from Django DB
    try:
        resident = Resident.objects.get(email=request.user.email)
    except Resident.DoesNotExist:
        messages.error(request, "Resident profile not found.")
        return redirect("list_trainings")

    # Build user_id and name to store in Supabase
    user_id_value = int(resident.id)  # matches training_attendees.user_id (int8)
    full_name = f"{resident.first_name} {resident.last_name}".strip()

    # Prevent duplicate registration
    try:
        existing = (
            supabase.table("training_attendees")
            .select("id")
            .eq("training_id", training_id)
            .eq("user_id", user_id_value)
            .execute()
        )
        if existing.data:
            messages.info(request, "You are already registered for this training.")
            return redirect("list_trainings")
    except Exception as e:
        messages.error(request, f"Error checking existing registration: {e}")
        return redirect("list_trainings")

    # Insert into training_attendees
    try:
        supabase.table("training_attendees").insert({
            "training_id": training_id,
            "user_id": user_id_value,
            "full_name": full_name,
            "email": resident.email,
        }).execute()
    except Exception as e:
        messages.error(request, f"Failed to register for training: {e}")
        return redirect("list_trainings")

    messages.success(request, "Successfully registered for this training!")
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
    if not request.session.get("user_email"):
        messages.error(request, "You must log in first.")
        return redirect("login")

    try:
        response = supabase.table("training").select("*").order("created_at", desc=True).execute()
        trainings_raw = response.data or []
        
        # Calculate available slots for each training
        for training in trainings_raw:
            # Normalize date_scheduled into a datetime/date for template formatting
            try:
                training['date_scheduled'] = _parse_iso_date(training.get('date_scheduled'))
            except Exception:
                training['date_scheduled'] = None

            try:
                # Get count of registered attendees
                attendees_resp = supabase.table("training_attendees").select("id", count="exact").eq("training_id", training['id']).execute()
                registered_count = attendees_resp.count or 0
                total_slots = training.get('slots', 0) or 0
                available_slots = max(0, total_slots - registered_count)
                training['available_slots'] = available_slots
                training['registered_count'] = registered_count
            except Exception as e:
                print(f"Error calculating slots for training {training.get('id')}: {e}")
                training['available_slots'] = training.get('slots', 0) or 0
                training['registered_count'] = 0
        
        trainings = trainings_raw
    except Exception as e:
        trainings = []
        messages.error(request, f"Unable to load training list: {e}")

    return render(request, "training/list_trainings.html", {
        "trainings": trainings,
        "user_role": request.session.get("user_role", "Resident"),
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
    if not request.session.get("user_email"):
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

    # normalize date_scheduled to datetime/date object for templates
    training['date_scheduled'] = _parse_iso_date(training.get('date_scheduled'))

    # Optional: also load attendees if you want to show them on the detail page
    try:
        attendees_resp = supabase.table("training_attendees").select("*").eq("training_id", training_id).execute()
        attendees = attendees_resp.data or []
    except Exception:
        attendees = []

    return render(request, "training/training_detail.html", {
        "training": training,
        "attendees": attendees,
        "user_role": request.session.get("user_role", "Resident"),
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
