
import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


from users.models import StudentProfile
from .models import Course, Category, EnrolledStudent, PaymentRecord

# Create your views here.

# ---------- Course Views ----------
def courses(request):
    courses = Course.objects.all()
    return render(request, 'courses-v1.html', {'courses': courses})


# --------- Course Detail View ----------
def course_detail(request, course_id):
    course = Course.objects.get(id=course_id)
    return render(request, 'courses-details-v1.html', {'course': course})


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
                PaymentRecord.objects.create(
                    student=student,
                    course=course,
                    amount=course.price,
                    transaction_id=reference,
                    payment_method='Paystack'
                )
                # Optionally, mark enrollment as completed or update progress? Not required.

            return render(request, 'payment-success.html')
        else:
            return render(request, 'payment-error.html', {'error': 'Payment verification failed', 'course':course})
    except Exception as e:
        return render(request, 'payment-error.html', {'error': str(e), 'course':course})
    
    
def instructor_dashboard(request):
    # Placeholder for instructor dashboard view
    return render(request, 'instructor-dashboard.html')

