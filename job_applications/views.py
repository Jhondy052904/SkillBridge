from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .services.supabase_crud import (
    create_job_application, get_job_applications, update_application, 
    delete_application, get_application_by_id, get_applications_by_resident,
    get_applications_by_job
)


def apply_for_job(request, job_id):
    """Allow residents to apply for a job"""
    if request.method == 'POST':
        try:
            application = create_job_application(
                resident_id=str(request.user.id),
                job_id=job_id,
                application_status='Pending'
            )
            messages.success(request, "Application submitted successfully!")
            return redirect('my_applications')
        except Exception as e:
            messages.error(request, f"Error submitting application: {str(e)}")
    
    return render(request, 'job_applications/apply_for_job.html', {'job_id': job_id})


def my_applications(request):
    """View resident's own job applications"""
    try:
        applications = get_applications_by_resident(str(request.user.id))
    except Exception as e:
        messages.error(request, f"Error loading applications: {str(e)}")
        applications = []
    return render(request, 'job_applications/my_applications.html', {'applications': applications})


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


def job_applications(request, job_id):
    """Admin view - see all applications for a specific job"""
    if not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect('home')
    
    try:
        applications = get_applications_by_job(job_id)
    except Exception as e:
        messages.error(request, f"Error loading applications: {str(e)}")
        applications = []
    return render(request, 'job_applications/job_applications.html', {
        'applications': applications,
        'job_id': job_id
    })


def update_application_status(request, application_id):
    """Update application status (admin only)"""
    if not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect('home')
    
    if request.method == 'POST':
        try:
            new_status = request.POST.get('application_status')
            updated = update_application(
                application_id=application_id,
                updates={'ApplicationStatus': new_status}
            )
            messages.success(request, f"Application status updated to {new_status}!")
            return redirect('list_all_applications')
        except Exception as e:
            messages.error(request, f"Error updating application: {str(e)}")
    
    try:
        application = get_application_by_id(application_id)
    except Exception as e:
        messages.error(request, f"Error loading application: {str(e)}")
        application = None
    
    return render(request, 'job_applications/update_application.html', {'application': application})


def delete_application_view(request, application_id):
    """Delete a job application (admin or applicant only)"""
    try:
        application = get_application_by_id(application_id)
        is_applicant = str(request.user.id) == application['ResidentID']
        
        if not (request.user.is_staff or is_applicant):
            messages.error(request, "Access denied.")
            return redirect('home')
        
        delete_application(application_id)
        messages.success(request, "Application deleted!")
    except Exception as e:
        messages.error(request, f"Error deleting application: {str(e)}")
    
    return redirect('my_applications' if not request.user.is_staff else 'list_all_applications')

