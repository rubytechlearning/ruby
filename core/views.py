from django.shortcuts import render
from django.contrib import messages

from lms.models import Course, Category
from users.models import InstructorProfile as Instructor

from .models import ContactLeads, Testimonials


# Create your views here.

def index(request):
    categories = Category.objects.all()[:6]  # Limit to 6 categories
    courses = Course.objects.all()
    testimonials = Testimonials.objects.all()[:4]
    instructors = Instructor.objects.all()[:6]
    
    
    context = {
        'categories': categories,
        'courses': courses,
        'testimonials': testimonials,
        'instructors': instructors,
        'trending_courses':courses.filter(is_trending=True)[:6],  # Limit to 6 trending courses
        'popularity_courses':courses.filter(is_popular=True)[:6],  # Limit to 6 popular courses
        'featured_courses':courses.filter(is_featured=True)[:6],  # Limit to 6 featured courses
    }
    
    return render(request, 'index.html', context)

def about(request):
    return render(request, 'about-us-v1.html')

def contact(request):
    if request.method == 'POST':
        # Handle form submission here
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        phone_no = request.POST.get('phone')

        # Create a new ContactLeads instance
        contact_lead = ContactLeads(
            name=name,
            email=email,
            subject=subject,
            message=message,
            phone_no=phone_no
        )
        contact_lead.save()
        messages.success(request, 'Your message has been sent successfully!')
        return render(request, 'contact-us.html')
    return render(request, 'contact-us.html')




# remove to their apps



def blog(request):
    return render(request, 'blog-grid.html')
