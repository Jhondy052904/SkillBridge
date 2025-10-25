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


# ============ JOB SKILLS RELATIONSHIP ============

def get_job_skills(job_id: int) -> List[Dict[str, Any]]:
    """Get all skills for a specific job"""
    try:
        response = supabase.table('job_skills').select('skills(*)').eq('jobid', int(job_id)).execute()
        return [record['skills'] for record in response.data] if response.data else []
    except Exception as e:
        raise Exception(f"Error retrieving job skills: {str(e)}")

def link_skills_to_job(job_id: int, skill_ids: List[str]) -> None:
    """Link skills to a job"""
    try:
        if not skill_ids:
            return
        # Use lowercase 'jobid' and 'skillid' to match the table schema
        job_skill_records = [{'jobid': int(job_id), 'skillid': skill_id} for skill_id in skill_ids]
        response = supabase.table('job_skills').insert(job_skill_records).execute()
        if not response.data:
            raise Exception(f"Failed to link skills: {response}")
    except Exception as e:
        raise Exception(f"Error linking skills: {str(e)}")


def unlink_skills_from_job(job_id: int) -> None:
    """Remove all skills from a job"""
    try:
        supabase.table('job_skills').delete().eq('jobid', int(job_id)).execute()
    except Exception as e:
        raise Exception(f"Error unlinking skills: {str(e)}")


# ============ JOB LISTINGS (PUBLIC VIEW) ============

def get_jobs_with_skills() -> List[Dict[str, Any]]:
    """Get all jobs with their associated skills for public listing"""
    try:
        jobs = get_jobs()
        jobs_with_skills = []
        
        for job in jobs:
            if job.get('Status') == 'Open':  # Only show open jobs
                try:
                    skills = get_job_skills(job['JobID'])
                    job['skills'] = skills
                    jobs_with_skills.append(job)
                except Exception as e:
                    # Log error but continue with other jobs
                    print(f"Warning: Could not load skills for job {job['JobID']}: {e}")
                    job['skills'] = []
                    jobs_with_skills.append(job)
        
        return jobs_with_skills
    except Exception as e:
        raise Exception(f"Error retrieving jobs with skills: {str(e)}")
