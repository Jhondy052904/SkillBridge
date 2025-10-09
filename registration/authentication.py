from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from supabase import create_client, Client

# Initialize Supabase client
SUPABASE_URL = "https://sfgnccdbgmewovbogibo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNmZ25jY2RiZ21ld292Ym9naWJvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg4NTgxMjYsImV4cCI6MjA3NDQzNDEyNn0.ZPrGL60IPIuS9DClstiv21r_Ss6RGluj18b0ulOGnLc"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class SupabaseAuthBackend(BaseBackend):
    """
    Custom authentication backend that authenticates against Supabase
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            print("Username or password is None")
            return None
        
        try:
            print(f"🔍 Attempting to authenticate username: {username}")
            
            # 1. Look up the user by username
            response = supabase.table("user_account").select("id, username, role, password_hash").eq("username", username).execute()
            
            print(f"📊 User lookup response: {response.data}")
            
            if not response.data or len(response.data) == 0:
                print(f"Username '{username}' not found in user_account table")
                return None
            
            user_data = response.data[0]
            user_id = user_data['id']
            supabase_uuid = user_data['password_hash']  # This stores the Supabase Auth UUID
            
            print(f"Found user_id: {user_id}, Supabase UUID: {supabase_uuid}")
            
            # 2. Get email from resident table
            resident_response = supabase.table("resident").select("email").eq("user_id", user_id).execute()
            
            print(f"Resident lookup response: {resident_response.data}")
            
            if not resident_response.data or len(resident_response.data) == 0:
                print(f"No resident record found for user_id: {user_id}")
                return None
            
            email = resident_response.data[0]['email']
            
            print(f"Found email: {email}")
            print(f"Attempting Supabase auth with email: {email}")
            
            # 3. Authenticate with Supabase Auth using email and password
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            print(f"🔑 Auth response user: {auth_response.user}")
            
            if auth_response.user:
                print(f"Supabase authentication successful!")
                
                # 4. Get or create Django user
                django_user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'is_staff': user_data['role'] == 'Admin',
                        'is_superuser': user_data['role'] == 'Admin'
                    }
                )
                
                print(f"Django user {'created' if created else 'found'}: {django_user.username}")
                
                # Update email if it changed
                if django_user.email != email:
                    django_user.email = email
                    django_user.save()
                
                # Store session data
                if request:
                    request.session['supabase_access_token'] = auth_response.session.access_token
                    request.session['supabase_user_id'] = str(user_id)
                    request.session['user_role'] = user_data['role']
                
                return django_user
            else:
                print("Supabase auth returned no user")
            
        except Exception as e:
            print(f"Authentication error: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None