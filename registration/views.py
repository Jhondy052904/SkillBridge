from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from supabase import create_client

# Initialize Supabase client
SUPABASE_URL = "https://sfgnccdbgmewovbogibo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNmZ25jY2RiZ21ld292Ym9naWJvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg4NTgxMjYsImV4cCI6MjA3NDQzNDEyNn0.ZPrGL60IPIuS9DClstiv21r_Ss6RGluj18b0ulOGnLc"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def index(request):
    return render(request, 'index.html')


def home(request):
    return render(request, 'home.html')


def signup_view(request):
    """
    Render signup page - signup handled by Supabase in frontend
    """
    return render(request, 'signup.html')


@csrf_protect
def login_view(request):
    """
    Handle login with username and password via Supabase authentication
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        print(f"=== LOGIN ATTEMPT ===")
        print(f"Username: {username}")
        print(f"Password length: {len(password)}")
        
        # Authenticate user using custom Supabase backend
        user = authenticate(request, username=username, password=password)
        
        print(f"Authentication result: {user}")
        
        if user is not None:
            # Login successful
            login(request, user)
            
            # Get user role from session
            user_role = request.session.get('user_role', 'Resident')
            
            print(f"Login successful! User role: {user_role}")
            
            # Redirect based on role
            if user_role == 'Admin':
                return redirect('home')
            else:
                return redirect('home')
        else:
            # Login failed
            print("Authentication failed!")
            messages.error(request, 'Invalid username or password')
            return render(request, 'registration/login.html', {
                'form': {'non_field_errors': ['Invalid username or password']}
            })
    
    # GET request - show login form
    return render(request, 'registration/login.html')


def logout_view(request):
    """
    Handle logout and clear session
    """
    logout(request)
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')