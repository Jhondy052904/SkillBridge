from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect


def index(request):
    return render(request, 'index.html')


def home(request):
    return render(request, 'home.html')


def signup_view(request):
    """
    Render signup page - actual signup is handled by Supabase in the frontend
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
        
        # Authenticate user using custom Supabase backend
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Login successful
            login(request, user)
            
            # Get user role from session
            user_role = request.session.get('user_role', 'Resident')
            
            # Redirect based on role
            if user_role == 'Admin':
                return redirect('home')  # Update to admin dashboard if you have one
            else:
                return redirect('home')  # Redirect to home page
        else:
            # Login failed
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
    # Clear Supabase session data
    request.session.flush()
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')