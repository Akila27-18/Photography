from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.core import signing
from django.core.cache import cache


from core.models import LoginPageConfig
from .models import PasswordResetRequest

# ------------------------------------------------------------------
# Custom User
# ------------------------------------------------------------------
User = get_user_model()

CACHE_KEY = "login_page_config"

def get_login_config():
    config = cache.get(CACHE_KEY)
    if not config:
        config = LoginPageConfig.objects.first()
        cache.set(CACHE_KEY, config, timeout=60 * 10)  # 10 minutes
    return config

# ------------------------------------------------------------------
# Root redirect
# ------------------------------------------------------------------
def root_redirect(request):
    """Redirect / → /login/"""
    return redirect('accounts:login')

# ------------------------------------------------------------------
# Admin login
# ------------------------------------------------------------------
def admin_login(request):
    config = get_login_config()

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user and user.is_staff:
            login(request, user)
            if not request.POST.get("remember_me"):
                request.session.set_expiry(0)
            return redirect('/leads/')

        messages.error(request, "Invalid credentials or not authorized.")

    return render(request, "accounts/login.html", {"config": config})

# ------------------------------------------------------------------
# Team login
# ------------------------------------------------------------------
def team_login(request):
    config = get_login_config()

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user and user.role == 'team':
            login(request, user)
            if not request.POST.get("remember_me"):
                request.session.set_expiry(0)
            return redirect('/team-dashboard/')

        messages.error(request, "Invalid credentials or not authorized as team member.")

    return render(request, "accounts/team_login.html", {"config": config})


def team_dashboard(request):
    if request.user.role != 'team':
        messages.error(request, "Unauthorized")
        return redirect('accounts:team_login')

    # Load team-specific projects/tasks here
    return render(request, "accounts/team_dashboard.html")

# ------------------------------------------------------------------
# Forgot password
# ------------------------------------------------------------------
def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        user = User.objects.filter(email=email).first()

        if user:
            token = signing.dumps(email)
            PasswordResetRequest.objects.create(user=user, token=token)

            superusers = User.objects.filter(is_superuser=True).values_list("email", flat=True)
            reset_url = f"http://127.0.0.1:8000/approve-reset/{token}/"

            send_mail(
                subject="Password Reset Approval",
                message=f"Approve password reset:\n\n{reset_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(superusers),
            )

        messages.success(request, "If this email exists, a reset request has been sent for approval.")

    return render(request, "accounts/forgot_password.html")

# ------------------------------------------------------------------
# Approve / Decline reset
# ------------------------------------------------------------------
def approve_reset(request, token):
    from django.core.signing import BadSignature, SignatureExpired

    try:
        email = signing.loads(token, max_age=900)  # 15 minutes
    except (BadSignature, SignatureExpired):
        return render(request, "accounts/invalid_token.html")

    req = PasswordResetRequest.objects.filter(token=token).first()
    if not req:
        return render(request, "accounts/invalid_token.html")

    if request.method == "POST":
        action = request.POST.get("action")
        req.approved = True if action == "approve" else False
        req.save()

        if req.approved:
            return redirect(f"/reset-password/{token}/")

        messages.info(request, "Password reset request declined.")

    return render(request, "accounts/approve_reset.html")

# ------------------------------------------------------------------
# Reset password
# ------------------------------------------------------------------
def reset_password(request, token):
    from django.core.signing import BadSignature, SignatureExpired

    try:
        email = signing.loads(token, max_age=900)
    except (BadSignature, SignatureExpired):
        return render(request, "accounts/invalid_token.html")

    user = User.objects.filter(email=email).first()
    if not user:
        return render(request, "accounts/invalid_token.html")

    if request.method == "POST":
        password = request.POST.get("password")
        user.set_password(password)
        user.save()

        messages.success(request, "Password reset successful. Please login.")
        return redirect('accounts:login')

    return render(request, "accounts/reset_password.html")

# ------------------------------------------------------------------
# Login page config API
# ------------------------------------------------------------------
def login_config_api(request):
    config = get_login_config()
    return JsonResponse({
        "welcome_text": config.welcome_text if config else "Hello, Welcome Back",
        "forgot_text": config.forgot_text if config else "Forgot Password?",
        "remember_me_enabled": config.remember_me_enabled if config else True,
    })
# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import TeamMemberCreationForm, TeamMemberEditForm
from .models import User

# --------------------------------------
# Team Members List (Admins only)
# --------------------------------------
def team_members_list(request):
    if not request.user.is_staff:
        messages.error(request, "Unauthorized")
        return redirect('accounts:login')

    members = User.objects.filter(role='team')
    return render(request, "accounts/team_members.html", {"members": members})

# --------------------------------------
# Add Team Member
# --------------------------------------
# accounts/views.py
from django.contrib.auth.hashers import make_password
from .models import User

def add_team_member(request):
    if not request.user.is_staff:
        messages.error(request, "Unauthorized")
        return redirect('accounts:login')

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")
        photography_role = request.POST.get("photography_role")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
        else:
            User.objects.create(
                username=username,
                email=email,
                password=make_password(password),
                role=role,
                photography_role=photography_role
            )
            messages.success(request, "Team member added successfully")
            return redirect('accounts:team_members')

    return render(request, "accounts/add_team_member.html")


# --------------------------------------
# Edit Team Member
# --------------------------------------
def edit_team_member(request, user_id):
    if not request.user.is_staff:
        messages.error(request, "Unauthorized")
        return redirect('accounts:login')

    member = get_object_or_404(User, id=user_id, role='team')

    if request.method == "POST":
        form = TeamMemberEditForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, "Team member updated successfully")
            return redirect('accounts:team_members')
    else:
        form = TeamMemberEditForm(instance=member)

    return render(request, "accounts/edit_team_member.html", {"form": form, "member": member})

# --------------------------------------
# Delete Team Member
# --------------------------------------
def delete_team_member(request, user_id):
    if not request.user.is_staff:
        messages.error(request, "Unauthorized")
        return redirect('accounts:login')

    member = get_object_or_404(User, id=user_id, role='team')
    member.delete()
    messages.success(request, "Team member deleted successfully")
    return redirect('accounts:team_members')

# --------------------------------------
# Admin Reset Team Member Password
# --------------------------------------
def admin_reset_team_password(request, user_id):
    if not request.user.is_staff:
        messages.error(request, "Unauthorized")
        return redirect('accounts:login')

    member = get_object_or_404(User, id=user_id, role='team')

    if request.method == "POST":
        new_password = request.POST.get("password")
        member.set_password(new_password)
        member.save()
        messages.success(request, "Password reset successfully")
        return redirect('accounts:team_members')

    return render(request, "accounts/reset_team_password.html", {"member": member})

# List team members
def team_members_list(request):
    if not request.user.is_staff:
        messages.error(request, "Unauthorized")
        return redirect('accounts:login')

    members = User.objects.filter(role='team')
    return render(request, "accounts/team_members.html", {"members": members})

# Add / Edit / Delete / Reset Password as we created previously


