from django.shortcuts import render
from .models import Review

# Create your views here.


def index(request):
    reviews = Review.objects.all()
    return render(request, 'reviews/reviews_index.template.html', {
        'reviews': reviews
    })