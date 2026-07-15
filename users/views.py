from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import UserRegisterForm, LoginForm, StudentUserForm, StudentProfileForm
from .models import User, StudentProfile, InstructorProfile

# Create your views here.


def signup(request):

    if request.method == "POST":

        form = UserRegisterForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)

            role = form.cleaned_data["role"]

            if role == "student":
                user.is_student = True
            else:
                user.is_instructor = True

            user.save()

            if user.is_student:
                StudentProfile.objects.create(user=user)

            if user.is_instructor:
                InstructorProfile.objects.create(user=user)

            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'index'
            messages.success(request, f"Account created for {user.username}!")
            return redirect(next_url)

    else:
        form = UserRegisterForm()

    return render(request, "sign-up.html", {
        "form": form
    })



def signin(request):

    form = LoginForm(request, data=request.POST or None)

    if request.method == "POST":

        if form.is_valid():

            login(request, form.get_user())
            messages.success(request, f"Welcome back, {form.get_user().username}!")
            return redirect("index")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "sign-in.html", {
        "form": form
    })


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def student_profile_update(request):

    profile = request.user.student_profile

    if request.method == "POST":

        user_form = StudentUserForm(
            request.POST,
            instance=request.user
        )

        profile_form = StudentProfileForm(
            request.POST,
            instance=profile
        )

        if user_form.is_valid() and profile_form.is_valid():

            user_form.save()
            profile_form.save()

            messages.success(request, "Profile updated successfully.")

            return redirect("student_dashboard")

    else:

        user_form = StudentUserForm(instance=request.user)

        profile_form = StudentProfileForm(instance=profile)

    return render(
        request,
        "profile-update.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
        },
    )
    