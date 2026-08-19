from django.urls import path
from . import views

urlpatterns = [
    path('courses/', views.courses, name='courses'),
    path('categories/', views.categories, name='categories'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('courses/<int:course_id>/initiate/payment/', views.initiate_payment, name='initiate_payment'),
]


