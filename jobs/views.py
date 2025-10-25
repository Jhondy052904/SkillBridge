from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .services.supabase_crud import (
    create_job, get_jobs, update_job, delete_job, get_job_by_id
)

@login_required
def post_job(request):
    """Allow users to post jobs"""
    if request.method == 'POST':
        try:
            data = request.POST
            job = create_job(
                title=data['title'],
                description=data['description'],
                posted_by=str(request.user.id),
                status=data.get('status', 'Open')
            )
            messages.success(request, "Job posted successfully!")
            return redirect('list_jobs')
        except Exception as e:
            messages.error(request, f"Error posting job: {str(e)}")
    return render(request, 'jobs/post_job.html')

@login_required
def admin_post_job(request):
    """Allow admins to post jobs"""
    if not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect('home')
    
    if request.method == 'POST':
        try:
            data = request.POST
            job = create_job(
                title=data['title'],
                description=data['description'],
                posted_by=str(request.user.id),
                status=data.get('status', 'Open')
            )
            messages.success(request, "Job posted successfully!")
            return redirect('list_jobs')
        except Exception as e:
            messages.error(request, f"Error posting job: {str(e)}")
    return render(request, 'jobs/post_job.html')

@login_required
def list_jobs(request):
    """Display all jobs"""
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
            updates = {
                'Title': request.POST.get('title'),
                'Description': request.POST.get('description'),
                'Status': request.POST.get('status'),
            }
            updates = {k: v for k, v in updates.items() if v is not None}
            
            updated_job = update_job(job_id, updates)
            messages.success(request, "Job updated!")
            return redirect('list_jobs')
        except Exception as e:
            messages.error(request, f"Error updating job: {str(e)}")
    
    try:
        job = get_job_by_id(job_id)
    except Exception as e:
        messages.error(request, f"Error loading job: {str(e)}")
        job = None
    
    return render(request, 'jobs/update_job.html', {'job': job})

@login_required
def delete_job_view(request, job_id):
    """Delete a job"""
    try:
        delete_job(job_id)
        messages.success(request, "Job deleted!")
    except Exception as e:
        messages.error(request, f"Error deleting job: {str(e)}")
    return redirect('list_jobs')