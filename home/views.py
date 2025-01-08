from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.html import format_html
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
import re
import random
import time
from dashboard.models import Product, ProductImages, Flavour, Category,Size,Review_prdct
from .models import HeroBanner
from django.db.models import Max
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse
from .models import Review, HelpfulVote
from .forms import ReviewForm
from dashboard.forms import ReviewForm
from dashboard.models import Review_prdct,ReviewHelpful



@never_cache
def HomePage(request):
    flavours = Flavour.objects.all()
    categories = Category.objects.all()
    hero_banners = HeroBanner.objects.filter(is_active=True)

    context = {
        'hero_banners':hero_banners,
        'flavours': flavours,
        'categories': categories,
    }

    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('dashboard')
        

    return render(request, 'user_side/home_page/home.html', context)


@never_cache
def SignupPage(request):
    context = {}
    if request.method == 'POST':
        uname = request.POST.get('username')
        email = request.POST.get('email')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')

        # Validate form fields
        if not all([uname, email, pass1, pass2]):
            messages.error(request, "All fields are required.")
        elif pass1 != pass2:
            messages.error(request, "Entered passwords do not match!")
        elif not validate_password(pass1):
    
            messages.error(request, "Password must be 6-10 characters long, include uppercase and lowercase letters, numbers, and special characters.")
        elif User.objects.filter(username=uname).exists():
            messages.error(request, "Username already taken.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
        else:
            my_user = User.objects.create_user(username=uname, email=email, password=pass1)
            my_user.save()

            request.session['email'] = email
            otp = generate_otp()
            request.session['otp'] = otp
            request.session['otp_time'] = time.time()

            # Send OTP to email
            send_otp_via_email(email, otp)
            messages.success(request, "Successfully created an account. Check your email for the OTP.")
            return redirect('verify_otp')

    return render(request, 'user_side/sign_up/signup.html', context)


def validate_password(password):
    """Validates the password with custom criteria."""
    if len(password) < 6 or len(password) > 10:
        return False
    return (
        re.search("[a-z]", password) and
        re.search("[A-Z]", password) and
        re.search("[0-9]", password) and
        re.search("[!@#$%^&*(),.?\":{}|<>]", password)
    )

@never_cache
@login_required(login_url='login')
def contact(request):
    return render(request,'user_side/contact/contact.html')

@never_cache
@login_required(login_url='login')
def about(request):
    return render(request,'user_side/about/about.html')

@never_cache
@login_required(login_url='login')
def shoplist(request, flavor_id=None, category_id=None, size_id=None):
    query = request.GET.get('q')
    sort_option = request.GET.get('sort', 'latest')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    flavours = Flavour.objects.all()
    categories = Category.objects.all()
    sizes = Size.objects.all()

    # Fetch the products
    products = Product.objects.filter(
        category__is_active=True,
        flavour__is_active=True,
        is_active=True
    )

    if flavor_id:
        products = products.filter(flavour__id=flavor_id)
    if category_id:
        products = products.filter(category__id=category_id)
    if size_id:
        products = products.filter(sizes__id=size_id)

    if query:
        products = products.prefetch_related('variants').filter(
            Q(title__icontains=query) | 
            Q(category__name__icontains=query) |
            Q(flavour__name__icontains=query) |
            Q(price__icontains=query)
        )
        if not products.exists():
            messages.error(request, "No products match your search criteria.")

    if min_price or max_price:
        try:
            min_price = float(min_price) if min_price else 0
            max_price = float(max_price) if max_price else Product.objects.aggregate(Max('price'))['price__max']

            if min_price and max_price:
                products = products.filter(price__gte=min_price, price__lte=max_price)
            elif min_price:
                products = products.filter(price__gte=min_price)
            elif max_price:
                products = products.filter(price__lte=max_price)
        except (ValueError, TypeError):
            messages.error(request, "Please enter valid price values.")

    # Simplified sort mapping
    sort_mapping = {
        'name_asc': 'title',
        'name_desc': '-title',
        'price_low': 'price',
        'price_high': '-price',
        'new_arrivals': '-added_on', 
        'latest': '-created_at',
    }

    # Apply sorting
    sort_field = sort_mapping.get(sort_option, '-created_at')  
    products = products.order_by(sort_field)

    # Set up the paginator
    page = request.GET.get('page', 1)
    paginator = Paginator(products, 16)
    try:
        page_products = paginator.page(page)
    except PageNotAnInteger:
        page_products = paginator.page(1)
    except EmptyPage:
        page_products = paginator.page(paginator.num_pages)

    context = {
        'products': page_products,
        'categories': categories,
        'flavours': flavours,
        'paginator': paginator,
        'query': query,
        'sort_option': sort_option,
        'sizes': sizes,
        'selected_size_id': size_id,
        'min_price': min_price,
        'max_price': max_price,
    }

    return render(request, "user_side/shop/shop.html", context)

def size_filter(request, size_id):
    
    selected_size = get_object_or_404(Size, id=size_id)

    products = Product.objects.filter(sizes=selected_size, is_active=True)

    context = {
        'products': products,
        'selected_size': selected_size,
    }

    return render(request, 'user_side/shop/shop.html', context)  



@never_cache
@login_required(login_url='login')
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    additional_images = ProductImages.objects.filter(product=product)
    reviews = product.reviews.select_related('user').prefetch_related('reviewhelpful_set')
    user_review = None
    review_form = None
    
    
    if request.user.is_authenticated:
        user_review = product.reviews.filter(user=request.user).first()
        review_form = ReviewForm(instance=user_review)
        
    # Calculate rating stats
    rating_dist = product.rating_distribution()
    total_reviews = product.total_reviews()
    
    # Get helpful reviews first
    top_reviews = reviews.order_by('-helpful_votes', '-created_at')

    context = {
        'product': product,
        'aditional_img': additional_images,
        'reviews': top_reviews,
        'user_review': user_review,
        'review_form': review_form,
        'rating_distribution': rating_dist,
        'total_reviews': total_reviews,
        'average_rating': product.average_rating(),
    }

    return render(request, 'user_side/shop/single_product.html', context)
@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review, created = Review_prdct.objects.update_or_create(
                product=product,
                user=request.user,
                defaults={
                    'rating': form.cleaned_data['rating'],
                    'comment': form.cleaned_data['comment'],
                    'images': form.cleaned_data.get('images')
                }
            )
            messages.success(request, 'Your review has been submitted successfully!')
            return redirect('product_detail', product_id=product_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    
    return redirect('product_detail', product_id=product_id)

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review_prdct, id=review_id, user=request.user)
    product_id = review.product.id
    review.delete()
    messages.success(request, 'Your review has been deleted successfully!')
    return redirect('product_detail', product_id=product_id)

@login_required
def helpful_review(request, review_id):
    review = get_object_or_404(Review_prdct, id=review_id)
    
    if request.user == review.user:
        messages.error(request, "You cannot mark your own review as helpful.")
        return redirect('product_detail', product_id=review.product.id)
        
    vote, created = ReviewHelpful.objects.get_or_create(
        review=review,
        user=request.user
    )
    
    if created:
        review.helpful_votes += 1
        review.save()
        messages.success(request, "Thank you for your feedback!")
    else:
        vote.delete()
        review.helpful_votes -= 1
        review.save()
        messages.info(request, "You have removed your helpful vote.")
        
    return redirect('product_detail', product_id=review.product.id)


@never_cache
def LogingPage(request):
    if request.user.is_authenticated:
        return redirect('dashboard' if request.user.is_superuser else 'home')

    context = {}
    if request.method == 'POST':
        getName = request.POST.get('username')
        getPass = request.POST.get('pass')

        if request.POST.get('demo_login'):
            getName, getPass = 'demo_user', 'demo_pass123'

        request.session['login_username'] = getName

        if not getName or not getPass:
            messages.error(request, "Username and password are required.")
        else:
            User = get_user_model()
            try:
                user = User.objects.get(username=getName)
                if not user.is_active:
                    messages.error(request, "Your account is inactive. Please contact support.")
                else:
                    user = authenticate(request, username=getName, password=getPass)
                    if user is not None:
                        login(request, user)
                        messages.success(request,format_html("Successfully logged in as {}",user.username))
                        return redirect('dashboard' if user.is_superuser else 'home')
                    else:
                        messages.error(request, "Invalid username or password.")
            except User.DoesNotExist:
                messages.error(request, "Invalid username or password.")

        context['username'] = request.session.get('login_username', '')

    return render(request, 'user_side/login_page/login.html', context)



def generate_otp():
    
    return random.randint(100000, 999999)


def send_otp_via_email(email, otp):
    subject = 'Your OTP Code'
    message = f'Your One-Time Password (OTP) is {otp}. It is valid for 1 minutes.'
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])


