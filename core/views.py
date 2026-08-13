from django.shortcuts import render, get_object_or_404
from django.contrib import messages

from lms.models import Course, Category
from users.models import InstructorProfile as Instructor

from .models import ContactLeads, Testimonials, Partner


# Create your views here.

def index(request):
    categories = Category.objects.all()[:6]  # Limit to 6 categories
    courses = Course.objects.all().order_by('timestamp')[:6]  # Limit to 6 courses
    testimonials = Testimonials.objects.all()[:4]
    instructors = Instructor.objects.all()[:6]
    partners = Partner.objects.all()[:6]
    has_partners = partners.exists()  # Check if there are any partners
    has_testimonials = testimonials.exists()  # Check if there are any testimonials
    has_instructors = instructors.exists()  # Check if there are any instructors
    has_blog_post = False
    
    context = {
        'categories': categories,
        'courses': courses,
        'testimonials': testimonials,
        'instructors': instructors,
        'trending_courses':courses.filter(is_trending=True)[:6],  # Limit to 6 trending courses
        'popularity_courses':courses.filter(is_popular=True)[:6],  # Limit to 6 popular courses
        'featured_courses':courses.filter(is_featured=True)[:6],  # Limit to 6 featured courses
        'partners': partners,
        'has_partners': has_partners,  # Pass the boolean
        'has_testimonials': has_testimonials,  # Pass the boolean
        'has_instructors': has_instructors,  # Pass the boolean
        'has_blog_post': has_blog_post,  # Pass the boolean
    }
    
    return render(request, 'index.html', context)

def about(request):
    return render(request, 'about-us-v1.html')


def programs(request):
    return render(request, 'programs.html')

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


def terms_service(request):
    return render(request, 'terms-of-service.html')


def privacy_policy(request):
    return render(request, 'privacy-policy.html')


def get_courses_category(request, cate_id):
    category = get_object_or_404(Category, id=cate_id)
    courses = Course.objects.filter(category=category)
    return render(request, "courses-v1.html", {"courses":courses})


def get_courses_category_name(request, name):
    category = get_object_or_404(Category, name=name)
    courses = Course.objects.filter(category=category)
    return render(request, "courses-v1.html", {"courses":courses})


# remove to their apps



def blog(request):
    return render(request, 'blog-grid.html')
