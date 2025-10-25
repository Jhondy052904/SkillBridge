from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .services.supabase_crud import (
    create_job_application, get_job_applications, update_application, 
    delete_application, get_application_by_id, get_applications_by_resident,
    get_applications_by_job, check_existing_application
)
from jobs.services.supabase_crud import get_job_by_id

@login_required
def apply_for_job(request, job_id):
    """Job application form"""
    try:
        # Check if already applied
        already_applied = check_existing_application(int(request.user.id), int(job_id))
        if already_applied:
            messages.warning(request, "You've already applied for this job.")
            return redirect('job_detail', job_id=job_id)
        
        # Get job details
        job = get_job_by_id(job_id)
        if not job:
            messages.error(request, "Job not found.")
            return redirect('job_listings')
        
    except Exception as e:
        messages.error(request, f"Error loading job: {str(e)}")
        return redirect('job_listings')
    
    if request.method == 'POST':
        try:
            # Check again for duplicate submission
            if check_existing_application(int(request.user.id), int(job_id)):
                messages.warning(request, "You've already applied for this job.")
                return redirect('job_detail', job_id=job_id)
            
            # Create application
            application = create_job_application(
                resident_id=int(request.user.id),
                job_id=int(job_id),
                application_status='Pending'
            )
            
            messages.success(request, "Application submitted successfully!")
            return redirect('my_applications')
        except Exception as e:
            messages.error(request, f"Error submitting application: {str(e)}")
    
    return render(request, 'job_applications/apply_for_job.html', {'job': job})


@login_required
def my_applications(request):
    """View resident's own job applications"""
    try:
        applications = get_applications_by_resident(int(request.user.id))
        
        # Enrich with job details
        for app in applications:
            try:
                job = get_job_by_id(app['JobID'])
                app['job'] = job
            except:
                app['job'] = None
    except Exception as e:
        messages.error(request, f"Error loading applications: {str(e)}")
        applications = []
    
    return render(request, 'job_applications/my_applications.html', {'applications': applications})


@login_required
def list_all_applications(request):
    """Admin view - list all job applications"""
    if not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect('home')
    
    try:
        applications = get_job_applications()
    except Exception as e:
        messages.error(request, f"Error loading applications: {str(e)}")
        applications = []
    return render(request, 'job_applications/list_applications.html', {'applications': applications})