from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .models import Product,Category,Flavour,ProductImages,Size,Variant
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.cache import never_cache
from django.contrib import messages
from PIL import Image
from io import BytesIO
import base64
# from django.core.files.base import ContentFile
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import re 
from django.utils.html import format_html


def is_superuser(user):
    return user.is_authenticated and user.is_superuser


#-------------------- dashboard-------------------
@user_passes_test(is_superuser, login_url='home:login')
def dashboard(request):
    
    return render(request, 'admin/home/admin_dashboard.html')
    




#--------------------userManagement-------------------
@user_passes_test(is_superuser, login_url='home:login')
def userManagement(request):
    user = User.objects.exclude(is_superuser=True)
    context = {'users': user}
    return render(request, 'admin/users/user_management.html', context)



#--------------------block_user-------------------
@user_passes_test(lambda u: u.is_superuser)  # Only superusers can block users
def block_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        messages.error(request, "Cannot block a superuser!")
    else:
        user.is_active = False  # Block the user
        user.save()
    return redirect('user_management')



#--------------------unblock_user-------------------
@user_passes_test(lambda u: u.is_superuser)  # Only superusers can unblock users
def unblock_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = True  # Unblock the user
    user.save()
    return redirect('user_management')




def delete_variant(request, variant_id):
    variant = get_object_or_404(Variant, id=variant_id)
    product_id = variant.product.id
    variant.delete()
    return redirect('manage_variants', product_id=product_id)

#-------------------- product_list-------------------
@user_passes_test(is_superuser, login_url='home:login')
def product_list(request):
    query = request.GET.get('search', '')
    
    # Filter products based on the search query
    products = Product.objects.prefetch_related('variants').filter(
        Q(title__icontains=query) |
        Q(category__name__icontains=query) |
        Q(flavour__name__icontains=query)
    )

    # Apply pagination on the filtered products
    paginator = Paginator(products, 10)  # 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,        # Paginated products
        'search_query': query,       # Search query for rendering in template
    }
    return render(request, 'admin/product_management/product_list.html', context)


#--------------------add_products-------------------
@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url='home:login')
def add_products(request):
    # Default values for form fields (in case of GET request or error)
    title = stock = description = price = None
    category_id = flavour_id = None
    selected_sizes = []
    
    if request.method == 'POST':
        
        title = request.POST.get('product_name')
        # stock = request.POST.get('quantity')
        description = request.POST.get('description')
        # price = request.POST.get('price')
        image = request.FILES.get('main_product_image')
        category_id = request.POST.get('category')
        flavour_id = request.POST.get('flavour')
        selected_sizes = request.POST.getlist('sizes')
        
        has_errors = False

        # Validate title
        if not title:
            messages.error(request, "Product name is required.")
            has_errors = True
        elif re.search("[0-9]", title):
            messages.error(request, "Product name should not contain numbers.")
            has_errors = True
        elif re.search("[!@#$%^&*(),.?\":{}|<>]", title):
            messages.error(request, "Product name should not contain special characters.")
            has_errors = True

        # Validate stock
        # stocks = request.POST.get('quantity')  # Updated variable name
        # if not stocks or not stocks.isdigit() or int(stocks) <= 0:
        #     messages.error(request, "Quantity should be a positive integer.")
        #     has_errors = True

        # Validate description
        if not description:
            messages.error(request, "Description is required.")
            has_errors = True

        # Validate price
        # prices = request.POST.get('price')  # Updated variable name
        # try:
        #     prices = float(prices)
        #     if prices <= 0:
        #         messages.error(request, "Price should be a positive number.")
        #         has_errors = True
        # except (ValueError, TypeError):
        #     messages.error(request, "Invalid price format.")
        #     has_errors = True

        # Validate category
        try:
            category = Category.objects.get(id=category_id)
        except (Category.DoesNotExist, ValueError):
            messages.error(request, "Invalid category selected.")
            has_errors = True

        # Validate flavour
        try:
            flavour = Flavour.objects.get(id=flavour_id)
        except (Flavour.DoesNotExist, ValueError):
            messages.error(request, "Invalid flavour selected.")
            has_errors = True

        # Validate main image
        if not image:
            messages.error(request, "Product image is required.")
            has_errors = True

        # Validate additional images
        additional_images = []
        for i in range(3):
            image_key = f'additional_product_image_{i}'
            if image_key in request.FILES:
                additional_images.append(request.FILES[image_key])
        
        if len(additional_images) < 3:
            messages.warning(request, f"You can upload up to 3 additional images. Currently, only {len(additional_images)} images are uploaded.")
            has_errors = True

        # Check for duplicate product
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

        # If no errors, save the product
        if not has_errors:
            try:
                product = Product.objects.create(
                    title=title,
                    # stock=int(stock),
                    description=description,
                    # price=price,
                    image=image,
                    category=category,
                    flavour=flavour,
                )

                if selected_sizes:
                    product.sizes.set(selected_sizes)
                    
                # Save additional images
                for additional_image in additional_images:
                    ProductImages.objects.create(
                        product=product,
                        image=additional_image
                    )

                # Add variant
              # Receive variant details from the form
                weights = request.POST.getlist('varient_weight[]')
                prices = request.POST.getlist('varient_price[]')
                stocks = request.POST.getlist('varient_stock[]')

                # Process each variant
                for weight, price, stock in zip(weights, prices, stocks):
                    if weight and price and stock:  # Ensure all fields are filled
                        try:
                            Variant.objects.create(
                                product=product,  # Assuming you already have the product instance
                                weight=weight,
                                price=float(price),
                                stock=int(stock)
                            )
                        except Exception as e:
                            messages.error(request, f"Error saving variant: {str(e)}")


                messages.success(request, "Product added successfully!")
                return redirect('product_list')

            except Exception as e:
                messages.error(request, f"Error saving product: {str(e)}")
                return redirect('add_products')

        # Redirect to avoid resubmission on page refresh
        return redirect('add_products')

    # GET request - display the form with the previous data
    context = {
        'categories': Category.objects.filter(is_active=True),
        'flavours': Flavour.objects.filter(is_active=True),
        # 'sizes': Size.objects.all(),
        'title': title,
        # 'stock': stock,
        'description': description,
        # 'price': price,
        'category_id': category_id,
        'flavour_id': flavour_id,
        # 'selected_sizes': selected_sizes,
    }
    return render(request, 'admin/product_management/add_product.html', context)

