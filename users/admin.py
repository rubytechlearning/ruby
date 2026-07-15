from django.contrib import admin

from .models import User, StudentProfile, InstructorProfile
# Register your models here.

admin.site.register([User, StudentProfile, InstructorProfile])