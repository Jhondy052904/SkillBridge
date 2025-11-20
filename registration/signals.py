from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from skillbridge.supabase_client import supabase
import datetime

@receiver(post_save, sender=User)
def create_user_profiles(sender, instance, created, **kwargs):
    if created:

        # ✅ Check if username already exists in registration_useraccount
        existing = supabase.table("registration_useraccount") \
            .select("*") \
            .eq("username", instance.username) \
            .execute()

        if existing.data:
            # If exists, reuse existing ID
            useraccount_id = existing.data[0]["id"]

        else:
            # ✅ Create new registration_useraccount entry
            useraccount_response = supabase.table("registration_useraccount").insert({
                "username": instance.username,
                "password_hash": "",  # optional
                "role": "resident"
            }).execute()

            useraccount_id = useraccount_response.data[0]["id"]

        # ✅ Create linked registration_resident (only if not existing)
        resident_check = supabase.table("registration_resident") \
            .select("*") \
            .eq("user_id", useraccount_id) \
            .execute()

        if not resident_check.data:
            supabase.table("registration_resident").insert({
                "first_name": instance.first_name or "",
                "last_name": instance.last_name or "",
                "email": instance.email or "",
                "employment_status": "Unemployed",
                "verification_status": "Pending",
                "date_registered": datetime.datetime.now().isoformat(),
                "address": "",          # 👈 provide safe default
                "contact_number": "",   # 👈 provide safe default
                "birthdate": None,      # 👈 optional
                "user_id": useraccount_id
            }).execute()

