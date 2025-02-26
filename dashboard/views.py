from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .models import Product,Category,Flavour,ProductImages,Size,Variant
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.cache import never_cache
from django.contrib import messages
from cart_app.models import Coupon
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import re 
from django.utils.html import format_html
from django.utils.dateparse import parse_datetime
from decimal import Decimal
from django.db.models import Sum, F, Count
from django.utils.timezone import now, timedelta
from django.http import JsonResponse
from order_app.models import Order, OrderItem 
from datetime import datetime, timedelta
import json
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.db.models.functions import TruncDay, TruncMonth
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from dashboard.models import Category, Product, Flavour, ProductImages, Variant
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404



def is_superuser(user):
    return user.is_authenticated and user.is_superuser


#-------------------- dashboard-------------------
@never_cache
@user_passes_test(is_superuser, login_url='home:login')
def dashboard(request):
    try:        
            report_type = request.GET.get('report_type', 'daily')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')

            orders = Order.objects.all()
            today = timezone.now().date()

            grouped_sales = []

            if report_type == 'custom' and start_date and end_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date() + timedelta(days=1)
                orders = orders.filter(created_at__range=[start_date, end_date])
                grouped_sales = orders.annotate(period=TruncDay('created_at')).values('period').annotate(
                    total_sales=Sum('total_amount')
                ).order_by('period')

            elif report_type == 'daily':
                orders = orders.filter(created_at__date=today)
                grouped_sales = orders.annotate(period=TruncDay('created_at')).values('period').annotate(
                    total_sales=Sum('total_amount')
                ).order_by('period')

            elif report_type == 'weekly':
                week_ago = today - timedelta(days=7)
                orders = orders.filter(created_at__date__gte=week_ago)
                grouped_sales = orders.annotate(period=TruncDay('created_at')).values('period').annotate(
                    total_sales=Sum('total_amount')
                ).order_by('period')

            elif report_type == 'monthly':
                month_ago = today - timedelta(days=30)
                orders = orders.filter(created_at__date__gte=month_ago)
                grouped_sales = orders.annotate(period=TruncDay('created_at')).values('period').annotate(
                    total_sales=Sum('total_amount')
                ).order_by('period')

            elif report_type == 'yearly':
                year_ago = today - timedelta(days=365)
                orders = orders.filter(created_at__date__gte=year_ago)
                grouped_sales = orders.annotate(period=TruncMonth('created_at')).values('period').annotate(
                    total_sales=Sum('total_amount')
                ).order_by('period')
            


            summary = Order.objects.aggregate(
            total_sales=Sum('total_amount'),
            total_discounts=Sum('user_cart__coupon__discount'),  
            total_taxes=Sum('user_cart__tax')  
        )


            total_sales = summary['total_sales'] or 0
            total_discounts = summary.get('total_discounts', 0) or 0
            total_taxes = summary.get('total_taxes', 0) or 0

            net_revenue = total_sales - total_discounts + total_taxes
            total_orders = orders.count()
            average_sales = total_sales / total_orders if total_orders > 0 else 0
            grouped_sales = [
                {"period": sale['period'].strftime('%Y-%m-%d'), "total_sales": str(sale['total_sales'])}
                for sale in grouped_sales
            ]

            export_type = request.GET.get('export')

            if export_type == 'pdf':
                response = HttpResponse(content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'

                doc = SimpleDocTemplate(response, pagesize=letter)
                data = [
                    ['Order ID', 'Date', 'Time', 'Customer', 'Items', 'Subtotal','Discount', 'Total'],
                ]

                for order in orders:
                    items_count = order.items.count()
                    data.append([
                        f'#{order.id}',
                        order.created_at.strftime('%Y-%m-%d'),
                        order.created_at.strftime('%H:%M'),
                        order.user.username,
                        
                        items_count,
                        f'₹{order.subtotal}',
                        
                        f'₹{order.discount}',
                        f'₹{order.total_amount}',
                    ])

                table = Table(data)
                table_style = TableStyle([
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ])

                table.setStyle(table_style)
                doc.build([table])

                return response

            best_seller_product, top_category, top_flavour = get_top_selling_products()

            context = {
                'orders': orders,
                'report_type': report_type,
                'start_date': start_date if report_type == 'custom' else '',
                'end_date': end_date if report_type == 'custom' else '',
                'total_sales': total_sales,
            'net_revenue': net_revenue,
            'total_orders': total_orders,
            'average_sales': average_sales,
            
                'total_orders': total_orders,
                'best_seller_product': best_seller_product,
                'top_category': top_category,
                'top_flavour': top_flavour,
                'grouped_sales': json.dumps(grouped_sales, default=str),
            }
            return render(request, 'admin/home/admin_dashboard.html', context)
        
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)       




