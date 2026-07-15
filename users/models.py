import secrets
import string

from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class User(AbstractUser):
    # Add any additional fields you want for your custom user model
    is_student = models.BooleanField(default=False)
    is_instructor = models.BooleanField(default=False)


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    # Add any additional fields you want for the student profile
    # For example:
    # bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    student_id = models.CharField(max_length=8, unique=False, null=True, editable=False, db_index=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.user.username
    
    
    def save(self, *args, **kwargs):
        if not self.student_id:
            self.student_id = self.generate_unique_short_id()
        super().save(*args, **kwargs)

    
    @classmethod
    def generate_unique_short_id(cls):
        # Define the allowed characters (uppercase + digits to avoid confusion)
        alphabet = string.ascii_uppercase + string.digits  # e.g., A-Z, 0-9
        length = 8
        
        # Keep generating until we find a unique one
        while True:
            # Generate a random 8-character string
            code = ''.join(secrets.choice(alphabet) for _ in range(length))
            # Check if it already exists in the database
            if not cls.objects.filter(student_id=code).exists():
                return code


class InstructorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor_profile')
    # Add any additional fields you want for the instructor profile
    # For example:
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    def __str__(self):
        return self.user.username
    
