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
from dashboard.models import Product, ProductImages, Flavour, Category,Size,Review_prdct,Variant
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
from order_app.models import Order, OrderItem,Invoice
import tempfile
import os
from datetime import datetime
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Q, Min, Max
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib import messages
from django.utils.html import format_html
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import get_backends


@never_cache
def HomePage(request):
    flavours = Flavour.objects.all()
    categories = Category.objects.all()
    hero_banners = HeroBanner.objects.filter(is_active=True)
    demo_user = request.user.username == "demo_user"


    context = {
         "demo_user": demo_user,
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
    if request.method == 'POST':
        uname = request.POST.get('username')
        email = request.POST.get('email')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')

        if not all([uname, email, pass1, pass2]):
            messages.error(request, "All fields are required.")
        elif pass1 != pass2:
            messages.error(request, "Passwords do not match!")
        elif not validate_password(pass1):
            messages.error(request, "Password must be 6-10 characters long, include uppercase, lowercase, numbers, and special characters.")
        elif User.objects.filter(username=uname).exists():
            messages.error(request, "Username already taken.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
        else:
            request.session['signup_data'] = {
                'username': uname,
                'email': email,
                'password': pass1,
            }

            otp = generate_otp()
            send_otp_via_email(email, otp)
            request.session['otp'] = otp
            request.session['otp_time'] = time.time() + 30  
            print("otp=", otp)

            messages.success(request, "OTP sent to your email. Please verify.")
            return redirect('verify_otp')

    return render(request, 'user_side/sign_up/signup.html')
def validate_password(password):
    """Validate password strength."""
    if len(password) < 6 or len(password) > 10:
        return False
    return (
        re.search("[a-z]", password) and
        re.search("[A-Z]", password) and
        re.search("[0-9]", password) and
        re.search("[!@#$%^&*(),.?\":{}|<>]", password)
    )

@never_cache
def contact(request):
    return render(request,'user_side/contact/contact.html')

@never_cache
def about(request):
    try:        
            variant_count = Variant.objects.count()
            user_count = User.objects.count()
            
            bakery_stats = {
                'cakes': {
                    'number': str(variant_count) + '+', 
                    'label': 'Cake Varieties'
                },
                'customers': {
                    'number': str(user_count) + '+',
                    'label': 'Happy Customers'
                },
                'chefs': {
                    'number': '10+',
                    'label': 'Expert Bakers'
                },
                'experience': {
                    'number': '5+',
                    'label': 'Years Experience'
                }
            }
            
            core_values = [
                {
                    'icon': 'fas fa-heart',
                    'title': 'Made with Love',
                    'description': 'Every cake we create is crafted with passion, care, and the finest ingredients to ensure a delightful experience.'
                },
                {
                    'icon': 'fas fa-star',
                    'title': 'Premium Quality',
                    'description': 'We use only the highest quality ingredients and maintain strict quality standards in our baking process.'
                },
                {
                    'icon': 'fas fa-magic',
                    'title': 'Custom Designs',
                    'description': 'Our expert bakers can bring any cake design to life, creating personalized masterpieces for your special occasions.'
                }
            ]
            
            bakery_features = [
                {
                    'image': 'user_assets/images/custom-cakes.jpg',
                    'title': 'Custom Cakes',
                    'description': 'Personalized for Every Occasion'
                },
                {
                    'image': 'user_assets/images/fresh-baking.jpg',
                    'title': 'Fresh Baking',
                    'description': 'Made Fresh Daily'
                },
                {
                    'image': 'user_assets/images/delivery.jpg',
                    'title': 'Fast Delivery',
                    'description': 'On-time Cake Delivery'
                },
                {
                    'image': 'user_assets/images/support.jpg',
                    'title': 'Expert Support',
                    'description': 'Professional Cake Consultation'
                }
            ]
            
        
            bakery_story = {
                'title': 'Our Sweet Journey',
                'paragraphs': [
                    'Cake Chief started as a small home bakery with a passion for creating delicious, beautiful cakes. What began as a love for baking has grown into a beloved destination for cake lovers seeking exceptional quality and unique designs.',
                    'Today, we\'ve become one of the most trusted names in custom cake creation, serving thousands of happy customers and making their special moments even sweeter with our delectable creations.'
                ]
            }
            
        
            hero_content = {
                'title': 'Welcome to Cake Chief',
                'subtitle': 'Where every cake tells a story and every bite brings joy. We specialize in creating beautiful, delicious custom cakes that make your special occasions unforgettable.'
            }
            
            context = {
                'stats': bakery_stats,
                'values': core_values,
                'features': bakery_features,
                'story': bakery_story,
                'hero': hero_content,
                'meta': {
                    'title': 'About Us - Cake Chief',
                    'description': 'Discover Cake Chief, your premier destination for custom cakes, wedding cakes, and specialty desserts. Learn about our passion for baking and commitment to quality.',
                    'keywords': 'Cake Chief, custom cakes, bakery, wedding cakes, birthday cakes, specialty desserts'
                }
            }
            
            return render(request,'user_side/about/about.html',context)
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)


@never_cache
@login_required(login_url='login')
def shoplist(request, flavor_id=None, category_id=None, size_id=None):
    try:
        query = request.GET.get('q')
        sort_option = request.GET.get('sort', 'latest')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        
        flavours = Flavour.objects.filter(is_active=True)
        categories = Category.objects.filter(is_active=True)
        
        products = Product.objects.filter(
            category__is_active=True,
            flavour__is_active=True,
            is_active=True
        ).prefetch_related('variants')
        
        if flavor_id:
            products = products.filter(flavour__id=flavor_id)
            if not products.exists():
                messages.info(request, "No products found for the selected flavor.")
        
        if category_id:
            products = products.filter(category__id=category_id)
            if not products.exists():
                messages.info(request, "No products found for the selected category.")
        
        if query:
            products = products.filter(
                Q(title__icontains=query) |
                Q(category__name__icontains=query) |
                Q(flavour__name__icontains=query)
            )
            # if not products.exists():
            #     messages.info(request, f"No products found matching '{query}'.")
        
        if min_price is not None or max_price is not None:
            try:
                min_price = float(min_price) if min_price else 0
                max_price = float(max_price) if max_price else float(Variant.objects.aggregate(Max('price'))['price__max'] or 0)
                
                if min_price > max_price:
                    messages.error(request, "Minimum price cannot be greater than maximum price.")
                else:
                    products = products.filter(
                            variants__price__gte=min_price,
                            variants__price__lte=max_price
                        ).distinct()
                    
               
            
            except (ValueError, TypeError):
                messages.error(request, "Please enter valid price values.")
        
        sort_mapping = {
            'name_asc': 'title',
            'name_desc': '-title',
            'price_low': 'min_variant_price',
            'price_high': '-min_variant_price',
            'new_arrivals': '-added_on',
            'latest': '-created_at',
        }
        
        sort_field = sort_mapping.get(sort_option, '-created_at')
        
        products = products.annotate(
            min_variant_price=Min('variants__price')
        ).order_by(sort_field)
        
        if not products.exists():
            if not any([query, min_price, max_price, flavor_id, category_id]):
                messages.info(request, "No products are currently available.")
        
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
            'min_price': min_price,
            'max_price': max_price,
            'has_results': products.exists(),
        }
        
        return render(request, "user_side/shop/shop.html", context)

    except Http404:
        messages.error(request, "The page you're looking for doesn't exist.")
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)
    
    except ObjectDoesNotExist:
        messages.error(request, "The requested resource was not found.")
        return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)
    
    except Exception as e:
            
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)


