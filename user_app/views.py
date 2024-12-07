from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from .models import Address, UserContact
from django.db import IntegrityError
import re

@never_cache
@login_required
def user_show_view(request):
    user = request.user
    try:
        user_mobile = UserContact.objects.get(user=user, contact_type='PRIMARY').mobile_number
    except UserContact.DoesNotExist:
        user_mobile = ''

    addresses = Address.objects.filter(user=user, is_active=True).order_by('-is_default')
    default_address = addresses.filter(is_default=True).first()

    context = {
        'user': user,
        'user_mobile': user_mobile,
        'addresses': addresses,
        'default_address': default_address,
    }
    return render(request, 'user_side/user_profile/user_profile.html', context)

phone_regex = r"^\+?[1-9](?!6)\d{1,14}$"

@never_cache
@login_required
def edit_profile_view(request):
    user = request.user
    if request.method == 'POST':
        # Retrieve form data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone', '').strip()  # Get phone number from form

        # Collect data to repopulate form in case of validation error
        data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone_number
        }

        # Validate required fields
        if not all(data.values()):
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'user_side/user_profile/edit_profile.html', {'data': data})

        # Validate names to contain only alphabetic characters
        if not (first_name.isalpha() and last_name.isalpha()):
            messages.error(request, "Please enter a valid name with alphabetic characters only.")
            return render(request, 'user_side/user_profile/edit_profile.html', {'data': data})

        # Validate phone number to be exactly 10 digits
        if not re.match(phone_regex,phone_number):
                messages.error(request, "Please enter a valid 10-digit phone number.")
                return render(request, 'user_side/user_profile/edit_profile.html', {'data': data})

        # Update user details
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        try:
            # Update or create primary phone number
            contact, created = UserContact.objects.update_or_create(
                user=user,
                contact_type='PRIMARY',
                defaults={'mobile_number': phone_number}
            )

        except IntegrityError:
            # Handle the unique constraint error gracefully
            messages.error(request, "This phone number is already in use. Please use a different number.")
            return render(request, 'user_side/user_profile/edit_profile.html', {'data': data})

        messages.success(request, "Profile updated successfully!")
        return redirect('user_app:user_show')

    # Fetch existing phone number if available
    try:
        user_mobile = UserContact.objects.get(user=user, contact_type='PRIMARY').mobile_number
    except UserContact.DoesNotExist:
        user_mobile = ''

    # Pass user and phone number to context
    context = {
        'user': user,
        'user_mobile': user_mobile,
    }
    return render(request, 'user_side/user_profile/edit_profile.html', context)
@never_cache
@login_required
def address_list_view(request):
    addresses = Address.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-is_default')
    
    return render(request, 'user_side/user_profile/user_profile.html', {
        'addresses': addresses
    })
@never_cache
@login_required
def add_address_view(request):
    # Collect Address model data in `data` dictionary
    data = {
        'name': request.POST.get('name', ''),
        'address_type': request.POST.get('address_type', 'HOME'),
        'pincode': request.POST.get('pincode', ''),
        'locality': request.POST.get('locality', ''),
        'address': request.POST.get('address', ''),
        'city': request.POST.get('city', ''),
        'district': request.POST.get('district', ''),
        'state': request.POST.get('state', ''),
        'landmark': request.POST.get('landmark', ''),
        'is_default': request.POST.get('is_default') == 'on',
        'phone_number' : request.POST.get('phone_number', '')
    }

    if request.method == 'POST':
        # Required fields in `data` dictionary, and check `phone_number` separately
        required_fields = ['name', 'pincode', 'locality', 'address', 'city', 'district', 'state','phone_number']
        
        if not all(data[field] for field in required_fields) :
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'user_side/address/add_address.html', {'data': data})

        # Additional validation for name, pincode, and phone_number
        if not data['name'].isalpha():
            messages.error(request, "Please enter a valid name with alphabetic characters only.")
            return render(request, 'user_side/address/add_address.html', {'data': data})

        if not data['pincode'].isdigit() or len(data['pincode']) != 6:
            messages.error(request, "Please enter a valid 6-digit pincode.")
            return render(request, 'user_side/address/add_address.html', {'data': data})

        if not data['phone_number'].isdigit() or len(data['phone_number']) != 10:
            messages.error(request, "Please enter a valid 10-digit phone number.")
            return render(request, 'user_side/address/add_address.html', {'data': data})

        # Create the address
        address = Address.objects.create(user=request.user, **data)

       

        messages.success(request, "Address and phone number added successfully!")
        return redirect('user_app:user_show')  # Redirect to the appropriate page

    return render(request, 'user_side/address/add_address.html', {'data': data})



@never_cache
@login_required
def edit_address_view(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == 'POST':
        # Collect data from form
        data = {
            'name': request.POST.get('name'),
            'address_type': request.POST.get('address_type', 'HOME'),
            'pincode': request.POST.get('pincode'),
            'locality': request.POST.get('locality'),
            'address': request.POST.get('address'),
            'city': request.POST.get('city'),
            'district': request.POST.get('district'),
            'state': request.POST.get('state'),
            'landmark': request.POST.get('landmark'),
            'is_default': request.POST.get('is_default') == 'on',
            'phone_number' : request.POST.get('phone_number', '')

        }

        # Validate required fields
        required_fields = ['name', 'pincode', 'locality', 'address', 'city', 'district', 'state','phone_number']
        if not all(data.get(field) for field in required_fields) :
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'user_side/address/edit_address.html', {'address': address})
          # Validate name
        if not data['name'].isalpha():
            messages.error(request, "Please enter a valid name with alphabetic characters only.")
            return render(request, 'user_side/address/add_address.html', {'data': data})

        # Validate pincode
        if not data['pincode'].isdigit() or len(data['pincode']) != 6:
            messages.error(request, "Please enter a valid 6-digit pincode.")
            return render(request, 'user_side/address/edit_address.html', {'address': address})

        # Validate phone number
        if not data['phone_number'].isdigit() or len(data['phone_number']) != 10:
            messages.error(request, "Please enter a valid 10-digit phone number.")
            return render(request, 'user_side/address/edit_address.html', {'address': address})

        # Update the address fields
        for key, value in data.items():
            setattr(address, key, value)
        address.save()

       

        messages.success(request, "Address and phone number updated successfully!")
        return redirect('user_app:user_show')

    # Handle GET request - Retrieve current phone number if it exists
    user_contact = UserContact.objects.filter(user=request.user, contact_type='PRIMARY').first()

    return render(request, 'user_side/address/edit_address.html', {
        'address': address,
        
    })

@never_cache
@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.is_active = False
    address.save()
    next_page = request.GET.get('next','user_app:user_show')
    if next_page =='':
        messages.success(request, "Address deleted successfully!")

        return redirect('cart_app:checkout')
    
    else:
        messages.success(request, "Address deleted successfully!")

        return redirect('user_app:user_show')

@never_cache
@login_required
def set_default_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)


    address.is_default = True
    address.save()
    next_page = request.GET.get('next','user_app:user_show')
    if next_page =='checkout':
            messages.success(request, "Default address updated successfully!")

            return redirect('cart_app:checkout')
    else:

        messages.success(request, "Default address updated successfully!")

        return redirect('user_app:user_show')

