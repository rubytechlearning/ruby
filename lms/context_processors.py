# courses/context_processors.py
from .models import Category

def categories_processor(request):
    # Return all categories; you may want to cache this for performance
    return {
        'categories': Category.objects.all(),
    }