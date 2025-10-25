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
                posted_by_id=str(request.user.id),
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

# ✅ IMPORTS FOR APPLICATION MODULE
from .services.supabase_crud import create_job_application, get_resident_by_user_id
from skillbridge.supabase_client import supabase

@login_required
def apply_job(request, job_id):
    try:
        # get resident record tied to Django user (Django auth_user.id)
        resident = get_resident_by_user_id(request.user.id)

        # ✅ Auto-create resident if missing
        if not resident:

            # get matching entry in registration_useraccount
            useraccount = supabase.table("registration_useraccount") \
                .select("*") \
                .eq("username", request.user.username) \
                .execute()

            if useraccount.data:
                useraccount_id = useraccount.data[0]["id"]

                # create registration_resident
                supabase.table("registration_resident").insert({
                    "first_name": request.user.first_name or "",
                    "last_name": request.user.last_name or "",
                    "email": request.user.email or "",
                    "employment_status": "Unemployed",
                    "verification_status": "Pending",
                    "date_registered": datetime.datetime.now().isoformat(),
                    "address": "",
                    "contact_number": "",
                    "birthdate": None,
                    "user_id": useraccount_id
                }).execute()

                resident = get_resident_by_user_id(request.user.id)

                if not resident:
                    messages.error(request, "Could not create resident profile.")
                    return redirect('list_jobs')
            else:
                messages.error(request, "User account not found!")
                return redirect('list_jobs')

        # ✅ now submit the job application
        create_job_application(
            resident_id=resident['id'],
            job_id=job_id
        )

        messages.success(request, "Application submitted!")

    except Exception as e:
        messages.error(request, f"Error applying: {str(e)}")

    return redirect('list_jobs')
