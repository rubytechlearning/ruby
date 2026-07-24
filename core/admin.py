from django.contrib import admin
from .models import ContactLeads, Testimonials, Partner

# Register your models here.
admin.site.register([
    ContactLeads, 
    Testimonials,
    Partner
])