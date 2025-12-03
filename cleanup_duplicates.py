#!/usr/bin/env python
"""
Script to clean up duplicate account records in both Django and Supabase
This should be run before applying the new uniqueness constraints
"""
import os
import sys
import django
from datetime import datetime

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillbridge.settings')
sys.path.append('.')
django.setup()

from django.contrib.auth.models import User
from registration.models import Resident, UserAccount
from supabase import create_client, Client
from registration.utils import clean_existing_duplicates

def cleanup_duplicates():
    print("=== Cleaning up duplicate account records ===\n")
    
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Log cleanup start
    with open('duplicate_cleanup_log.txt', 'w') as log_file:
        log_file.write(f"Duplicate cleanup started at: {datetime.now()}\n\n")
    
    def log_message(message):
        try:
            print(message)
            with open('duplicate_cleanup_log.txt', 'a', encoding='utf-8') as log_file:
                log_file.write(f"{datetime.now()}: {message}\n")
        except UnicodeEncodeError:
            safe_message = message.encode('ascii', 'replace').decode('ascii')
            print(safe_message)
            with open('duplicate_cleanup_log.txt', 'a', encoding='utf-8') as log_file:
                log_file.write(f"{datetime.now()}: {safe_message}\n")
    
    log_message("1. Cleaning Django User duplicates:")
    try:
        # Find all duplicate emails in User model
        emails = User.objects.exclude(email='').values_list('email', flat=True)
        email_counts = {}
        for email in emails:
            if email:
                count = User.objects.filter(email=email).count()
                if count > 1:
                    email_counts[email] = count
        
        if email_counts:
            log_message(f"   Found {len(email_counts)} emails with duplicates:")
            for email, count in email_counts.items():
                log_message(f"   - {email}: {count} records")
                
                # Keep the most recent user (highest ID) and delete others
                users_to_delete = User.objects.filter(email=email).order_by('id')[1:]  # Keep first, delete rest
                
                for user in users_to_delete:
                    log_message(f"     * Deleting user: {user.username} (ID: {user.id})")
                    user.delete()
        else:
            log_message("   No duplicate emails found in User model")
    except Exception as e:
        log_message(f"   Error cleaning User duplicates: {e}")
    
    log_message("\n2. Cleaning Django Resident duplicates:")
    try:
        # Find all duplicate emails in Resident model
        emails = Resident.objects.exclude(email='').values_list('email', flat=True)
        email_counts = {}
        for email in emails:
            if email:
                count = Resident.objects.filter(email=email).count()
                if count > 1:
                    email_counts[email] = count
        
        if email_counts:
            log_message(f"   Found {len(email_counts)} emails with duplicates:")
            for email, count in email_counts.items():
                log_message(f"   - {email}: {count} records")
                
                # Keep the most recent resident (highest ID) and delete others
                residents_to_delete = Resident.objects.filter(email=email).order_by('id')[1:]  # Keep first, delete rest
                
                for resident in residents_to_delete:
                    log_message(f"     * Deleting resident: {resident.first_name} {resident.last_name} (ID: {resident.id})")
                    resident.delete()
        else:
            log_message("   No duplicate emails found in Resident model")
    except Exception as e:
        log_message(f"   Error cleaning Resident duplicates: {e}")
    
    log_message("\n3. Cleaning Supabase resident duplicates:")
    try:
        response = supabase.table("resident").select("email, id, first_name, last_name").execute()
        residents = response.data or []
        
        # Group residents by email
        email_groups = {}
        for resident in residents:
            email = resident.get('email')
            if email:
                if email not in email_groups:
                    email_groups[email] = []
                email_groups[email].append(resident)
        
        # Find duplicates
        duplicate_emails = {email: residents for email, residents in email_groups.items() if len(residents) > 1}
        
        if duplicate_emails:
            log_message(f"   Found {len(duplicate_emails)} emails with duplicates:")
            for email, residents_list in duplicate_emails.items():
                log_message(f"   - {email}: {len(residents_list)} records")
                
                # Sort by ID (most recent first) - created_at column doesn't exist
                residents_sorted = sorted(residents_list, key=lambda x: x.get('id', 0), reverse=True)
                residents_to_delete = residents_sorted[1:]  # Keep first, delete rest
                
                for resident in residents_to_delete:
                    log_message(f"     * Deleting resident: {resident.get('first_name', '')} {resident.get('last_name', '')} (ID: {resident.get('id')})")
                    try:
                        supabase.table("resident").delete().eq("id", resident.get('id')).execute()
                    except Exception as e:
                        log_message(f"       Error deleting resident ID {resident.get('id')}: {e}")
        else:
            log_message("   No duplicate emails found in Supabase resident table")
    except Exception as e:
        log_message(f"   Error cleaning Supabase duplicates: {e}")
    
    log_message("\n4. Cross-validation check:")
    try:
        # Final check for remaining duplicates
        django_emails = set(u.email for u in User.objects.exclude(email='').all() if u.email)
        supabase_emails = set(r.get('email') for r in supabase.table("resident").select("email").execute().data or [] if r.get('email'))
        resident_emails = set(r.email for r in Resident.objects.exclude(email='').all() if r.email)
        
        log_message(f"   Django User emails: {len(django_emails)}")
        log_message(f"   Django Resident emails: {len(resident_emails)}")
        log_message(f"   Supabase resident emails: {len(supabase_emails)}")
        
        # Check for any remaining duplicates
        django_dup_check = any(User.objects.filter(email=email).count() > 1 for email in django_emails)
        supabase_response = supabase.table("resident").select("email").execute()
        if supabase_response.data:
            supabase_dup_check = any(sum(1 for r in supabase_response.data if r.get('email') == email) > 1 for email in supabase_emails)
        else:
            supabase_dup_check = False
        
        if not django_dup_check and not supabase_dup_check:
            log_message("   ✅ All duplicates successfully cleaned!")
        else:
            log_message("   ⚠️ Some duplicates may still remain")
            
    except Exception as e:
        log_message(f"   Error in validation check: {e}")
    
    log_message(f"\n=== Cleanup completed at {datetime.now()} ===")
    log_message("Check duplicate_cleanup_log.txt for detailed logs")

def create_sql_constraints():
    """Create SQL commands to add unique constraints to Supabase"""
    print("\n=== Creating SQL constraints for Supabase ===\n")
    
    # Create SQL file for Supabase unique constraints
    with open('supabase_unique_constraints.sql', 'w') as f:
        f.write("-- Add unique constraints to prevent future duplicates\n")
        f.write("-- Execute these commands in your Supabase SQL editor\n\n")
        
        f.write("-- Add unique constraint on resident table email column\n")
        f.write("ALTER TABLE resident ADD CONSTRAINT unique_resident_email UNIQUE (email);\n\n")
        
        f.write("-- Add unique constraint on registration_official table email column (if exists)\n")
        f.write("-- ALTER TABLE registration_official ADD CONSTRAINT unique_official_email UNIQUE (email);\n\n")
        
        f.write("-- Create unique index on email for better performance\n")
        f.write("CREATE UNIQUE INDEX IF NOT EXISTS idx_resident_email_unique ON resident(email);\n\n")
    
    print("Created supabase_unique_constraints.sql")
    print("Please execute the SQL commands in your Supabase dashboard to add unique constraints")

if __name__ == "__main__":
    cleanup_duplicates()
    create_sql_constraints()