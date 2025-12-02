from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from datetime import datetime
from skillbridge.supabase_client import supabase
from .services.supabase_crud import (
    get_jobs,
    update_job,
    delete_job,
    get_job_by_id,
    create_job_application,
    get_applied_jobs_by_resident,
)

# ========== LOGGING FOR AUDIT TRAIL ==========
def log_action(action, entity, entity_id, request):
    try:
        supabase.table("audit_logs").insert({
            "entity": entity,
            "entity_id": entity_id,
            "action": action,
            "performed_by": request.session.get("user_email"),
            "timestamp": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        print("Audit log error:", e)


# ========== HOME (RESIDENT) ==========
@login_required
def home(request):
    try:
        resident = get_resident_by_user_id(request.user.id)
        applied_jobs = get_applied_jobs_by_resident(resident["id"]) if resident else []
        return render(request, "home.html", {"applied_jobs": applied_jobs})

    except Exception as e:
        messages.error(request, f"Error loading applied jobs: {str(e)}")
        return render(request, "home.html", {"applied_jobs": []})


def job_success(request):
    return render(request, 'jobs/job_success.html')


# ==========================================================
# POST JOB (OFFICIAL)
# ==========================================================
def post_job(request):
    if request.session.get('user_role') != 'Official':
        messages.error(request, "Access denied. Officials only.")
        return redirect('login')
    try:
        email = request.user.email.strip().lower()
        official = supabase.table("registration_official").select("*").ilike("email", email).execute()

        if not official.data:
            official = supabase.table("registration_official").select("*").eq("user_id", request.user.id).execute()

        if not official.data:
            messages.error(request, "Official profile not found.")
            return redirect("official_dashboard")

        official_data = official.data[0]

        if request.method == 'POST':
            data = request.POST
            title = data['title']
            description = data['description']
            status = data.get('status', 'Open')
            selected_skills = [skill for skill in data.get('skills_list', '').split(',') if skill]

            result = supabase.table("jobs").insert({
                "Title": title,
                "Description": description,
                "PostedBy": str(official_data["id"]),
                "Status": status,
                "dateposted": datetime.utcnow().isoformat()  # FINAL + CORRECT
            }).execute()

            print("DEBUG INSERT RESULT:", result.data)

            job = result.data[0]
            job_id = job.get("JobID")

            # Insert skill requirements
            import uuid
            for skill_id in selected_skills:
                supabase.table("job_skill_list").insert({
                    "id": str(uuid.uuid4()),
                    "job_id": job_id,
                    "skill_id": skill_id,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()

            log_action("create", "job", job_id, request)
            messages.success(request, "Job posted successfully!")
            return redirect("official_dashboard")

        # Fetch skills for the form
        try:
            skills_resp = supabase.table("skill_list").select("SkillID,SkillName").execute()
            skills = skills_resp.data if skills_resp.data else []
        except Exception as e:
            print("Error fetching skills:", e)
            skills = []

        return render(request, 'jobs/post_job.html', {'skills': skills})

    except Exception as e:
        print("EXCEPTION:", e)
        messages.error(request, f"Error posting job: {str(e)}")
        return redirect('official_dashboard')


# ==========================================================
# LIST JOBS
# ==========================================================
def list_jobs(request):
    if request.session.get('user_role') != 'Resident':
        return redirect('login')
    try:
        # ==========================
        # 1. Fetch All Jobs
        # ==========================
        jobs = get_jobs()

        # ==========================
        # 2. Fetch all job-skill relations
        # ==========================
        skills_resp = supabase.table("job_skill_list").select(
            "job_id, skill_list!inner(SkillID, SkillName)"
        ).execute()

        job_skills_by_id = {}       # skill IDs
        job_skills_by_name = {}     # skill names

        for item in skills_resp.data:
            job_id = item["job_id"]
            skill_id = item["skill_list"]["SkillID"]
            skill_name = item["skill_list"]["SkillName"]

            if job_id not in job_skills_by_id:
                job_skills_by_id[job_id] = []
                job_skills_by_name[job_id] = []

            job_skills_by_id[job_id].append(skill_id)
            job_skills_by_name[job_id].append(skill_name)

        # Attach skill names to job object for UI
        for job in jobs:
            job["skills"] = job_skills_by_name.get(job["JobID"], [])

        print("DEBUG JOB SKILLS:", job_skills_by_id)

        # ======================================================
        # 3. Get Resident Info from Supabase
        # ======================================================
        resident_email = request.user.email
        supabase_resident = supabase.table("resident").select("id").eq("email", resident_email).execute()
        recommended_jobs = []

        if supabase_resident.data:
            resident_id = supabase_resident.data[0]["id"]

            # ======================================================
            # 4. Fetch resident skills from Supabase
            # ======================================================
            resident_skill_resp = supabase.table("resident_skills").select("skill_id").eq("resident_id", resident_id).execute()
            resident_skill_ids = {item["skill_id"] for item in resident_skill_resp.data}

            # ======================================================
            # 5. Filter recommended jobs
            # ======================================================
            recommended_jobs = [
                job for job in jobs
                if any(skill_id in resident_skill_ids for skill_id in job_skills_by_id.get(job["JobID"], []))
            ]

    except Exception as e:
        print("ERROR:", str(e))
        messages.error(request, f"Error loading jobs: {str(e)}")
        jobs = []
        recommended_jobs = []

    # ==========================
    # Render Template
    # ==========================
    return render(request, "jobs/list_jobs.html", {
        "jobs": jobs,
        "recommended_jobs": recommended_jobs
    })

# ==========================================================
# JOB HUNT
# ==========================================================# 
from django.shortcuts import render
from skillbridge.supabase_client import supabase
from .services.supabase_crud import get_jobs

def jobhunt(request):
    try:
        # Fetch all jobs
        jobs = get_jobs()  # Returns list of dicts, e.g., [{"JobID": 1, "Title": ..., "Status": "Open"}, ...]

        # Fetch job-skill relations
        skills_resp = supabase.table("job_skill_list").select(
            "job_id, skill_list!inner(SkillID, SkillName)"
        ).execute()

        job_skills_by_name = {}
        job_skills_by_id = {}
        for item in skills_resp.data:
            job_id = item["job_id"]
            skill_name = item["skill_list"]["SkillName"]
            skill_id = item["skill_list"]["SkillID"]

            job_skills_by_name.setdefault(job_id, []).append(skill_name)
            job_skills_by_id.setdefault(job_id, []).append(skill_id)

        # Attach skills to jobs
        for job in jobs:
            job["skills"] = job_skills_by_name.get(job["JobID"], [])

        # Recommended jobs for logged-in residents only
        recommended_jobs = []
        if request.user.is_authenticated and request.session.get("user_role") == "Resident":
            resident_email = request.user.email
            supabase_resident = supabase.table("resident").select("id").eq("email", resident_email).execute()
            if supabase_resident.data:
                resident_id = supabase_resident.data[0]["id"]
                resident_skill_resp = supabase.table("resident_skills").select("skill_id").eq("resident_id", resident_id).execute()
                resident_skill_ids = {item["skill_id"] for item in resident_skill_resp.data}
                recommended_jobs = [
                    job for job in jobs
                    if any(skill_id in resident_skill_ids for skill_id in job_skills_by_id.get(job["JobID"], []))
                ]

    except Exception as e:
        print("Error fetching jobs:", e)
        jobs = []
        recommended_jobs = []

    return render(request, 'registration/jobhunt.html', {
        'jobs': jobs,
        'recommended_jobs': recommended_jobs
    })


# ==========================================================
# UPDATE JOB
# ==========================================================
def update_job_view(request, job_id):
    if request.session.get('user_role') != 'Official':
        messages.error(request, "Access denied. Officials only.")
        return redirect('login')

    email = request.user.email.strip().lower()
    official = supabase.table("registration_official").select("*").ilike("email", email).execute()
    official_data = official.data[0] if official.data else None

    if request.method == 'POST':
        try:
            updates = {
                "Title": request.POST.get('title'),
                "Description": request.POST.get('description'),
                "Status": request.POST.get('status'),
            }
            updates = {k: v for k, v in updates.items() if v}

            update_job(job_id, updates)

            # Update skills
            selected_skills = request.POST.getlist('skills')
            # Delete existing skills
            supabase.table("job_skill_list").delete().eq("job_id", job_id).execute()
            # Insert new skills
            import uuid
            for skill_id in selected_skills:
                supabase.table("job_skill_list").insert({
                    "id": str(uuid.uuid4()),
                    "job_id": job_id,
                    "skill_id": skill_id,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()

            log_action("edit", "job", job_id, request)
            messages.success(request, "Job updated successfully!")
            return redirect('official_dashboard')

        except Exception as e:
            messages.error(request, f"Error updating job: {str(e)}")

    try:
        job = get_job_by_id(job_id)
        # Fetch current skills for the job
        job_skills_resp = supabase.table("job_skill_list").select("skill_id").eq("job_id", job_id).execute()
        job_skill_ids = [s['skill_id'] for s in job_skills_resp.data] if job_skills_resp.data else []
    except Exception as e:
        messages.error(request, f"Error loading job: {str(e)}")
        job = None
        job_skill_ids = []

    # Fetch all skills
    skills_resp = supabase.table("skill_list").select("SkillID,SkillName").execute()
    skills = skills_resp.data if skills_resp.data else []

    return render(request, 'jobs/update_job.html', {'job': job, 'official': official_data, 'skills': skills, 'job_skill_ids': job_skill_ids})


# ==========================================================
# DELETE JOB
# ==========================================================
def delete_job_view(request, job_id):
    if request.session.get('user_role') != 'Official':
        messages.error(request, "Access denied. Officials only.")
        return redirect('login')
    try:
        delete_job(job_id)
        log_action("delete", "job", job_id, request)
        messages.success(request, "Job deleted successfully!")
    except Exception as e:
        messages.error(request, f"Error deleting job: {str(e)}")
    return redirect('official_dashboard')


# ==========================================================
# APPLY FOR JOB
# ==========================================================
def apply_job(request, job_id):
    if request.session.get('user_role') != 'Resident':
        messages.error(request, "Access denied. Residents only.")
        return redirect('login')
    try:
        resident = get_resident_by_user_id(request.user.id)

        if not resident:
            useraccount = supabase.table("registration_useraccount") \
                .select("*").eq("username", request.user.username).execute()

            if useraccount.data:
                useraccount_id = useraccount.data[0]["id"]

                supabase.table("registration_resident").insert({
                    "first_name": request.user.first_name or "",
                    "last_name": request.user.last_name or "",
                    "email": request.user.email or "",
                    "employment_status": "Unemployed",
                    "verification_status": "Pending",
                    "date_registered": datetime.utcnow().isoformat(),
                    "address": "",
                    "contact_number": "",
                    "birthdate": None,
                    "user_id": useraccount_id
                }).execute()

                resident = get_resident_by_user_id(request.user.id)

            else:
                messages.error(request, "User account not found!")
                return redirect('list_jobs')

        create_job_application(resident_id=resident['id'], job_id=job_id)
        return redirect('job_success')

    except Exception as e:
        messages.error(request, f"Error applying for job: {str(e)}")
        return redirect('list_jobs')

def job_detail(request, job_id):
    try:
        job = get_job_by_id(job_id)
        # Fetch required skills
        skills_resp = supabase.table("job_skill_list").select("skill_id, skill_list!inner(SkillName)").eq("job_id", job_id).execute()
        skills = [s['skill_list']['SkillName'] for s in skills_resp.data] if skills_resp.data else []
    except Exception as e:
        raise Http404("Job not found")
    context = {'job': job, 'required_skills': skills}
    return render(request, 'jobs/job_detail.html', context)

