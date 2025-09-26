from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        max_length=20,  # maximum length
        min_length=3,   # minimum length (can adjust)
        required=True,
        help_text="3–20 Chars and Special Chars only."
    )

    class Meta:
        model = User
        fields = ("username", "password1", "password2")
