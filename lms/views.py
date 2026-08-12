
import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.conf import settings
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.forms import modelformset_factory
from django.db import transaction

from users.models import StudentProfile
from .models import Course, Category, EnrolledStudent, PaymentRecord, ClassSession, AttendanceRecord

# Create your views here.

# ---------- Course Views ----------
def courses(request):
    from django.db.models import Q

    queryset = Course.objects.all()
    q = request.GET.get('q')
    category = request.GET.get('category')

    if q:
        # Search by course title OR category name (case‑insensitive)
        queryset = queryset.filter(
            Q(title__icontains=q) | Q(category__name__icontains=q)
        )

    if category:
        # Filter by category name (exact match, case‑insensitive)
        queryset = queryset.filter(category__name__iexact=category)

    # Optional: ordering, pagination, etc.
    context = {'courses': queryset}
    paginator = Paginator(queryset, 12)   # 12 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context.update({'page_obj': page_obj})
    return render(request,  'courses-v1.html', context)
    

# --------- Course Detail View ----------
def course_detail(request, course_id):
    course = Course.objects.get(id=course_id)
    outline_list = course.outline.split(',') if course.outline else []
    context = {'course': course, 'outline_items': outline_list}
    return render(request, 'courses-details-v1.html', context)


# --------- Enroll in Course View ----------
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.user.is_authenticated and request.user.is_student:
        EnrolledStudent.objects.get_or_create(student=request.user.student_profile, course=course)
        messages.success(request, f"You have successfully enrolled in {course.title}!")
        return redirect('course_detail', course_id=course.id)
    else:
        referer = request.META.get('HTTP_REFERER')
        if referer:
            messages.error(request, "You need to be logged in as a student to enroll in a course.")
            return redirect(referer)    
        return redirect('login')


# --------- Student Dashboard View ----------
@login_required
def student_dashboard(request):
    context = {}
    try:
        student = request.user.student_profile
        context.update({'student':student})
    except StudentProfile.DoesNotExist:
        referer = request.META.get('HTTP_REFERER')
        if referer:
            messages.error(request, "You need to be logged in as a student to access the dashboard.")
            return redirect(referer)  
         
    enrolled_courses = EnrolledStudent.objects.filter(student=request.user.student_profile)
    payment_history = PaymentRecord.objects.filter(student=request.user.student_profile)
    payment_status = {record.course.id: record for record in payment_history}
    total_amount_paid = sum(record.amount for record in payment_history)
    materials = {enrollment.course.id: enrollment.course.materials.all() for enrollment in enrolled_courses}
    
    context.update({
        'enrolled_courses': enrolled_courses, 
        'payment_status': payment_status,
        'payments': payment_history,
        'total_paid': total_amount_paid,
        'materials': materials
    })
    
    
    return render(request, 'student-dashboard.html', context)



# ---------- Paystack Payment Initiation ----------
@login_required
def initiate_payment(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.user.is_authenticated and request.user.is_student:
        student = request.user.student_profile
        
        # Check if the student is enrolled in the course
        if not EnrolledStudent.objects.filter(student=student, course=course).exists():
            messages.error(request, "You need to enroll in the course before making a payment.")
            return redirect('course_detail', course_id=course.id)
        
        # Check if the student has already made a payment for the course
        if PaymentRecord.objects.filter(student=student, course=course).exists():
            messages.info(request, "You have already made a payment for this course.")
            return redirect('student_dashboard')
        
        # Prepare Paystack data
        amount = int(course.price * 100)  # Paystack uses kobo (cents)
        email = request.user.email
        callback_url = settings.PAYSTACK_CALLBACK_URL

        payload = {
            'amount': amount,
            'email': email,
            'callback_url': callback_url,
            'metadata': {
                'student_id': student.id,
                'course_id': course.id,
            }
        }

        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            'Content-Type': 'application/json',
        }

        try:
            response = requests.post(
                'https://api.paystack.co/transaction/initialize',
                json=payload,
                headers=headers
            )
            response_data = response.json()
            if response_data['status']:
                # Redirect user to Paystack payment page
                payment_url = response_data['data']['authorization_url']
                messages.success(request, "Payment initiated successfully. You will be redirected to Paystack.")
                return redirect(payment_url)
            else:
                # Handle error
                messages.error(request, "Failed to initiate payment.")
                return render(request, 'payment-error.html', {'error': response_data.get('message'), 'course':course})
        except Exception as e:
            messages.error(request, "An error occurred while initiating payment.")
            return render(request, 'payment-error.html', {'error': str(e), 'course':course})   
    else:
        messages.error(request, "You need to be logged in as a student to make a payment.")
        return redirect('login')


