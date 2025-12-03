#!/usr/bin/env python
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillbridge.settings')
sys.path.append('.')
django.setup()

from registration.models import Resident, UserAccount
from django.contrib.auth.models import User
from supabase import create_client, Client

def check_duplicates():
    print("=== Checking for duplicate account records ===\n")
    
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Check Django models
    print("1. Django Resident model duplicates:")
    try:
        resident_emails = [r.email for r in Resident.objects.all() if r.email]
        email_counts = {}
        for email in resident_emails:
            email_counts[email] = email_counts.get(email, 0) + 1
        
        duplicates = {email: count for email, count in email_counts.items() if count > 1}
        if duplicates:
            print(f"   Found {len(duplicates)} duplicate emails:")
            for email, count in duplicates.items():
                residents = Resident.objects.filter(email=email)
                print(f"   - Email: {email} (appears {count} times)")
                for resident in residents:
                    print(f"     * ID: {resident.id}, Name: {resident.first_name} {resident.last_name}")
        else:
            print("   No duplicate emails found in Resident model")
    except Exception as e:
        print(f"   Error checking Resident duplicates: {e}")
    
    print("\n2. Django User model duplicates:")
    try:
        user_emails = [u.email for u in User.objects.all() if u.email]
        email_counts = {}
        for email in user_emails:
            email_counts[email] = email_counts.get(email, 0) + 1
        
        duplicates = {email: count for email, count in email_counts.items() if count > 1}
        if duplicates:
            print(f"   Found {len(duplicates)} duplicate emails:")
            for email, count in duplicates.items():
                users = User.objects.filter(email=email)
                print(f"   - Email: {email} (appears {count} times)")
                for user in users:
                    print(f"     * ID: {user.id}, Username: {user.username}")
        else:
            print("   No duplicate emails found in User model")
    except Exception as e:
        print(f"   Error checking User duplicates: {e}")
    
    print("\n3. Django UserAccount model duplicates:")
    try:
        usernames = [ua.username for ua in UserAccount.objects.all() if ua.username]
        username_counts = {}
        for username in usernames:
            username_counts[username] = username_counts.get(username, 0) + 1
        
        duplicates = {username: count for username, count in username_counts.items() if count > 1}
        if duplicates:
            print(f"   Found {len(duplicates)} duplicate usernames:")
            for username, count in duplicates.items():
                accounts = UserAccount.objects.filter(username=username)
                print(f"   - Username: {username} (appears {count} times)")
                for account in accounts:
                    print(f"     * ID: {account.id}, Role: {account.role}")
        else:
            print("   No duplicate usernames found in UserAccount model")
    except Exception as e:
        print(f"   Error checking UserAccount duplicates: {e}")
    
    # Check Supabase resident table
    print("\n4. Supabase resident table duplicates:")
    try:
        response = supabase.table("resident").select("email, id, first_name, last_name").execute()
        residents = response.data or []
        
        email_counts = {}
        for resident in residents:
            email = resident.get('email')
            if email:
                email_counts[email] = email_counts.get(email, 0) + 1
        
        duplicates = {email: count for email, count in email_counts.items() if count > 1}
        if duplicates:
            print(f"   Found {len(duplicates)} duplicate emails in Supabase:")
            for email, count in duplicates.items():
                supabase_residents = [r for r in residents if r.get('email') == email]
                print(f"   - Email: {email} (appears {count} times)")
                for resident in supabase_residents:
                    print(f"     * ID: {resident.get('id')}, Name: {resident.get('first_name', '')} {resident.get('last_name', '')}")
        else:
            print("   No duplicate emails found in Supabase resident table")
    except Exception as e:
        print(f"   Error checking Supabase duplicates: {e}")
    
    # Cross-reference check
    print("\n5. Cross-reference analysis:")
    try:
        django_emails = set(u.email for u in User.objects.all() if u.email)
        supabase_emails = set(r.get('email') for r in supabase.table("resident").select("email").execute().data or [] if r.get('email'))
        
        common_emails = django_emails & supabase_emails
        django_only = django_emails - supabase_emails
        supabase_only = supabase_emails - django_emails
        
        print(f"   Emails in both Django and Supabase: {len(common_emails)}")
        print(f"   Emails only in Django: {len(django_only)}")
        print(f"   Emails only in Supabase: {len(supabase_only)}")
        
        if django_only:
            print(f"   Django-only emails: {list(django_only)[:5]}{'...' if len(django_only) > 5 else ''}")
        if supabase_only:
            print(f"   Supabase-only emails: {list(supabase_only)[:5]}{'...' if len(supabase_only) > 5 else ''}")
            
    except Exception as e:
        print(f"   Error in cross-reference analysis: {e}")
    
    print("\n=== Analysis complete ===")

if __name__ == "__main__":
    check_duplicates()