@never_cache
@login_required(login_url='login')
def product_detail(request, product_id):
    try:        
            product = get_object_or_404(Product, id=product_id)
            additional_images = ProductImages.objects.filter(product=product)
            reviews = product.reviews.select_related('user').prefetch_related('reviewhelpful_set')
            user_review = None
            review_form = None
            
            
            if request.user.is_authenticated:
                user_review = product.reviews.filter(user=request.user).first()
                review_form = ReviewForm(instance=user_review)
                
            rating_dist = product.rating_distribution()
            total_reviews = product.total_reviews()
            
            top_reviews = reviews.order_by('-helpful_votes', '-created_at')
            related_products = Product.objects.filter(
                category=product.category,  
                is_active=True
            ).exclude(id=product.id)[:4]


            context = {
                'product': product,
                'aditional_img': additional_images,
                'reviews': top_reviews,
                'user_review': user_review,
                'review_form': review_form,
                'rating_distribution': rating_dist,
                'total_reviews': total_reviews,
                'average_rating': product.average_rating(),
                'related_products': related_products, 

            }

            return render(request, 'user_side/shop/single_product.html', context)
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

@login_required(login_url='login')
def add_review(request, product_id):
    try:       
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
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

@login_required(login_url='login')
def delete_review(request, review_id):
    try:        
            review = get_object_or_404(Review_prdct, id=review_id, user=request.user)
            product_id = review.product.id
            review.delete()
            messages.success(request, 'Your review has been deleted successfully!')
            return redirect('product_detail', product_id=product_id)
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

@login_required(login_url='login')
def helpful_review(request, review_id):
    try:        
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
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

from django.views.decorators.csrf import csrf_protect





def generate_otp():
    return random.randint(100000, 999999)

def send_otp_via_email(email, otp):
    subject = 'Your OTP Code'
    message = f'Your One-Time Password (OTP) is {otp}. It is valid for 30 seconds.'
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])


User = get_user_model()