#--------------------userManagement-------------------
@never_cache
@user_passes_test(is_superuser, login_url='home:login')
def userManagement(request):
    try:        
            user = User.objects.exclude(is_superuser=True).order_by('id')
            context = {'users': user}
            return render(request, 'admin/users/user_manager.html', context)
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)


#--------------------block_user-------------------
@user_passes_test(lambda u: u.is_superuser)  
def block_user(request, user_id):
    try:        
            user = get_object_or_404(User, id=user_id)
            if user.is_superuser:
                messages.error(request, "Cannot block a superuser!")
            else:
                user.is_active = False  
                user.save()
            return redirect('user_management')
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)



#--------------------unblock_user-------------------
@user_passes_test(lambda u: u.is_superuser)  
def unblock_user(request, user_id):
    try:        
            user = get_object_or_404(User, id=user_id)
            user.is_active = True  
            user.save()
            return redirect('user_management')
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)




def delete_variant(request, variant_id):
    try:        
            variant = get_object_or_404(Variant, id=variant_id)
            product_id = variant.product.id
            variant.delete()
            return redirect('manage_variants', product_id=product_id)
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

#-------------------- product_list-------------------
@never_cache
@user_passes_test(is_superuser, login_url='home:login')
def product_list(request):
    try:       
            query = request.GET.get('search', '')
        
            products = Product.objects.prefetch_related('variants').filter(
                Q(title__icontains=query) |
                Q(category__name__icontains=query) |
                Q(flavour__name__icontains=query)
            ).order_by('-id')


            paginator = Paginator(products, 10)  
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            
            context = {
                'page_obj': page_obj,     
                'search_query': query,     
            }
            return render(request, 'admin/product_management/product_list.html', context)
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

