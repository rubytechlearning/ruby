from django.shortcuts import render
from .models import Course, Category, EnrolledStudent

# Create your views here.

def courses(request):
    courses = Course.objects.all()
    return render(request, 'courses-v1.html', {'courses': courses})



def course_detail(request, course_id):
    course = Course.objects.get(id=course_id)
    return render(request, 'course-detail-v1.html', {'course': course})