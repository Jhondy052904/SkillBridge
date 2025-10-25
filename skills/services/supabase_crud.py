from skillbridge.supabase_client import supabase
from typing import List, Dict, Any

# Skills CRUD
def create_skill(skill_name: str, description: str) -> Dict[str, Any]:
    response = supabase.table('skills').insert({
        'SkillName': skill_name,
        'Description': description,
    }).execute()
    if response.data:
        return response.data[0]
    raise Exception(f"Error creating skill: {response}")

def get_skills() -> List[Dict[str, Any]]:
    response = supabase.table('skills').select('*').execute()
    return response.data

def update_skill(skill_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    response = supabase.table('skills').update(updates).eq('SkillID', skill_id).execute()
    if response.data:
        return response.data[0]
    raise Exception(f"Error updating skill: {response}")

def delete_skill(skill_id: str) -> None:
    response = supabase.table('skills').delete().eq('SkillID', skill_id).execute()
    if not response.data:
        raise Exception(f"Error deleting skill: {response}")