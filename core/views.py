
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import CustomUser, Teacher


# =====================================
# LOGIN PAGE
# =====================================

def login_view(request):
    error = ""

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password")
        role = request.POST.get("role", "").upper()

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None and user.role == role:
            login(request, user)
            return redirect('dashboard')
        else:
            error = "Invalid username, password or role."

    return render(request, 'login.html', {
        'error': error
    })


# =====================================
# PRINCIPAL REGISTRATION
# =====================================

def principal_register(request):
    error = ""

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            error = "Passwords do not match."

        elif CustomUser.objects.filter(username=username).exists():
            error = "Username already exists."

        elif CustomUser.objects.filter(email=email).exists():
            error = "Email is already registered."

        else:
            try:
                validate_password(password)

                CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    first_name=full_name,
                    password=password,
                    role='PRINCIPAL'
                )

                return redirect('login')

            except ValidationError as e:
                error = " ".join(e.messages)

    return render(request, 'principal_register.html', {
        'error': error
    })


# =====================================
# VICE PRINCIPAL REGISTRATION
# =====================================

def vice_principal_register(request):
    error = ""

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            error = "Passwords do not match."

        elif CustomUser.objects.filter(username=username).exists():
            error = "Username already exists."

        elif CustomUser.objects.filter(email=email).exists():
            error = "Email is already registered."

        else:
            try:
                validate_password(password)

                CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    first_name=full_name,
                    password=password,
                    role='VICE_PRINCIPAL'
                )

                return redirect('login')

            except ValidationError as e:
                error = " ".join(e.messages)

    return render(request, 'vice_principal_register.html', {
        'error': error
    })


# =====================================
# DASHBOARD
# =====================================

@login_required
def dashboard(request):
    return render(request, 'dashboard.html', {
        'username': request.user.username,
        'full_name': request.user.first_name,
        'role': request.user.get_role_display()
    })


# =====================================
# LOGOUT
# =====================================

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# =====================================
# TEACHER MANAGEMENT
# =====================================


# =====================================
# TEACHER MANAGEMENT
# =====================================

@login_required
def teacher_management(request):

    if request.user.role not in ['PRINCIPAL', 'VICE_PRINCIPAL']:
        return redirect('dashboard')

    error = ""

    if request.method == "POST":

        teacher_id = request.POST.get("teacher_id", "").strip()
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        subjects = request.POST.get("subjects", "").strip()

        # Check required fields
        if not all([full_name, email, phone, subjects]):
            error = "Please fill in all required fields."

        # Check Teacher ID only if provided
        elif teacher_id and Teacher.objects.filter(
            teacher_id=teacher_id
        ).exists():
            error = "Teacher ID already exists."

        # Check duplicate email
        elif Teacher.objects.filter(email=email).exists():
            error = "Email address already exists."

        else:
            Teacher.objects.create(
                teacher_id=teacher_id or None,
                full_name=full_name,
                email=email,
                phone=phone,
                subjects=subjects
            )

            return redirect('teacher_management')

    teachers = Teacher.objects.all().order_by('full_name')

    return render(request, 'teacher_management.html', {
        'teachers': teachers,
        'error': error
    })

# =====================================
# EDIT TEACHER
# =====================================

@login_required
def edit_teacher(request, teacher_pk):

    if request.user.role not in ['PRINCIPAL', 'VICE_PRINCIPAL']:
        return redirect('dashboard')

    try:
        teacher = Teacher.objects.get(pk=teacher_pk)
    except Teacher.DoesNotExist:
        return redirect('teacher_management')

    error = ""

    if request.method == "POST":

        teacher_id = request.POST.get("teacher_id", "").strip()
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        subjects = request.POST.get("subjects", "").strip()

        if not all([full_name, email, phone, subjects]):
            error = "Please fill in all required fields."

        elif Teacher.objects.filter(teacher_id=teacher_id).exclude(pk=teacher.pk).exists() if teacher_id else False:
            error = "Teacher ID already exists."

        elif Teacher.objects.filter(email=email).exclude(pk=teacher.pk).exists():
            error = "Email address already exists."

        else:
            teacher.teacher_id = teacher_id or None
            teacher.full_name = full_name
            teacher.email = email
            teacher.phone = phone
            teacher.subjects = subjects
            teacher.save()

            return redirect('teacher_management')

    return render(request, 'edit_teacher.html', {
        'teacher': teacher,
        'error': error
    })


# =====================================
# DELETE TEACHER
# =====================================

@login_required
def delete_teacher(request, teacher_pk):

    if request.user.role not in ['PRINCIPAL', 'VICE_PRINCIPAL']:
        return redirect('dashboard')

    if request.method == "POST":
        Teacher.objects.filter(pk=teacher_pk).delete()

    return redirect('teacher_management')


# =====================================
# CREATE TIMETABLE PAGE
# =====================================

@login_required
def create_timetable(request):

    if request.user.role not in ['PRINCIPAL', 'VICE_PRINCIPAL']:
        return redirect('dashboard')

    error = ""
    success = ""

    if request.method == "POST":

        school_start = request.POST.get("school_start", "")
        school_end = request.POST.get("school_end", "")
        working_days = request.POST.get("working_days", "")
        periods = request.POST.get("periods", "")

        short_break_start = request.POST.get("short_break_start", "")
        short_break_end = request.POST.get("short_break_end", "")

        lunch_start = request.POST.get("lunch_start", "")
        lunch_end = request.POST.get("lunch_end", "")

        selected_classes = request.POST.getlist("classes")
        sections = request.POST.get("sections", "").strip()

        if not all([
            school_start,
            school_end,
            working_days,
            periods,
            short_break_start,
            short_break_end,
            lunch_start,
            lunch_end
        ]):
            error = "Please fill in all the timetable details."

        elif not selected_classes or not sections:
            error = "Please select classes and enter sections."

        elif school_start >= school_end:
            error = "School ending time must be after starting time."

        elif short_break_start >= short_break_end:
            error = "Please enter valid short break timings."

        elif lunch_start >= lunch_end:
            error = "Please enter valid lunch timings."

        elif not periods.isdigit() or not (1 <= int(periods) <= 12):
            error = "Periods per day must be between 1 and 12."

        else:
            success = (
                "Timetable settings received successfully. "
                "Database saving will be added next."
            )

    return render(request, 'create_timetable.html', {
        'error': error,
        'success': success
    })
