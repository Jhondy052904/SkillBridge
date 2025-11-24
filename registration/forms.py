from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
from django import forms
from .models import Resident, Skill

# class ResidentForm(forms.ModelForm):
#     class Meta:
#         model = Resident
#         fields = ['first_name', 'middle_name', 'last_name', 'address', 'contact_number', 'employment_status', 'skills']
#         widgets = {
#             'skills': forms.Textarea(attrs={'rows': 2}),
#         }

# class CustomUserCreationForm(UserCreationForm):
#     username = forms.CharField(
#         max_length=20,  # maximum length
#         min_length=3,   # minimum length (can adjust)
#         required=True,
#         help_text="3–20 Chars and Special Chars only."
#     )

#     class Meta:
#         model = User
#         fields = ("username", "password1", "password2")

class ResidentForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': 6})
    )

    class Meta:
        model = Resident
        fields = ['first_name', 'middle_name', 'last_name', 'address', 'contact_number', 'employment_status', 'skills', 'current_status']
        labels = {
            'first_name': '', 'middle_name': '', 'last_name': '',
            'address': '', 'contact_number': '', 'employment_status': '', 'skills': '', 'current_status': '',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class':'form-control', 'placeholder':' '}),
            'middle_name': forms.TextInput(attrs={'class':'form-control', 'placeholder':' '}),
            'last_name': forms.TextInput(attrs={'class':'form-control', 'placeholder':' '}),
            'address': forms.TextInput(attrs={'class':'form-control', 'placeholder':' '}),
            'contact_number': forms.TextInput(attrs={'class':'form-control', 'placeholder':' '}),
            'employment_status': forms.Select(attrs={'class':'form-control'}),
            'current_status': forms.Select(attrs={'class':'form-control'}),
        }

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
