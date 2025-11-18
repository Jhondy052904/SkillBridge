from skillbridge.supabase_client import supabase
from typing import List, Dict, Any
from django.contrib.auth.models import User
from datetime import datetime

# ============ JOBS CRUD ============

def create_job(title: str, description: str, posted_by_id: str, status: str = "Open") -> Dict[str, Any]:
    """Create a new job"""
    try:
        response = supabase.table('jobs').insert({
            'Title': title,
            'Description': description,
            'PostedBy': posted_by_id,
            'Status': status,
            'dateposted': datetime.utcnow().isoformat() + 'Z',  # 🔥 FIXED
        }).execute()

        if response.data:
            print("DEBUG CREATE JOB:", response.data)  # debug confirm
            return response.data[0]

        raise Exception(f"Failed to create job: {response}")

    except Exception as e:
        raise Exception(f"Error creating job: {str(e)}")



def get_jobs():
    response = supabase.table("jobs").select("*").order("JobID", desc=True).execute()
    print("DEBUG GET JOBS:", response.data)  # TEMPORARY DEBUG
    # Fix missing dateposted for existing jobs
    for job in response.data:
        if not job.get('dateposted'):
            job['dateposted'] = datetime.utcnow().isoformat() + 'Z'  # Set to now as default
    return response.data


def get_job_by_id(job_id: str) -> Dict[str, Any]:
    """Retrieve a specific job by ID"""
    try:
        response = supabase.table('jobs').select('*').eq('JobID', job_id).single().execute()
        return response.data
    except Exception as e:
        raise Exception(f"Error retrieving job: {str(e)}")


def update_job(job_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update a job"""
    try:
        response = supabase.table('jobs').update(updates).eq('JobID', job_id).execute()
        if response.data:
            return response.data[0]
        raise Exception(f"Failed to update job: {response}")
    except Exception as e:
        raise Exception(f"Error updating job: {str(e)}")


def delete_job(job_id: str) -> None:
    """Delete a job"""
    try:
        response = supabase.table('jobs').delete().eq('JobID', job_id).execute()
        if not response.data:
            raise Exception(f"Failed to delete job: {response}")
    except Exception as e:
        raise Exception(f"Error deleting job: {str(e)}")
    

# ============ JOB APPLICATION CRUD ============

def create_job_application(resident_id: int, job_id: int) -> Dict[str, Any]:
    """Create a job application entry"""

    try:
        # Prevent duplicate applications
        check = supabase.table('JobApplication') \
            .select('*') \
            .eq('ResidentID', resident_id) \
            .eq('JobID', job_id) \
            .execute()

        if check.data:
            raise Exception("You already applied to this job.")

        response = supabase.table('JobApplication').insert({
            'ResidentID': resident_id,
            'JobID': job_id,
            'ApplicationStatus': "Pending"
        }).execute()

        if response.data:
            return response.data[0]

        raise Exception(f"Failed to apply: {response}")

    except Exception as e:
        raise Exception(str(e))

# FIXED FUNCTION
def get_resident_by_user_id(django_user_id: int):
    # Step 1: Get username from Django auth table
    username = User.objects.get(id=django_user_id).username

    # Step 2: Find matching registration_useraccount row
    useraccount = supabase.table("registration_useraccount") \
        .select("*") \
        .eq("username", username) \
        .execute()

    if not useraccount.data:
        return None

    useraccount_id = useraccount.data[0]["id"]

    # Step 3: Fetch resident row using correct FK
    resident = supabase.table("registration_resident") \
        .select("*") \
        .eq("user_id", useraccount_id) \
        .execute()

    if resident.data:
        return resident.data[0]

    return None
    
def get_applied_jobs_by_resident(resident_id: int) -> List[Dict[str, Any]]:
    """Get all jobs that a resident has applied to"""
    try:
        response = supabase.table("JobApplication") \
            .select("ApplicationID, DateApplied, ApplicationStatus, jobs:JobID(Title, Status)") \
            .eq("ResidentID", resident_id) \
            .execute()

        jobs = []
        for item in response.data:
            job = {
                "title": item["jobs"]["Title"] if item.get("jobs") else "Unknown",
                "status": item["ApplicationStatus"],
                "date_applied": item.get("DateApplied", "—")
            }
            jobs.append(job)

        return jobs

    except Exception as e:
        raise Exception(f"Error fetching applied jobs: {str(e)}")
