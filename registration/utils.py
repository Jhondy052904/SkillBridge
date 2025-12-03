"""
Utility functions for handling duplicate account prevention and common operations
"""
import logging
from typing import Optional, Tuple
from django.contrib.auth.models import User
from registration.models import Resident
from supabase import Client
import os

logger = logging.getLogger(__name__)

def require_official(request):
    """
    Check if the current user is an official.
    Returns True if user is logged in and has 'Official' role, False otherwise.
    """
    user_email = request.session.get('user_email')
    user_role = request.session.get('user_role')
    
    return bool(user_email and user_role == 'Official')

def normalize_email(email: str) -> str:
    """Normalize email to lowercase and strip whitespace"""
    return email.strip().lower() if email else ""

def check_email_exists(email: str, supabase: Client) -> Tuple[bool, str]:
    """
    Check if email already exists in Django or Supabase
    Returns: (exists, source) where source is 'django', 'supabase', or 'both'
    """
    email = normalize_email(email)
    if not email:
        return False, ""
    
    # Check Django User model
    django_exists = User.objects.filter(email=email).exists()
    
    # Check Supabase resident table
    try:
        response = supabase.table("resident").select("id").eq("email", email).execute()
        supabase_exists = bool(response.data)
    except Exception as e:
        logger.error(f"Error checking Supabase for email {email}: {e}")
        supabase_exists = False
    
    if django_exists and supabase_exists:
        return True, "both"
    elif django_exists:
        return True, "django"
    elif supabase_exists:
        return True, "supabase"
    
    return False, ""

def clean_existing_duplicates(email: str, supabase: Client):
    """
    Clean existing duplicates for an email
    Keeps the most recent record and removes others
    """
    email = normalize_email(email)
    if not email:
        return
    
    logger.info(f"Cleaning duplicates for email: {email}")
    
    # Clean Django User duplicates
    try:
        users = User.objects.filter(email=email).order_by('-id')  # Keep most recent
        if users.count() > 1:
            users_to_delete = users[1:]  # Keep first (most recent), delete rest
            for user in users_to_delete:
                logger.info(f"Deleting duplicate Django user: {user.username} (ID: {user.id})")
                user.delete()
    except Exception as e:
        logger.error(f"Error cleaning Django duplicates for {email}: {e}")
    
    # Clean Supabase resident duplicates
    try:
        response = supabase.table("resident").select("id, created_at").eq("email", email).execute()
        residents = response.data or []
        
        if len(residents) > 1:
            # Sort by created_at or id to keep most recent
            residents_sorted = sorted(residents, key=lambda x: x.get('created_at', '') or str(x.get('id', '')), reverse=True)
            residents_to_delete = residents_sorted[1:]  # Keep first, delete rest
            
            for resident in residents_to_delete:
                logger.info(f"Deleting duplicate Supabase resident: ID {resident.get('id')}")
                supabase.table("resident").delete().eq("id", resident.get('id')).execute()
    except Exception as e:
        logger.error(f"Error cleaning Supabase duplicates for {email}: {e}")

def prevent_duplicate_signup(email: str, supabase: Client) -> Tuple[bool, Optional[str]]:
    """
    Check if signup should be prevented due to existing records
    Returns: (should_prevent, error_message)
    """
    email = normalize_email(email)
    if not email:
        return True, "Email is required"
    
    exists, source = check_email_exists(email, supabase)
    
    if exists:
        if source == "both":
            return True, "An account with this email already exists in both systems. Please try logging in instead."
        elif source == "django":
            return True, "An account with this email already exists. Please try logging in instead."
        elif source == "supabase":
            return True, "An account with this email is already registered. Please try logging in instead."
    
    return False, None

def handle_signup_with_deduplication(email: str, supabase: Client) -> Tuple[bool, Optional[str]]:
    """
    Handle signup process with proper deduplication
    Returns: (success, error_message)
    """
    # First check if we should prevent signup
    should_prevent, error_msg = prevent_duplicate_signup(email, supabase)
    if should_prevent:
        return False, error_msg
    
    # Clean any existing duplicates first
    clean_existing_duplicates(email, supabase)
    
    # Check again after cleanup
    exists, source = check_email_exists(email, supabase)
    if exists:
        return False, f"Unable to create account due to existing records in {source}"
    
    return True, None