# ---------- Paystack Callback (verification) ----------
@csrf_exempt   # Paystack will POST to this URL; use csrf_exempt for simplicity (or use a non-CSRF endpoint)
def payment_callback(request):
    # Paystack sends a GET request with reference and other params
    reference = request.GET.get('reference')
    if not reference:
        return JsonResponse({'status': 'error', 'message': 'No reference provided'}, status=400)

    # Verify transaction with Paystack
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
    }
    verify_url = f'https://api.paystack.co/transaction/verify/{reference}'
    try:
        response = requests.get(verify_url, headers=headers)
        response_data = response.json()
        if response_data['status'] and response_data['data']['status'] == 'success':
            # Extract metadata
            metadata = response_data['data']['metadata']
            student_id = metadata.get('student_id')
            course_id = metadata.get('course_id')
            if not student_id or not course_id:
                return JsonResponse({'status': 'error', 'message': 'Missing metadata'}, status=400)

            student = get_object_or_404(StudentProfile, id=student_id)
            course = get_object_or_404(Course, id=course_id)

            # Check if payment already recorded
            if not PaymentRecord.objects.filter(student=student, course=course).exists():
                # Create payment record
                payRecord = PaymentRecord.objects.create(
                    student=student,
                    course=course,
                    amount=course.price,
                    transaction_id=reference,
                    payment_method='Paystack',
                    status='Paid'
                )
                record = EnrolledStudent.objects.get(student=student, course=course)
                record.paid = True
                record.save()
                # Optionally, mark enrollment as completed or update progress? Not required.

            return render(request, 'payment-success.html', {'payment':payRecord})
        else:
            return render(request, 'payment-error.html', {'error': 'Payment verification failed', 'course':course})
    except Exception as e:
        return render(request, 'payment-error.html', {'error': str(e), 'course':course})


@login_required
def instructor_mark_attendance(request, session_id):
    # 1. Get the session and ensure the instructor owns the course
    session = get_object_or_404(ClassSession, id=session_id)
    course = session.course

    # Permission check: Only the assigned instructor can mark attendance
    try:
        instructor_profile = request.user.instructor_profile
    except AttributeError:
        messages.error(request, "You are not an instructor.")
        return redirect('home')

    if course.instructor != instructor_profile:
        messages.error(request, "You are not authorized to mark attendance for this course.")
        return redirect('home')

    # 2. Get all students enrolled in this course
    enrolled_students = EnrolledStudent.objects.filter(course=course).select_related('student')

    # 3. Ensure every enrolled student has an AttendanceRecord for this session
    #    (This prevents missing rows in the form)
    for enrollment in enrolled_students:
        AttendanceRecord.objects.get_or_create(
            student=enrollment.student,
            session=session,
            defaults={'status': 'absent'}  # Default to absent if not marked yet
        )

    # 4. Fetch all records for this session to edit
    attendance_queryset = AttendanceRecord.objects.filter(session=session).select_related('student__user')

    # 5. Setup the ModelFormSet
    AttendanceFormSet = modelformset_factory(
        AttendanceRecord,
        fields=('status', 'check_in_time', 'remarks'),  # Only these fields are editable by instructor
        extra=0,  # We don't want empty extra forms
        labels={
            'status': 'Status',
            'check_in_time': 'Check-in Time',
            'remarks': 'Remarks'
        }
    )

    if request.method == 'POST':
        formset = AttendanceFormSet(request.POST, queryset=attendance_queryset)
        if formset.is_valid():
            with transaction.atomic():
                formset.save()
            messages.success(request, f"Attendance for {session.title} updated successfully!")
            return redirect('instructor_course_detail', course_id=course.id)  # Redirect back to course dashboard
    else:
        formset = AttendanceFormSet(queryset=attendance_queryset)

    # Prepare context for template
    context = {
        'session': session,
        'course': course,
        'formset': formset,
        'students': attendance_queryset,  # For display purposes
    }
    return render(request, 'instructor_mark_attendance.html', context)
    
    
def instructor_dashboard(request):
    # Placeholder for instructor dashboard view
    return render(request, 'instructor-dashboard.html')