#--------------------add_products-------------------
@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url='home:login')
def add_products(request):
    try:        
            title = stock = description = price = None
            category_id = flavour_id = None
            selected_sizes = []
            
            if request.method == 'POST':
                
                title = request.POST.get('product_name')
                description = request.POST.get('description')
                image = request.FILES.get('main_product_image')
                category_id = request.POST.get('category')
                flavour_id = request.POST.get('flavour')
                selected_sizes = request.POST.getlist('sizes')
                
                has_errors = False

                if not title:
                    messages.error(request, "Product name is required.")
                    has_errors = True
                elif re.search("[0-9]", title):
                    messages.error(request, "Product name should not contain numbers.")
                    has_errors = True
                elif re.search("[!@#$%^&*(),.?\":{}|<>]", title):
                    messages.error(request, "Product name should not contain special characters.")
                    has_errors = True



                if not description:
                    messages.error(request, "Description is required.")
                    has_errors = True

            
                try:
                    category = Category.objects.get(id=category_id)
                except (Category.DoesNotExist, ValueError):
                    messages.error(request, "Invalid category selected.")
                    has_errors = True

                try:
                    flavour = Flavour.objects.get(id=flavour_id)
                except (Flavour.DoesNotExist, ValueError):
                    messages.error(request, "Invalid flavour selected.")
                    has_errors = True

                if not image:
                    messages.error(request, "Product image is required.")
                    has_errors = True

                additional_images = []
                for i in range(3):
                    image_key = f'additional_product_image_{i}'
                    if image_key in request.FILES:
                        additional_images.append(request.FILES[image_key])
                
                if len(additional_images) < 3:
                    messages.warning(request, f"You can upload up to 3 additional images. Currently, only {len(additional_images)} images are uploaded.")
                    has_errors = True

                if not has_errors and Product.objects.filter(
                    title=title, 
                    category=category, 
                    flavour=flavour
                ).exists():
                    messages.error(request, "A product with this name, category, and flavour already exists.")
                    has_errors = True

                ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png']

                def is_valid_image(file):
                    return any(file.name.endswith(ext) for ext in ALLOWED_IMAGE_EXTENSIONS)

                if not is_valid_image(image):
                    messages.error(request, "Invalid image file format. Please upload a .jpg, .jpeg, or .png file.")
                    has_errors = True

                if not has_errors:
                    try:
                        product = Product.objects.create(
                            title=title,
                            description=description,
                            image=image,
                            category=category,
                            flavour=flavour,
                        )

                        if selected_sizes:
                            product.sizes.set(selected_sizes)
                            
                        for additional_image in additional_images:
                            ProductImages.objects.create(
                                product=product,
                                image=additional_image
                            )

                    
                        weights = request.POST.getlist('varient_weight[]')
                        prices = request.POST.getlist('varient_price[]')
                        stocks = request.POST.getlist('varient_stock[]')

                        for weight, price, stock in zip(weights, prices, stocks):
                                if weight and price and stock:
                                    try:
                                        stock = int(stock)
                                        if stock < 0:
                                            messages.error(request, "Stock value cannot be negative.")
                                            has_errors = True
                                            

                                        Variant.objects.create(
                                            product=product,
                                            weight=weight,
                                            price=float(price),
                                            stock=stock
                                        )
                                    except ValueError:
                                        messages.error(request, "Invalid stock value. Please enter a valid number.")
                                    except Exception as e:
                                        messages.error(request, f"Error saving variant: {str(e)}")


                        messages.success(request, "Product added successfully!")
                        return redirect('product_list')

                    except Exception as e:
                        messages.error(request, f"Error saving product: {str(e)}")
                        return redirect('add_products')

                
                for stock in request.POST.getlist('varient_stock[]'):
                    try:
                        stock = int(stock)
                        if stock < 0:
                            messages.error(request, "Stock value cannot be negative.")
                            has_errors = True
                            break  
                    except ValueError:
                        messages.error(request, "Invalid stock value. Please enter a valid number.")
                        has_errors = True
                        break

                if has_errors:
                    return redirect('add_products') 

            
            context = {
                'categories': Category.objects.filter(is_active=True),
                'flavours': Flavour.objects.filter(is_active=True),
                
                'title': title,
                'description': description,
                'category_id': category_id,
                'flavour_id': flavour_id,
            }
            return render(request, 'admin/product_management/add_product.html', context)
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

def validate_product_name(title):
    if not title:
        return "Product name is required."
    if re.search("[0-9]", title):
        return "Product name should not contain numbers."
    if re.search("[!@#$%^&*(),.?\":{}|<>]", title):
        return "Product name should not contain special characters."
    return None


