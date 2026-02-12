# accounts/forms.py
from django import forms
from .models import User

ROLE_CHOICES = [
    ('photographer', 'Photographer'),
    ('editor', 'Editor'),
    ('designer', 'Album Designer'),
    ('videographer', 'Videographer'),
]

class TeamMemberCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    photography_role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'photography_role']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'team'
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class TeamMemberEditForm(forms.ModelForm):
    photography_role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'photography_role']
