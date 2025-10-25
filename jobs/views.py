from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .services.supabase_crud import (
    create_job, get_jobs, update_job, delete_job, get_job_by_id,
    get_jobs_with_skills, link_skills_to_job, unlink_skills_from_job
)
from skills.services.supabase_crud import get_skills
from job_applications.services.supabase_crud import (
    create_job_application, get_applications_by_resident, check_existing_application
)
from .services.supabase_crud import get_job_skills

@login_required
def post_job(request):
    """Allow users to post jobs"""
    if request.method == 'POST':
        try:
            data = request.POST
            skill_ids = request.POST.getlist('skills')
            
            job = create_job(
                title=data['title'],
                description=data['description'],
                posted_by_id=str(request.user.id),
                status=data.get('status', 'Open')
            )
            
            # Link skills to job if provided
            if skill_ids:
                link_skills_to_job(job['JobID'], skill_ids)
            
            messages.success(request, "Job posted successfully!")
            return redirect('list_jobs')
        except Exception as e:
            messages.error(request, f"Error posting job: {str(e)}")
    
    try:
        skills = get_skills()
    except Exception as e:
        messages.error(request, f"Error loading skills: {str(e)}")
        skills = []
    
    return render(request, 'jobs/post_job.html', {'skills': skills})


@login_required
def admin_post_job(request):
    """Allow admins to post jobs"""
    if not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect('home')
    
    if request.method == 'POST':
        try:
            data = request.POST
            skill_ids = request.POST.getlist('skills')
            
            job = create_job(
                title=data['title'],
                description=data['description'],
                posted_by_id=str(request.user.id),
                status=data.get('status', 'Open')
            )
            
            if skill_ids:
                link_skills_to_job(job['JobID'], skill_ids)
            
            messages.success(request, "Job posted successfully!")
            return redirect('list_jobs')
        except Exception as e:
            messages.error(request, f"Error posting job: {str(e)}")
    
    try:
        skills = get_skills()
    except Exception as e:
        messages.error(request, f"Error loading skills: {str(e)}")
        skills = []
    
    return render(request, 'jobs/post_job.html', {'skills': skills})


def job_listings(request):
    """Public job listings page - visible to all users"""
    try:
        jobs = get_jobs_with_skills()
    except Exception as e:
        messages.error(request, f"Failed to load job listings: {str(e)}")
        jobs = []
    
    return render(request, 'jobs/job_listings.html', {
        'jobs': jobs,
        'user_is_authenticated': request.user.is_authenticated
    })


@login_required
def job_detail(request, job_id):
    """View job details with apply button"""
    try:
        job = get_job_by_id(job_id)
        if not job:
            messages.error(request, "Job not found.")
            return redirect('job_listings')
        
        # Get skills for this job
        skills = get_job_skills(job['JobID'])
        job['skills'] = skills
        
        # Check if user already applied
        user_applications = get_applications_by_resident(request.user.id)
        already_applied = any(app['JobID'] == int(job_id) for app in user_applications)
        
    except Exception as e:
        messages.error(request, f"Error loading job: {str(e)}")
        return redirect('job_listings')
    
    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'already_applied': already_applied
    })


@login_required
def list_jobs(request):
    """Display all jobs (admin/recruiter view)"""
    try:
        jobs = get_jobs()
    except Exception as e:
        messages.error(request, f"Error loading jobs: {str(e)}")
        jobs = []
    return render(request, 'jobs/list_jobs.html', {'jobs': jobs})


@login_required
def update_job_view(request, job_id):
    """Update a job"""
    if request.method == 'POST':
        try:
            data = request.POST
            skill_ids = request.POST.getlist('skills')
            
            updates = {
                'Title': data.get('title'),
                'Description': data.get('description'),
                'Status': data.get('status'),
            }
            updates = {k: v for k, v in updates.items() if v is not None}
            
            update_job(job_id, updates)
            
            # Update skills
            unlink_skills_from_job(int(job_id))
            if skill_ids:
                link_skills_to_job(int(job_id), skill_ids)
            
            messages.success(request, "Job updated!")
            return redirect('list_jobs')
        except Exception as e:
            messages.error(request, f"Error updating job: {str(e)}")
    
    try:
        job = get_job_by_id(job_id)
        skills = get_skills()
        job_skills = get_job_skills(int(job_id))
        selected_skill_ids = [s['SkillID'] for s in job_skills]
    except Exception as e:
        messages.error(request, f"Error loading job: {str(e)}")
        job = None
        skills = []
        selected_skill_ids = []
    
    return render(request, 'jobs/update_job.html', {
        'job': job,
        'skills': skills,
        'selected_skill_ids': selected_skill_ids
    })


@login_required
def delete_job_view(request, job_id):
    """Delete a job"""
    try:
        delete_job(job_id)
        messages.success(request, "Job deleted!")
    except Exception as e:
        messages.error(request, f"Error deleting job: {str(e)}")
    return redirect('list_jobs')