#-------------------- edit_product------------------
@never_cache
def edit_product(request, product_id):
    try:        
            product = get_object_or_404(Product, id=product_id)
            product_images = ProductImages.objects.filter(product=product)
            variants = Variant.objects.filter(product=product)

            if request.method == 'POST':
                title = request.POST.get('product_name', '').strip()
                description = request.POST.get('description', '').strip()
                category_id = request.POST.get('category')
                flavour_id = request.POST.get('flavour')

                errors = []

                product_name_error = validate_product_name(title)
                if product_name_error:
                    errors.append(product_name_error)

                if not description:
                    errors.append("Description is required.")

                category = Category.objects.filter(id=category_id).first()
                flavour = Flavour.objects.filter(id=flavour_id).first()

                if not category:
                    errors.append("This category is currently unavailable.")
                if not flavour:
                    errors.append("This flavour is currently unavailable.")

                if errors:
                    for error in errors:
                        messages.error(request, error)
                    return redirect('edit_product', product_id=product.id)

                for i, img in enumerate(product_images, start=1):
                    if request.POST.get(f'remove_image_{i}') == 'on':  
                        img.delete()
                    elif f'extra_image_{i}' in request.FILES:
                        img.image = request.FILES[f'extra_image_{i}']
                        img.save()

                for image in request.FILES.getlist('new_images'):
                    ProductImages.objects.create(product=product, image=image)

                for variant in variants:
                    delete_variant = request.POST.get(f'delete_variant_{variant.id}')
                    if delete_variant:
                        variant.delete()
                        continue

                    weight = request.POST.get(f'variant_weight_{variant.id}')
                    price = request.POST.get(f'variant_price_{variant.id}')
                    stock = request.POST.get(f'variant_stock_{variant.id}')

                    if weight and price and stock:
                        variant.weight = weight
                        variant.price = float(price)
                        variant.stock = int(stock)
                        variant.save()

                new_weights = request.POST.getlist('new_variant_weight[]')
                new_prices = request.POST.getlist('new_variant_price[]')
                new_stocks = request.POST.getlist('new_variant_stock[]')

                for weight, price, stock in zip(new_weights, new_prices, new_stocks):
                    if weight or price or stock:  
                        if weight and price and stock:  
                            Variant.objects.create(product=product, weight=weight, price=float(price), stock=int(stock))
                        else:
                            messages.error(request, "All fields are required for a new variant.")
                            return redirect('edit_product', product_id=product.id)


                product.title = title
                product.description = description
                product.category = category
                product.flavour = flavour

                if 'main_image' in request.FILES:
                    product.image = request.FILES['main_image']

                product.save()

                messages.success(request, "Product updated successfully!")
                return redirect('product_list')

            categories = Category.objects.all()
            flavours = Flavour.objects.all()
            context = {
                'product': product,
                'product_images': product_images,
                'categories': categories,
                'flavours': flavours,
                'variants': variants,
                'errors': [msg for msg in messages.get_messages(request)],
            }
            return render(request, 'admin/product_management/edit_product.html', context)
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)



#-------------------- delete_product-------------------
@user_passes_test(is_superuser, login_url='home:login')
def delete_product(request, product_id):
    try:        
            product = get_object_or_404(Product, id=product_id)
            product.is_active = False
            product.save()
            messages.error(request, "product blocked succesfully")
        
            return redirect('product_list')
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500) 


#-------------------- unblock_product-------------------
@user_passes_test(is_superuser, login_url='home:login')
def unblock_product(request, product_id):
    try:        
            product = get_object_or_404(Product, id=product_id)
            product.is_active = True
            product.save()
            messages.success(request, "product unblocked succesfully")

            

            return redirect('product_list')
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

#-------------------- category_list-------------------
@never_cache
@user_passes_test(is_superuser, login_url='home:login')
def category_list(request):
    try:        
            search_query = request.GET.get('search', '')
            
            if search_query:
                categories = Category.objects.filter(
                    Q(name__icontains=search_query) |
                    Q(description__icontains=search_query)
                ).order_by('name')
                paginator = Paginator(categories, items_per_page)

            else:
                categories = Category.objects.all().order_by('name')
            
            page = request.GET.get('page', 1)
            items_per_page = 10  
            paginator = Paginator(categories, items_per_page)
            
            try:
                page_obj = paginator.page(page)
            except PageNotAnInteger:

                page_obj = paginator.page(1)
            except EmptyPage:
            
                page_obj = paginator.page(paginator.num_pages)
            
            
            if search_query and not categories.exists():
                messages.info(request, f"No categories found matching '{search_query}'")
            
            context = {
                'categories': categories,
                'page_obj': page_obj,
                'search_query': search_query,
                'total_categories': categories.count(),
            }
            
            return render(request, 'admin/product_management/category_list.html', context)
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