@never_cache
def verify_otp(request):
    email = request.session.get('email')
    if request.method == 'POST':
        if 'resend_otp' in request.POST:
            otp = generate_otp()
            print(f"Resent OTP: {otp}")
            request.session['otp'] = otp
            request.session['otp_time'] = time.time()
            send_otp_via_email(email, otp)
            messages.success(request, "New OTP has been sent to your email.")
            
            return redirect('verify_otp')

        entered_otp = request.POST.get('otp')
        stored_otp = request.session.get('otp')
        otp_time = request.session.get('otp_time')

        if stored_otp is None or otp_time is None or time.time() - otp_time > 60:
            messages.error(request, "OTP has expired. Please request a new one.")
            otp = generate_otp()
            print(f"Resent OTP: {otp}")
            request.session['otp'] = otp
            request.session['otp_time'] = time.time()
            send_otp_via_email(email, otp)
            return redirect('verify_otp')

        if entered_otp == str(stored_otp):
            messages.success(request, "OTP verified successfully! Please log in.")
           
            return redirect('login')
        else:
            messages.error(request, "Invalid OTP. Please try again.")
            return redirect('verify_otp')

    return render(request, 'user_side/otp_page/verify_otp.html', {'email': email})





def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            # Generate a password reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Create reset password link
            reset_link = request.build_absolute_uri(
                reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            
            # Send email with reset link
            subject = 'Password Reset Request'
            message = f'''
            You have requested a password reset. 
            Please click the link below to reset your password:
            
            {reset_link}
            
            If you did not request this reset, please ignore this email.
            '''
            send_mail(
                subject, 
                message, 
                settings.DEFAULT_FROM_EMAIL, 
                [email],
                fail_silently=False
            )
            
            messages.success(request, "A password reset link has been sent to your email.")
            return redirect('login')
        
        except User.DoesNotExist:
            messages.error(request, "No account found with this email address.")
    
    return render(request, 'user_side/password/forgot_password.html')

def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
        # Validate token
        if default_token_generator.check_token(user, token):
            if request.method == 'POST':
                new_password = request.POST.get('new_password')
                confirm_password = request.POST.get('confirm_password')
                
                # Validate password
                if new_password != confirm_password:
                    messages.error(request, "Passwords do not match.")
                elif not validate_password(new_password):
                    messages.error(request, "Password must be 6-10 characters long, include uppercase and lowercase letters, numbers, and special characters.")
                else:
                    user.set_password(new_password)
                    user.save()
                    messages.success(request, "Password reset successfully. Please log in.")
                    return redirect('login')
            
            return render(request, 'user_side/password/password_reset_confirm.html')
        else:
            messages.error(request, "Invalid or expired reset link.")
            return redirect('login')
    
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, "Invalid reset link.")
        return redirect('login')
    