# Encapsulate product name validation
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
    product = get_object_or_404(Product, id=product_id)
    product_images = ProductImages.objects.filter(product=product)
    variants = Variant.objects.filter(product=product)

    if request.method == 'POST':
        title = request.POST.get('product_name')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        flavour_id = request.POST.get('flavour')

        # Validate product name
        product_name_error = validate_product_name(title)
        if product_name_error:
            messages.error(request, product_name_error)

        # Validate description
        if not description:
            messages.error(request, "Description is required.")

        # Validate category and flavour
        if not Category.objects.filter(id=category_id).exists():
            messages.error(request, "This category is currently unavailable.")
        if not Flavour.objects.filter(id=flavour_id).exists():
            messages.error(request, "This flavour is currently unavailable.")

        # Process additional images
        for i, img in enumerate(product_images, start=1):
            if request.POST.get(f'remove_image_{i}'):
                img.delete()
            elif f'extra_image_{i}' in request.FILES:
                img.image = request.FILES[f'extra_image_{i}']
                img.save()

        # Add new images
        for image in request.FILES.getlist('new_images'):
            ProductImages.objects.create(product=product, image=image)

        # Process variants (editing existing variants)
        for variant in variants:
            weight = request.POST.get(f'variant_weight_{variant.id}')
            price = request.POST.get(f'variant_price_{variant.id}')
            stock = request.POST.get(f'variant_stock_{variant.id}')
            delete_variant = request.POST.get(f'delete_variant_{variant.id}')

            if delete_variant:
                variant.delete()
            elif weight and price and stock:
                variant.weight = weight
                variant.price = float(price)
                variant.stock = int(stock)
                variant.save()

        # Add new variants (if there are no existing variants or if new variants are being added)
        new_weights = request.POST.getlist('new_variant_weight[]')
        new_prices = request.POST.getlist('new_variant_price[]')
        new_stocks = request.POST.getlist('new_variant_stock[]')

        for weight, price, stock in zip(new_weights, new_prices, new_stocks):
            if weight and price and stock:
                Variant.objects.create(
                    product=product,
                    weight=weight,
                    price=float(price),
                    stock=int(stock)
                )
            else:
                messages.error(request, "All fields are required for new variants.")
                return redirect('edit_product', product_id=product.id)

        # Update product details
        product.title = title
        product.description = description
        product.category = Category.objects.get(id=category_id)
        product.flavour = Flavour.objects.get(id=flavour_id)
        if 'main_image' in request.FILES:
            product.image = request.FILES['main_image']
        product.save()

        messages.success(request, "Product updated successfully!")
        return redirect('product_list')

    # Prepare context
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




#-------------------- delete_product-------------------
@user_passes_test(is_superuser, login_url='home:login')
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_active = False
    product.save()
    messages.error(request, "product blocked succesfully")
   
    return redirect('product_list') 


#-------------------- unblock_product-------------------
@user_passes_test(is_superuser, login_url='home:login')
def unblock_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_active = True
    product.save()
    messages.success(request, "product unblocked succesfully")

    

    return redirect('product_list')

