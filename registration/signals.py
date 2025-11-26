# signals.py (fixed)
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from skillbridge.supabase_client import supabase
import datetime

@receiver(post_save, sender=User)
def create_user_profiles(sender, instance, created, **kwargs):
    if not created:
        return

    username = instance.username
    email = instance.email or ""

    # 1) Ensure registration_useraccount exists (reuse if present)
    existing = supabase.table("registration_useraccount") \
        .select("*") \
        .eq("username", username) \
        .execute()

    if existing.data:
        useraccount_id = existing.data[0]["id"]
    else:
        useraccount_response = supabase.table("registration_useraccount").insert({
            "username": username,
            "password_hash": "",  # optional
            "role": "resident"
        }).execute()
        useraccount_id = useraccount_response.data[0]["id"]

    # 2) Prefer checking by email first to avoid duplicate email inserts
    try:
        # check if resident exists using email
        resident_by_email = supabase.table("registration_resident") \
            .select("*") \
            .eq("email", email) \
            .single() \
            .execute()

        if resident_by_email.data:
            # resident row exists for this email -> ensure it's linked to useraccount_id
            resident = resident_by_email.data
            # If user_id is missing or different, update it
            if not resident.get("user_id") or str(resident.get("user_id")) != str(useraccount_id):
                supabase.table("registration_resident").update({
                    "user_id": useraccount_id
                }).eq("id", resident["id"]).execute()

        else:
            # If none found by email, fallback to checking by user_id (existing behavior)
            resident_check = supabase.table("registration_resident") \
                .select("*") \
                .eq("user_id", useraccount_id) \
                .execute()

            if not resident_check.data:
                # Safe to insert — no resident with this email or user_id
                supabase.table("registration_resident").insert({
                    "first_name": instance.first_name or "",
                    "last_name": instance.last_name or "",
                    "email": email,
                    "employment_status": "Unemployed",
                    "verification_status": "Pending",
                    "date_registered": datetime.datetime.now().isoformat(),
                    "address": "",
                    "contact_number": "",
                    "birthdate": None,
                    "user_id": useraccount_id
                }).execute()

    except Exception as e:
        # Log for debugging but don't crash the signal handler
        print("create_user_profiles signal error:", e)
