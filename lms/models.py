from django.db import models

# Create your models here.

class MetaData(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # This tells Django NOT to make a separate database table for MetaData
        abstract = True
    

class Category(MetaData):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image_file = models.ImageField(upload_to='categories/', null=True, blank=True)

    def __str__(self):
        return self.name



class Course(MetaData):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image_file = models.FileField(upload_to='courses/images/', blank=True, null=True)
    outline = models.TextField(help_text="What you will learn, modules, and key topics covered.")
    course_material_list = models.TextField(help_text="List of course materials, resources, and references.")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='courses')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    review = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    instructor = models.ForeignKey('users.InstructorProfile', on_delete=models.CASCADE, related_name='courses', null=True, blank=True)
    is_trending = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_popular = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class CourseMaterial(MetaData):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    has_pdf = models.BooleanField(default=False)
    pdf_file = models.FileField(upload_to='Materials/pdfs/')
    has_video = models.BooleanField(default=False)
    video_file = models.FileField(upload_to='Materials/videos/')
    has_notes = models.BooleanField(default=False)
    notes_file = models.FileField(upload_to='Materials/notes/')
    has_content = models.BooleanField(default=False)
    content = models.TextField(blank=True, null=True)
    
    
    def __str__(self):
        return f"{self.title} - {self.course.title}"
    

class EnrolledStudent(MetaData):
    student = models.ForeignKey('users.StudentProfile', on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrolled_students')
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    completed = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.user.username} - {self.course.title}"


class PaymentRecord(MetaData):
    student = models.ForeignKey('users.StudentProfile', on_delete=models.CASCADE, related_name='payments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.student.user.username} - {self.course.title} - {self.amount}"