@never_cache
@staff_member_required(login_url='home:login')
def add_category(request):
    try:
            if request.method == 'POST':
                name = request.POST.get('category_name', '').strip()
                description = request.POST.get('description', '').strip()
                
                errors = []
                
                if not name:
                    errors.append("Category name is required.")
                
                if Category.objects.filter(name__iexact=name).exists():
                    errors.append("This category already exists.")
                
                if name:
                    if len(name) < 3:
                        errors.append("Category name must be at least 3 characters long.")
                    
                    if re.search(r'\d', name):
                        errors.append("Category name should not contain numbers.")
                    
                    if re.search(r'[!@#$%^&*(),.?":{}|<>]', name):
                        errors.append("Category name should not contain special characters.")
                
                if errors:
                    for error in errors:
                        messages.error(request, error)
                    return render(request, 'admin/product_management/add_category.html')
                
                try:
                    Category.objects.create(
                        name=name,
                        description=description,
                    )
                    messages.success(request, "Category added successfully!")
                    return redirect('category_list')
                except Exception as e:
                    messages.error(request, f"Error creating category: {str(e)}")
            
            return render(request, 'admin/product_management/add_category.html')
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)
@never_cache
@staff_member_required(login_url='home:login')
def edit_category(request, id):
    try:
            category = get_object_or_404(Category, id=id)

            if request.method == 'POST':
                name = request.POST.get('category_name', '').strip()
                description = request.POST.get('description', '').strip()
                
                errors = []
                
                if not name:
                    errors.append("Category name is required.")
                
                if name:
                    if len(name) < 3:
                        errors.append("Category name must be at least 3 characters long.")
                    
                    if re.search(r'\d', name):
                        errors.append("Category name should not contain numbers.")
                    
                    if re.search(r'[!@#$%^&*(),.?":{}|<>]', name):
                        errors.append("Category name should not contain special characters.")
                
                if Category.objects.filter(name__iexact=name).exclude(id=id).exists():
                    errors.append("A category with this name already exists.")
                
                if errors:
                    for error in errors:
                        messages.error(request, error)
                    return render(request, 'admin/product_management/edit_category.html', {'category': category})
                
                try:
                    category.name = name
                    category.description = description
                    category.save()
                    messages.success(request, "Category updated successfully!")
                    return redirect('category_list')
                except Exception as e:
                    messages.error(request, f"Error updating category: {str(e)}")
            
            return render(request, 'admin/product_management/edit_category.html', {'category': category})
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)
    

@user_passes_test(is_superuser, login_url='home:login')
def delete_category(request, id):
    try:        
            category = get_object_or_404(Category, id=id)
            category.is_active = False
            category.save()
            messages.error(request,format_html(f"Category '{category.name}' has been blocked successfully."))
            return redirect('category_list')
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

@user_passes_test(is_superuser, login_url='home:login')
def unblock_category(request, id):
    try:        
            category = get_object_or_404(Category, id=id)
            category.is_active = True
            category.save()
            messages.success(request, format_html(f"Category '{category.name}' has been unblocked successfully."))
            return redirect('category_list')
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

#-------------------- flavour_list-------------------
@never_cache
@user_passes_test(is_superuser, login_url='home:login')
def flavour_list(request):
    try:
            flavour = Flavour.objects.all()
            context = {
                'flavours': flavour
            }
            return render(request,'admin/product_management/flavour_list.html', context)
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)



#-------------------- add_flavour-------------------
@never_cache
@user_passes_test(is_superuser, login_url='home:login')
def add_flavour(request):
    try:        
            if request.method == 'POST':
                name = request.POST.get('flavour_name', '').strip()
                description = request.POST.get('description', '').strip()

                errors = []

                if not name:
                    errors.append("Flavour name is required.")
                
                if Flavour.objects.filter(name__iexact=name).exists():
                    errors.append("This flavour already exists.")
                
                if name:
                    if len(name) < 3:
                        errors.append("Flavour name must be at least 3 characters long.")
                    
                    if re.search(r'\d', name):
                        errors.append("Flavour name should not contain numbers.")
                    
                    if re.search(r'[!@#$%^&*(),.?":{}|<>]', name):
                        errors.append("Flavour name should not contain special characters.")
                
                if errors:
                    for error in errors:
                        messages.error(request, error)
                    return render(request, 'admin/product_management/add_flavour.html')
                
                try:
                    Flavour.objects.create(
                        name=name,
                        description=description,
                    )
                    messages.success(request, "Flavour added successfully!")
                    return redirect('flavour_list')
                except Exception as e:
                    messages.error(request, f"Error creating flavour: {str(e)}")

            return render(request, 'admin/product_management/add_flavour.html')
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)