@never_cache
def verify_otp(request):
    try:        
            email = request.session.get('signup_data', {}).get('email')
            signup_data = request.session.get('signup_data', {})  
            
            if not email:
                messages.error(request, "Please enter your email to proceed.")
                return redirect('SignupPage')

            if request.method == 'POST':
                entered_otp = request.POST.get('otp')
                stored_otp = request.session.get('otp')
                otp_time = request.session.get('otp_time')
                print("otp=", stored_otp)

                if not stored_otp or not otp_time or time.time() > otp_time:
                    messages.error(request, "OTP has expired. Please request a new one.")
                    return redirect('verify_otp')

                if entered_otp == str(stored_otp):
                    username = signup_data.get('username')
                    password = signup_data.get('password')
                    
                    if not username or not password:
                        messages.error(request, "Signup data is incomplete. Please try again.")
                        return redirect('SignupPage')

                    user = User.objects.create_user(username=username, email=email, password=password)
                    user.save()

                
                    backend = 'django.contrib.auth.backends.ModelBackend'
                    user.backend = backend  

                    login(request, user, backend=backend)

                    del request.session['signup_data']
                    del request.session['otp']
                    del request.session['otp_time']

                    messages.success(request, "OTP verified successfully! You are now logged in.")
                    return redirect('home') 

                else:
                    messages.error(request, "Invalid OTP. Please try again.")

            return render(request, 'user_side/otp_page/verify_otp.html', {'email': email})
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)



@never_cache
def resend_otp(request):
    try:
            signup_data = request.session.get('signup_data')
            if not signup_data:
                return redirect('SignupPage')

            email = signup_data.get('email')
            
            otp = generate_otp()
            send_otp_via_email(email, otp)
            request.session['otp'] = otp
            request.session['otp_time'] = time.time() + 30  
            print("otp=", otp)

            messages.success(request, "New OTP has been sent to your email.")
            return redirect('verify_otp')
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)



@csrf_protect
@never_cache
def LogingPage(request):
    # try:
        if request.user.is_authenticated:
            return redirect('dashboard' if request.user.is_superuser else 'home')

        context = {}


        if request.method == 'POST':
            if 'demo_login' in request.POST:
                getName = 'demo_user'
                getPass = 'demo_pass123'
            else:
                getName = request.POST.get('username')
                getPass = request.POST.get('pass')

            if not getName or not getPass:
                messages.error(request, "Username and password are required.")
                return render(request, 'user_side/login_page/login.html', context)

            user = authenticate(request, username=getName, password=getPass)

            if user is not None:
                if not user.is_active:
                    messages.error(request, "Your account is inactive. Please contact support.")
                else:
                    login(request, user)
                    messages.success(request, format_html("Successfully logged in as {}", user.username))
                    return redirect('dashboard' if user.is_superuser else 'home')
            else:
                messages.error(request, "Invalid username or password.")
                
            if 'demo_login' not in request.POST:
                request.session['login_username'] = getName
                context['username'] = getName

        return render(request, 'user_side/login_page/login.html', context)

    # except Http404:
    #     return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)
    # except ObjectDoesNotExist:
    #     return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)
    # except Exception as e:
    #     return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

@login_required(login_url='login')
def forgot_password(request):
    try:        
            if request.method == 'POST':
                email = request.POST.get('email')
                
                try:
                    user = User.objects.get(email=email)
                    
                    token = default_token_generator.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    
                    reset_link = request.build_absolute_uri(
                        reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                    )
                    
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
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)
@login_required(login_url='login')
def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
        if default_token_generator.check_token(user, token):
            if request.method == 'POST':
                new_password = request.POST.get('new_password')
                confirm_password = request.POST.get('confirm_password')
                
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
    
@login_required(login_url='login')
def review_list(request):
    try:    
        reviews = Review.objects.all()
        return render(request, 'user_side/reviews/review_list.html', {'reviews': reviews})
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

@login_required(login_url='login')
def create_review(request):
    try:        
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
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)


@login_required(login_url='login')
def vote_helpful(request, review_id):
    try:        
            review = get_object_or_404(Review, id=review_id)

            
            if HelpfulVote.objects.filter(user=request.user, review=review).exists():
                messages.error(request, "You have already marked this review as helpful.")
            else:
            
                review.helpful_votes += 1  
                review.save()

                HelpfulVote.objects.create(user=request.user, review=review)
                messages.success(request, "Thanks for your feedback!")

            return redirect('review_list')
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

@login_required(login_url='login')
def delete_review(request, review_id):
    try: 
            review = get_object_or_404(Review, id=review_id)

            if review.user == request.user:
                review.delete()
                messages.success(request, "Review deleted successfully!")
            else:
                messages.error(request, "You are not authorized to delete this review.")

            return redirect('review_list')
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

@never_cache
def LogoutPage(request):
    logout(request)
    request.session.flush()
    messages.success(request, "Successfully logged out")
    return redirect('home')



