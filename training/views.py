from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import datetime
from skillbridge.supabase_client import supabase


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
from registration.utils import require_official  # <-- Your access control helper

def post_training(request):
    # Enforce access control
    if not require_official(request):
        return redirect("login")

    official_id = request.session.get("official_id") or request.session.get("user_email")

    if request.method == "POST":
        data = request.POST
        try:
            # ░░ INSERT TRAINING ░░
            result = supabase.table("training").insert({
                "training_name": data["training_name"],
                "description": data["description"],
                "date_scheduled": data["date_scheduled"],
                "slots": data.get("slots") or 20,
                "created_by": official_id  # REQUIRED
            }).execute()

            new_id = result.data[0]["id"]

            # ░░ INSERT NOTIFICATION ░░
            supabase.table("notifications").insert({
                "type": "Training Event",
                "message": f"New training posted: {data['training_name'][:100]}",
                "link_url": "/official/dashboard/",   # <-- Now correct
                "visible": True,
            }).execute()

            # ░░ LOG AUDIT ░░
            log_action("create", "training", new_id, request)

            messages.success(request, "Training created successfully!")
            return redirect("official_dashboard")  # <--- Correct redirect

        except Exception as e:
            messages.error(request, f"Error: {e}")

    return render(request, "training/post_training.html")



# ================== READ ==================
def list_trainings(request):

    if not request.session.get("user_email"):
        messages.error(request, "You must log in first.")
        return redirect("login")

    try:
        response = supabase.table("training").select("*").order("created_at", desc=True).execute()
        trainings = response.data
    except:
        trainings = []
        messages.error(request, "Unable to load training list")

    user_role = request.session.get("user_role", "Resident")
    return render(request, "training/list_trainings.html", {"trainings": trainings, "user_role": user_role})


# ================== UPDATE ==================
def edit_training(request, training_id):

    if not require_official(request):
        return redirect("login")

    training = supabase.table("training").select("*").eq("id", training_id).single().execute().data
    if not training:
        messages.error(request, "Training not found.")
        return redirect("list_trainings")

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


# ================== DELETE ==================
def delete_training(request, training_id):
    if request.method == "POST":
        response = supabase.table("training").delete().eq("id", training_id).execute()
        if response.data:
            messages.success(request, "Training deleted successfully.")
        else:
            messages.error(request, "Training not found or already deleted.")
    else:
        messages.error(request, "Invalid request method.")
    return redirect("official_dashboard")
