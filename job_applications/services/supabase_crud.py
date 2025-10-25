from skillbridge.supabase_client import supabase
from typing import List, Dict, Any

# ============ JOB APPLICATIONS CRUD ============

def create_job_application(resident_id: int, job_id: int, application_status: str = "Pending") -> Dict[str, Any]:
    """Create a new job application"""
    try:
        response = supabase.table('JobApplication').insert({
            'ResidentID': int(resident_id),
            'JobID': int(job_id),
            'ApplicationStatus': application_status,
        }).execute()
        if response.data:
            return response.data[0]
        raise Exception(f"Failed to create application: {response}")
    except Exception as e:
        raise Exception(f"Error creating application: {str(e)}")


def get_job_applications() -> List[Dict[str, Any]]:
    """Retrieve all job applications"""
    try:
        response = supabase.table('JobApplication').select('*').execute()
        return response.data
    except Exception as e:
        raise Exception(f"Error retrieving applications: {str(e)}")


def get_application_by_id(application_id: str) -> Dict[str, Any]:
    """Retrieve a specific application by ID"""
    try:
        response = supabase.table('JobApplication').select('*').eq('ApplicationID', application_id).single().execute()
        return response.data
    except Exception as e:
        raise Exception(f"Error retrieving application: {str(e)}")


def get_applications_by_resident(resident_id: int) -> List[Dict[str, Any]]:
    """Retrieve all applications for a specific resident"""
    try:
        response = supabase.table('JobApplication').select('*').eq('ResidentID', int(resident_id)).execute()
        return response.data
    except Exception as e:
        raise Exception(f"Error retrieving resident applications: {str(e)}")


def get_applications_by_job(job_id: int) -> List[Dict[str, Any]]:
    """Retrieve all applications for a specific job"""
    try:
        response = supabase.table('JobApplication').select('*').eq('JobID', int(job_id)).execute()
        return response.data
    except Exception as e:
        raise Exception(f"Error retrieving job applications: {str(e)}")


def check_existing_application(resident_id: int, job_id: int) -> bool:
    """Check if resident already applied for this job"""
    try:
        response = supabase.table('JobApplication').select('*').eq('ResidentID', int(resident_id)).eq('JobID', int(job_id)).execute()
        return len(response.data) > 0
    except Exception as e:
        raise Exception(f"Error checking application: {str(e)}")


def update_application(application_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update a job application"""
    try:
        response = supabase.table('JobApplication').update(updates).eq('ApplicationID', application_id).execute()
        if response.data:
            return response.data[0]
        raise Exception(f"Failed to update application: {response}")
    except Exception as e:
        raise Exception(f"Error updating application: {str(e)}")


def delete_application(application_id: str) -> None:
    """Delete a job application"""
    try:
        response = supabase.table('JobApplication').delete().eq('ApplicationID', application_id).execute()
        if not response.data:
            raise Exception(f"Failed to delete application: {response}")
    except Exception as e:
        raise Exception(f"Error deleting application: {str(e)}")