#-------------------- edit_flavour-------------------
@never_cache
@user_passes_test(is_superuser, login_url='home:login')
def edit_flavour(request, id):
    try:        
            flavour = get_object_or_404(Flavour, id=id)

            if request.method == 'POST':
                name = request.POST.get('flavour_name', '').strip()
                description = request.POST.get('description', '').strip()
                category_id = request.POST.get('category')
                flavour_id = request.POST.get('flavour')

                errors = []

                if not name:
                    errors.append("Flavour name is required.")
                
                if name:
                    if len(name) < 3:
                        errors.append("Flavour name must be at least 3 characters long.")
                    
                    if re.search(r'\d', name):
                        errors.append("Flavour name should not contain numbers.")
                    
                    if re.search(r'[!@#$%^&*(),.?":{}|<>]', name):
                        errors.append("Flavour name should not contain special characters.")
                
                if errors:
                    for error in errors:
                        messages.error(request, error)
                    return render(request, 'admin/product_management/edit_flavour.html', {'flavour': flavour, 'id': id})

                try:
                    if category_id:
                        flavour.category = get_object_or_404(Category, id=category_id)
                    if flavour_id:
                        flavour.flavour = get_object_or_404(Flavour, id=flavour_id)

                    flavour.name = name
                    flavour.description = description
                    flavour.save()

                    messages.success(request, "Flavour updated successfully!")
                    return redirect('flavour_list')

                except ValueError:
                    messages.error(request, "Invalid flavour or category selected.")
                    return redirect('edit_flavour', id=id)  

            return render(request, 'admin/product_management/edit_flavour.html', {'flavour': flavour, 'id': id})
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

@user_passes_test(is_superuser, login_url='home:login')
def delete_flavour(request, id):
    try:        
            flavour = get_object_or_404(Flavour, id=id)
            flavour.is_active = False 
            flavour.save()
            return redirect('flavour_list')
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

@user_passes_test(is_superuser, login_url='home:login')
def unblock_flavour(request, id):
    try:    
        flavour = get_object_or_404(Flavour, id=id)
        flavour.is_active = True  
        flavour.save()
        return redirect('flavour_list')
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

@never_cache
@user_passes_test(is_superuser, login_url='home:login')
def coupon_list(request):
    try:        
            coupons = Coupon.objects.all()
            return render(request, 'admin/coupon_management/coupon_list.html', {'coupons': coupons})
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

from decimal import Decimal, InvalidOperation
from django.utils.dateparse import parse_datetime
from django.shortcuts import render, redirect
@never_cache
@user_passes_test(is_superuser, login_url='home:login')
def coupon_add(request):
    try:
            if request.method == 'POST':
                code = request.POST.get('code')
                discount = request.POST.get('discount')
                valid_from = request.POST.get('valid_from')
                valid_to = request.POST.get('valid_to')
                active = request.POST.get('active') == 'on'

                try:
                    discount = Decimal(discount)
                except InvalidOperation:
                    return render(request, 'admin/coupon_management/add_coupon.html', {
                        'error_message': "Invalid discount value. Please enter a valid number.",
                        'form_data': request.POST,
                    })
                
                try:
                    valid_from = parse_datetime(valid_from)
                    valid_to = parse_datetime(valid_to)

                    if not valid_from or not valid_to or valid_from >= valid_to:
                        raise ValueError("Invalid date range. 'Valid From' must be earlier than 'Valid To'.")
                except Exception as e:
                    return render(request, 'admin/coupon_management/add_coupon.html', {
                        'error_message': str(e),
                        'form_data': request.POST,
                    })

                Coupon.objects.create(
                    code=code,
                    discount=discount,
                    valid_from=valid_from,
                    valid_to=valid_to,
                    active=active
                )
                return redirect('coupon_list')

            return render(request, 'admin/coupon_management/add_coupon.html')
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)