#-------------------- category_list-------------------
@user_passes_test(is_superuser, login_url='home:login')
def category_list(request):
    # Get search query from request
    search_query = request.GET.get('search', '')
    
    # Filter categories based on search query
    if search_query:
        categories = Category.objects.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        ).order_by('name')
        paginator = Paginator(categories, items_per_page)

    else:
        categories = Category.objects.all().order_by('name')
    
    # Pagination
    page = request.GET.get('page', 1)
    items_per_page = 10  # You can adjust this number
    paginator = Paginator(categories, items_per_page)
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        page_obj = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        page_obj = paginator.page(paginator.num_pages)
    
    # Add message if no results found
    if search_query and not categories.exists():
        messages.info(request, f"No categories found matching '{search_query}'")
    
    context = {
        'categories': categories,
        'page_obj': page_obj,
        'search_query': search_query,
        'total_categories': categories.count(),
    }
    
    return render(request, 'admin/product_management/category_list.html', context)

# Update add_category view to handle form validation better
@user_passes_test(is_superuser, login_url='home:login')
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('category_name')
        description = request.POST.get('description')
        
        # Validation
        if not name:
            messages.error(request, "Category name is required.")
            return redirect('add_category')
            
        if Category.objects.filter(name__iexact=name).exists():
            messages.error(request, "This category already exists.")
            return redirect('add_category')
        
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

# Update edit_category view for better error handling
@user_passes_test(is_superuser, login_url='home:login')
def edit_category(request, id):
    category = get_object_or_404(Category, id=id)

    if request.method == 'POST':
        name = request.POST.get('category_name')
        description = request.POST.get('description')
        
        # Validation
        if not name:
            messages.error(request, "Category name is required.")
            return redirect('edit_category', id=id)
            
        # Check if name exists for other categories
        if Category.objects.filter(name__iexact=name).exclude(id=id).exists():
            messages.error(request, "A category with this name already exists.")
            return redirect('edit_category', id=id)
        
        try:
            category.name = name
            category.description = description
            category.save()
            messages.success(request, "Category updated successfully!")
            return redirect('category_list')
        except Exception as e:
            messages.error(request, f"Error updating category: {str(e)}")
            
    return render(request, 'admin/product_management/edit_category.html', {'category': category})

# Update delete_category view to add success message
@user_passes_test(is_superuser, login_url='home:login')
def delete_category(request, id):
    category = get_object_or_404(Category, id=id)
    category.is_active = False
    category.save()
    messages.error(request,format_html(f"Category '{category.name}' has been blocked successfully."))
    return redirect('category_list')

# Update unblock_category view to add success message
@user_passes_test(is_superuser, login_url='home:login')
def unblock_category(request, id):
    category = get_object_or_404(Category, id=id)
    category.is_active = True
    category.save()
    messages.success(request, format_html(f"Category '{category.name}' has been unblocked successfully."))
    return redirect('category_list')

#-------------------- flavour_list-------------------
@user_passes_test(is_superuser, login_url='home:login')
def flavour_list(request):
    flavour = Flavour.objects.all()
    context = {
        'flavours': flavour
    }
    return render(request,'admin/product_management/flavour_list.html', context)



#-------------------- add_flavour-------------------
@user_passes_test(is_superuser, login_url='home:login')
def add_flavour(request):
    if request.method == 'POST':
        name = request.POST.get('flavour_name')
        description = request.POST.get('description')

        Flavour.objects.get_or_create(
                name=name,
                
                description=description,
                
            )
            
        return redirect('flavour_list')


    return render(request, 'admin/product_management/add_flavour.html')

#-------------------- edit_flavour-------------------
@user_passes_test(is_superuser, login_url='home:login')
def edit_flavour(request, id):
    flavour = get_object_or_404(Flavour, id=id)

    if request.method == 'POST':
        flavour.name = request.POST.get('flavour_name')
        flavour.description = request.POST.get('description')
        category_id = request.POST.get('category')
        flavour_id = request.POST.get('flavour')

        try:
            if category_id:
                flavour.category = get_object_or_404(Category, id=category_id)
            if flavour_id:
                flavour.flavour = get_object_or_404(Flavour, id=flavour_id)

            flavour.save()
            # messages.success(request, "Category updated successfully!")
            return redirect('flavour_list')

        except ValueError:
            messages.error(request, "Invalid  flavour selected.")

    return render(request, 'admin/product_management/edit_flavour.html', {'flavour': flavour,'id':id})

@user_passes_test(is_superuser, login_url='home:login')
def delete_flavour(request, id):
    flavour = get_object_or_404(Flavour, id=id)
    flavour.is_active = False
    flavour.save()
    
 
    return redirect('flavour_list')

@user_passes_test(is_superuser, login_url='home:login')
def unblock_flavour(request, id):
    flavour = get_object_or_404(Flavour, id=id)
    flavour.is_active = True  
    flavour.save()  
    return redirect('flavour_list')

