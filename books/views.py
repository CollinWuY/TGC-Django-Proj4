from django.shortcuts import (
    render,
    HttpResponse,
    redirect,
    get_object_or_404,
    reverse)
from django.template.loader import render_to_string
from .models import Book, Category, Genre, Tag
from reviews.models import Review
from .forms import BookForm
from reviews.forms import ReviewForm
from django.db.models import Q
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.


def redirect_view(request):
    response = redirect('/books/')
    return response


def homepage(request):
    books = Book.objects.all()
    books_nav = books.order_by('-release_date')[:2]
    books_cut = books.order_by('-release_date')[:10]
    cart = request.session.get('shopping_cart', {})
    grand_total = 0
    for item in cart:
        grand_total += cart[item]['subtotal']
    return render(request, 'books/homepage.template.html', {
        'books': books_cut,
        'books_nav': books_nav,
        'grand_total': grand_total,
    })


def index(request):
    genre = Genre.objects.all()
    tags = Tag.objects.all()
    books_nav = Book.objects.order_by('-release_date')[:2]
    cart = request.session.get('shopping_cart', {})
    grand_total = 0
    for item in cart:
        grand_total += cart[item]['subtotal']

    search_query = request.GET.get('search', '')

    if search_query:
        books = Book.objects.filter(
            Q(title__icontains=search_query) |
            Q(category__title__icontains=search_query) |
            Q(genre__title__icontains=search_query))
    else:
        books_all = Book.objects.all()
        books = books_all.order_by('-release_date')

    return render(request, 'books/index.template.html', {
        'genre': genre,
        'tags': tags,
        'books': books,
        'books_nav': books_nav,
        'grand_total': grand_total,
    })


@login_required
def create_book(request):
    books_nav = Book.objects.order_by('-release_date')[:2]
    cart = request.session.get('shopping_cart', {})
    grand_total = 0
    for item in cart:
        grand_total += cart[item]['subtotal']
    if request.user.is_superuser:
        if request.method == "POST":
            create_form = BookForm(request.POST, request.FILES)
            if create_form.is_valid():
                create_form.save()
                messages.success(
                    request, f"New book {create_form.cleaned_data['title']}"
                    " has been created!")
                return redirect(reverse("homepage"))
            else:
                return render(request, 'books/create_book.template.html', {
                    'form': create_form,
                    'books_nav': books_nav,
                    'grand_total': grand_total,
                })
        else:
            create_form = BookForm
            return render(request, 'books/create_book.template.html', {
                'form': create_form,
                'books_nav': books_nav,
                'grand_total': grand_total,
            })
    else:
        messages.warning(
            request, "You are not administator !"
            " Contact admin to post new products !")
        return redirect(reverse('homepage'))


def edit_book(request, book_id):
    books_nav = Book.objects.order_by('-release_date')[:2]
    cart = request.session.get('shopping_cart', {})
    grand_total = 0
    for item in cart:
        grand_total += cart[item]['subtotal']
    book_to_edit = get_object_or_404(Book, pk=book_id)
    if request.user.is_superuser:
        if request.method == "POST":
            edit_form = BookForm(request.POST, instance=book_to_edit)
            if edit_form.is_valid():
                edit_form.save()
                messages.success(
                    request, f"Book {edit_form.cleaned_data['title']}"
                    f" has been updated!")
                return redirect("book_info", book_id=book_to_edit.id)
            else:
                messages.warning(request, "Invalid update, check form!")
                return render(request, 'books/edit_book.template.html', {
                    'form': edit_form,
                    'books_nav': books_nav,
                    'grand_total': grand_total,
                })
        else:
            edit_form = BookForm(instance=book_to_edit)
            return render(request, 'books/edit_book.template.html', {
                'book': book_to_edit,
                'form': edit_form,
                'books_nav': books_nav,
                'grand_total': grand_total,
            })
    else:
        messages.warning(
            request, "You are not administator !"
            " Contact admin to edit products !")
        return redirect(reverse('homepage'))


def delete_book(request, book_id):
    book_to_delete = get_object_or_404(Book, pk=book_id)
    book_to_delete.delete()
    messages.warning(
        request, f"Book product {book_to_delete.title} has been Deleted !")
    return redirect('show_books')


def get_category(request):
    if request.method == 'GET':
        category_list = Category.objects.all()
        category = []
        for cat in category_list:
            category.append({"id": cat.id, "title": cat.title,
                             "publisher": cat.publisher})
    return JsonResponse(category, safe=False)


def genre_filter(request):
    if request.method == 'GET':
        genre = request.GET.get('text', None)
        genre_filter = Genre.objects.values_list(
            'id', flat=True).get(title=genre)
        data = Book.objects.filter(genre=genre_filter)
        html = render_to_string('books/filtered_data.template.html', {
            "data": data
        })
        return HttpResponse(html)


def tag_filter(request):
    if request.method == 'GET':
        tag = request.GET.get('text', None)
        tag_filter = Tag.objects.values_list(
            'id', flat=True).get(title=tag)
        data = Book.objects.filter(tags=tag_filter)
        html = render_to_string('books/filtered_data.template.html', {
            "data": data
        })
        return HttpResponse(html)


def book_info(request, book_id):
    books = Book.objects.all()
    books_nav = books.order_by('-release_date')[:2]
    cart = request.session.get('shopping_cart', {})
    grand_total = 0
    for item in cart:
        grand_total += cart[item]['subtotal']

    book_selected = get_object_or_404(Book, pk=book_id)
    book_form = BookForm(instance=book_selected)
    review_form = ReviewForm(request.POST)
    reviews = Review.objects.filter(book=book_id)

    if request.method == "POST":
        if request.user.is_authenticated:
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.user = request.user
                review.book = book_selected
                review.save()
                messages.success(
                    request,
                    f"Review has been posted on {book_selected.title}")
                return redirect('book_info', book_id=book_id)
        else:
            messages.warning(request, "Kindly log in to post reviews !")
            return redirect('account_login')

    return render(request, 'books/book_info.template.html', {
        "books_nav": books_nav,
        "form": book_form,
        "book": book_selected,
        "reviews": reviews,
        "review_form": review_form,
        "grand_total": grand_total,
    })
