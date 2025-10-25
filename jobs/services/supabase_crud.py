from skillbridge.supabase_client import supabase
from typing import List, Dict, Any

# ============ JOBS CRUD ============

def create_job(title: str, description: str, posted_by_id: str, status: str = "Open") -> Dict[str, Any]:
    """Create a new job"""
    try:
        response = supabase.table('jobs').insert({
            'Title': title,
            'Description': description,
            'PostedBy': posted_by_id,
            'Status': status,
        }).execute()
        if response.data:
            return response.data[0]
        raise Exception(f"Failed to create job: {response}")
    except Exception as e:
        raise Exception(f"Error creating job: {str(e)}")


def get_jobs() -> List[Dict[str, Any]]:
    """Retrieve all jobs"""
    try:
        response = supabase.table('jobs').select('*').execute()
        return response.data
    except Exception as e:
        raise Exception(f"Error retrieving jobs: {str(e)}")


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