@login_required
def review_list(request):
    reviews = Review.objects.all()
    return render(request, 'user_side/reviews/review_list.html', {'reviews': reviews})

@login_required
def create_review(request):
    if Review.objects.filter(user=request.user).exists():
        messages.warning(request, 'You have already posted a review.')
        return redirect('review_list')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.save()
            messages.success(request, 'Your review has been posted!')
            return redirect('review_list')
    else:
        form = ReviewForm()

    return render(request, 'user_side/reviews/create_review.html', {'form': form})


@login_required
def vote_helpful(request, review_id):
 
    review = get_object_or_404(Review, id=review_id)

    
    if HelpfulVote.objects.filter(user=request.user, review=review).exists():
        messages.error(request, "You have already marked this review as helpful.")
    else:
       
        review.helpful_votes += 1  
        review.save()

        HelpfulVote.objects.create(user=request.user, review=review)
        messages.success(request, "Thanks for your feedback!")

    return redirect('review_list')

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)

    if review.user == request.user:
        review.delete()
        messages.success(request, "Review deleted successfully!")
    else:
        messages.error(request, "You are not authorized to delete this review.")

    return redirect('review_list')

@never_cache
def LogoutPage(request):
    logout(request)
    request.session.flush()
    messages.success(request, "Successfully logged out")
    return redirect('home')


