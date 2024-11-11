from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from .models import Address, UserContact

@never_cache
@login_required
def user_show_view(request):
    user = request.user
    try:
        user_mobile = UserContact.objects.get(
            user=user, 
            contact_type='PRIMARY'
        ).mobile_number
    except UserContact.DoesNotExist:
        user_mobile = ''

    addresses = Address.objects.filter(
        user=user,
        is_active=True
    ).order_by('-is_default')
    
    default_address = addresses.filter(is_default=True).first()

    context = {
        'user': user,
        'user_mobile': user_mobile,
        'addresses': addresses,
        'default_address': default_address,
    }
    return render(request, 'user_side/user_profile/user_profile.html', context)

@never_cache
@login_required
def edit_profile_view(request):
    user = request.user
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone')

        if not phone_number.isdigit() or len(phone_number) != 10:
            messages.error(request, "Please enter a valid 10-digit phone number.")
            return redirect('user_app:edit_profile')

        # Update user details
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        # Update or create primary phone number
        UserContact.objects.update_or_create(
            user=user,
            defaults={
                'mobile_number': phone_number,
                'contact_type': 'PRIMARY'
            }
        )

        messages.success(request, "Profile updated successfully!")
        return redirect('user_app:user_show')

    try:
        user_mobile = UserContact.objects.get(
            user=user,
            contact_type='PRIMARY'
        ).mobile_number
    except UserContact.DoesNotExist:
        user_mobile = ''

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
    if request.method == 'POST':
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
            'is_default': request.POST.get('is_default') == 'on'
        }

        # Validate required fields
        required_fields = ['name', 'pincode', 'locality', 'address', 'city', 'district', 'state']
        if not all(data[field] for field in required_fields):
            messages.error(request, "Please fill in all required fields.")
            return redirect('user_app:add_address')

        if not data['pincode'].isdigit() or len(data['pincode']) != 6:
            messages.error(request, "Please enter a valid 6-digit pincode.")
            return redirect('user_app:add_address')
        
        # Add the user to the data dictionary
        data['user'] = request.user  # Associate the address with the logged-in user

        # Create new address
        Address.objects.create(**data)

        messages.success(request, "Address added successfully!")
        return redirect('user_app:user_show')  # Redirect to address list or another relevant page

    return render(request, 'user_side/address/add_address.html', {
        'address': None  # No address is passed because it's for adding
    })


@never_cache
@login_required
def edit_address_view(request, address_id):
    address = get_object_or_404(Address, id=address_id)

    if request.method == 'POST':
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
            'is_default': request.POST.get('is_default') == 'on'
        }

        # Validate required fields
        required_fields = ['name', 'pincode', 'locality', 'address', 'city', 'district', 'state']
        if not all(data[field] for field in required_fields):
            messages.error(request, "Please fill in all required fields.")
            return redirect('user_app:edit_address', address_id=address.id)

        if not data['pincode'].isdigit() or len(data['pincode']) != 6:
            messages.error(request, "Please enter a valid 6-digit pincode.")
            return redirect('user_app:edit_address', address_id=address.id)

        # Update existing address
        for key, value in data.items():
            setattr(address, key, value)
        address.save()

        messages.success(request, "Address updated successfully!")
        return redirect('user_app:user_show')  # Redirect to address list or another relevant page

    return render(request, 'user_side/address/edit_address.html', {
        'address': address  # Pass the existing address to the template
    })

@never_cache
@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.is_active = False
    address.save()
    messages.success(request, "Address deleted successfully!")
    return redirect('user_app:user_show')

@never_cache
@login_required
def set_default_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    # The model's save method will handle removing default status from other addresses
    address.is_default = True
    address.save()
    messages.success(request, "Default address updated successfully!")
    return redirect('user_app:user_show')