@never_cache
@user_passes_test(is_superuser, login_url='home:login')
def coupon_edit(request, pk):
    try:        
            coupon = get_object_or_404(Coupon, pk=pk)
            if request.method == 'POST':
                coupon.code = request.POST.get('code')
                coupon.discount = Decimal(request.POST.get('discount'))
                coupon.valid_from = parse_datetime(request.POST.get('valid_from'))
                coupon.valid_to = parse_datetime(request.POST.get('valid_to'))
                coupon.active = request.POST.get('active') == 'on'

                coupon.save()
                return redirect('coupon_list')
            
            return render(request, 'admin/coupon_management/add_coupon.html', {'coupon': coupon})
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)


def coupon_delete(request, pk):
    try:       
            coupon = get_object_or_404(Coupon, pk=pk)
            if request.method == 'POST':
                coupon.delete()
                return redirect('coupon_list')
            
            return render(request, 'admin/coupon_management/delete_coupon.html', {'coupon': coupon})
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)





def get_top_selling_products():
            
            top_products = (
                Product.objects
                .annotate(sold_count=Sum('orderitem__quantity'))  
                .filter(sold_count__gt=0) 
                .order_by('-sold_count')[:5]  
            )

            
            top_category = (
                Category.objects
                .annotate(total_sold=Sum('products__orderitem__quantity')) 
                .filter(total_sold__gt=0)  
                .order_by('-total_sold')[:2]  
            )

            
            top_flavour = (
                Product.objects
                .values('flavour__name')  
                .annotate(total_sold=Sum('orderitem__quantity'))  
                .filter(total_sold__gt=0)  
                .order_by('-total_sold')[:2]  
            )

            return top_products, top_category, top_flavour

def sales_report(request):
    try:        
            filter_type = request.GET.get('filter', 'daily') 
            start_date = request.GET.get('start_date')  
            end_date = request.GET.get('end_date')      

            orders = Order.objects.filter(order_status='DELIVERED')

            if filter_type == 'daily':
                orders = orders.filter(created_at__date=now().date())
            elif filter_type == 'weekly':
                start_of_week = now().date() - timedelta(days=now().weekday())  
                orders = orders.filter(created_at__date__gte=start_of_week)
            elif filter_type == 'yearly':
                orders = orders.filter(created_at__year=now().year)
            elif filter_type == 'custom' and start_date and end_date:
                orders = orders.filter(created_at__date__range=[start_date, end_date])

            sales_data = orders.annotate(
                calculated_total_amount=Sum(F('orderitem__quantity') * F('orderitem__price')),
                total_quantity=Sum('orderitem__quantity')
            
            ).values('id', 'calculated_total_amount', 'total_quantity', 'created_at')


            return render(request, 'admin/reports/sales_report.html', {
                'sales_data': sales_data,
                'filter_type': filter_type,
                'start_date': start_date,
                'end_date': end_date,
            })
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)
@never_cache
@user_passes_test(is_superuser, login_url='home:login')
def admin_product_detail(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        variants = product.variants.all()
        additional_images = product.images.all()
        # reviews = product.reviews.all().order_by('-created_at')
        
        # Get rating statistics
        # avg_rating = product.average_rating()
        # total_reviews = product.total_reviews()
        # rating_dist = product.rating_distribution()
        
        context = {
            'product': product,
            'variants': variants,
            'additional_images': additional_images,
            # 'reviews': reviews,
            # 'avg_rating': avg_rating,
            # 'total_reviews': total_reviews,
            # 'rating_distribution': rating_dist,
            'categories': Category.objects.filter(is_active=True),
            'flavours': Flavour.objects.filter(is_active=True),
        }
        
        return render(request, 'admin/product_management/product_detail.html', context)
    
    except Exception as e:
        messages.error(request, f"Error loading product: {str(e)}")
        return redirect('admin_product_list')
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)
    except Exception as e:
        return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url='home:login')
def toggle_product_status(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        product.is_active = not product.is_active
        product.save()
        messages.success(request, f"Product {product.title} has been {'activated' if product.is_active else 'deactivated'}")
        return redirect('admin_product_detail', product_id=product_id)
    except Exception as e:
        messages.error(request, f"Error updating product status: {str(e)}")
        return redirect('admin_product_detail', product_id=product_id)
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)
    except Exception as e:
        return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)