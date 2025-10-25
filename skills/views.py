from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .services.supabase_crud import create_skill, get_skills, update_skill, delete_skill

@login_required
def post_skill(request):
    if request.method == 'POST':
        try:
            data = request.POST
            skill = create_skill(
                skill_name=data['skill_name'],
                description=data.get('description', '')
            )
            messages.success(request, "Skill created successfully!")
            return redirect('skills_dashboard')
        except Exception as e:
            messages.error(request, f"Error creating skill: {str(e)}")
    return render(request, 'skills/post_skill.html')

@login_required
def admin_post_skill(request):
    if not request.user.is_staff:  # Or check custom role
        messages.error(request, "Access denied.")
        return redirect('home')
    if request.method == 'POST':
        try:
            data = request.POST
            skill = create_skill(
                skill_name=data['skill_name'],
                description=data.get('description', '')
            )
            messages.success(request, "Skill created successfully!")
            return redirect('admin_dashboard')
        except Exception as e:
            messages.error(request, f"Error creating skill: {str(e)}")
    return render(request, 'skills/post_skill.html')

@login_required
def list_skills(request):
    try:
        skills = get_skills()
    except Exception as e:
        messages.error(request, f"Error loading skills: {str(e)}")
        skills = []
    return render(request, 'skills/list_skills.html', {'skills': skills})

@login_required
def update_skill_view(request, skill_id):
    if request.method == 'POST':
        try:
            updates = {k: v for k, v in request.POST.items() if k != 'csrfmiddlewaretoken'}
            # Map form fields to table columns if needed
            mapped_updates = {
                'SkillName': updates.get('skill_name'),
                'Description': updates.get('description'),
            }
            updated_skill = update_skill(skill_id, {k: v for k, v in mapped_updates.items() if v is not None})
            messages.success(request, "Skill updated!")
            return redirect('list_skills')
        except Exception as e:
            messages.error(request, f"Error updating skill: {str(e)}")
    # Pre-fill form with existing data
    try:
        skills = get_skills()
        skill = next((s for s in skills if s['SkillID'] == skill_id), None)
    except:
        skill = None
    return render(request, 'skills/update_skill.html', {'skill': skill})

@login_required
def delete_skill_view(request, skill_id):
    try:
        delete_skill(skill_id)
        messages.success(request, "Skill deleted!")
    except Exception as e:
        messages.error(request, f"Error deleting skill: {str(e)}")
    return redirect('list_skills')
