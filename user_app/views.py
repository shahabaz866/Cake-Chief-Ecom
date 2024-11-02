from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import UserAddress,UserMobile
from django.contrib.auth.models import User
from django.contrib import messages
import re


@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone')

        # Update user details
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        # Update or create phone number
        UserMobile.objects.update_or_create(user=user, defaults={'mobile_number': phone_number})

        # Handle address fields
        name = request.POST.get('name')
        pincode = request.POST.get('pincode')
        locality = request.POST.get('locality')
        address = request.POST.get('address')
        city = request.POST.get('city')
        district = request.POST.get('district')
        state = request.POST.get('state')
        landmark = request.POST.get('landmark')

        # Check if the required fields are not empty before updating
        if name and pincode and locality and address and city and district and state:
            # Update or create user address
            UserAddress.objects.update_or_create(
                user=user,
                defaults={
                    'name': name,
                    'pincode': pincode,
                    'locality': locality,
                    'address': address,
                    'city': city,
                    'district': district,
                    'state': state,
                    'landmark': landmark,
                }
            )
            messages.success(request, "Profile updated successfully!")
        else:
            messages.error(request, "Please fill in all required fields for address.")

      
    try:
        user_mobile = UserMobile.objects.get(user=user).mobile_number
    except UserMobile.DoesNotExist:
        user_mobile = ''

    try:
        user_address = UserAddress.objects.get(user=user)
    except UserAddress.DoesNotExist:
        user_address = None

  

    context = {
        'user': user,
        'user_mobile': user_mobile,
        'user_address': user_address,
        
    }
    return render(request, 'user_side/user_profile/profile.html', context)

@login_required
def user_show_view(request):
    user = request.user
    try:
        user_mobile = UserMobile.objects.get(user=user).mobile_number
    except UserMobile.DoesNotExist:
        user_mobile = ''

    try:
        user_address = UserAddress.objects.get(user=user)
    except UserAddress.DoesNotExist:
        user_address = None

    context = {
        'user': user,
        'user_mobile': user_mobile,
        'user_address': user_address,
    }
    return render(request, 'user_side/user_profile/user_profile.html', context)



# @login_required(login_url='home:signin')
# def user_address(request):
#     user = request.user
#     addresses = UserAddress.objects.filter(user=user)
    
#     return render(request,'user_details/user_address.html', {'user': user, 'addresses': addresses} )

# @login_required(login_url='home:signin')
# def add_user_address(request):
#     if request.method == 'POST':
#         user = request.user
#         name = request.POST.get('name')
#         locality = request.POST.get('locality')
#         pincode = request.POST.get('pincode')
#         address = request.POST.get('address')
#         city = request.POST.get('city')
#         district = request.POST.get('district')
#         state = request.POST.get('state')
#         landmark = request.POST.get('landmark')

#         user_address = UserAddress(
#             user=user,
#             name=name,
#             pincode=pincode,
#             address=address,
#             city=city,
#             district=district,
#             state=state,
#             landmark=landmark,
#             locality = locality
#         )
#         # Save the instance to the database
#         user_address.save()
#         return redirect('user_profile:user_address')
#     return render(request,'user_details/add_user_address.html')

# @login_required(login_url='home:signin')
# def add_user_mobile(request):
#     if request.method == 'POST':
#         user = request.user
#         mobile = request.POST.get('mobile')

#         # Ensure the mobile number contains exactly 10 digits
#         if not mobile.isdigit() or len(mobile) != 10:
#             # The mobile number does not meet the required format
#             error_message = 'Invalid mobile number format. Please enter a 10-digit number.'
#             messages.error(request, error_message)
#             return render(request, 'user_details/add_user_mobile.html', {'error_message': error_message})

#         # Create a new UserMobile object with the user and mobile number
#         user_mobile = UserMobile(
#             user=user,
#             mobile_number=mobile
#         )

#         # Save the UserMobile object to the database
#         user_mobile.save()

#         # Redirect to the user profile page after saving the mobile number
#         return redirect('user_profile:user_profile')

#     # If the request method is not POST, render the add_user_mobile.html template
#     return render(request, 'user_details/add_user_mobile.html')

# @login_required(login_url='home:signin')
# def add_user_firstname(request):
#     if request.method == 'POST':
#         user = request.user
#         firstname = request.POST.get('firstname').strip()  # Remove leading and trailing whitespaces

#         # Validate if firstname is not empty or just whitespace
#         if not firstname:
#             error_message = 'Please enter a valid first name.'
#             messages.error(request, error_message)
#             return redirect('user_profile:add_user_firstname')  # Redirect to the same page to display the error message

#         # Update user details
#         user.first_name = firstname

#         # Save the changes
#         user.save()

#         return redirect('user_profile:user_profile')

#     # If the request method is not POST, render the add_user_firstname.html template
#     return render(request, 'user_details/add_user_firstname.html')

# @login_required(login_url='home:signin')
# def add_user_lastname(request):
#     if request.method == 'POST':
#         user = request.user
#         lastname = request.POST.get('lastname').strip()  # Remove leading and trailing whitespaces

#         # Validate if lastname is not empty or just whitespace
#         if not lastname:
#             error_message = 'Please enter a valid last name.'
#             messages.error(request, error_message)
#             return redirect('user_profile:add_user_lastname')  # Redirect to the same page to display the error message

#         # Update user details
#         user.last_name = lastname

#         # Save the changes
#         user.save()

#         return redirect('user_profile:user_profile')

#     # If the request method is not POST, render the add_user_lastname.html template
#     return render(request, 'user_details/add_user_lastname.html')

# @login_required(login_url='home:signin')
# def delete_user_address(request,id):
#     address=UserAddress.objects.get(id=id)
#     address.delete()
#     return redirect('user_profile:user_address')


# @login_required(login_url='home:signin')
# def edit_user_mobile(request):
#     user = request.user
#     user_mobile = UserMobile.objects.get(user=user)
#     if request.method == 'POST':
#         user = request.user
#         mobile = request.POST.get('mobile')

#         # Ensure the mobile number contains exactly 10 digits
#         if not mobile.isdigit() or len(mobile) != 10:
#             # The mobile number does not meet the required format
#             error_message = 'Invalid mobile number format. Please enter a 10-digit number.'
#             messages.error(request, error_message)
#             return redirect('user_profile:edit_user_mobile')  # Redirect to the same page to display the error message

#         # Check if the user already has a mobile number, and update it if exists
#         try:
#             user_mobile = UserMobile.objects.get(user=user)
#             user_mobile.mobile_number = mobile
#         except UserMobile.DoesNotExist:
#             # If the user does not have a mobile number, create a new UserMobile object
#             user_mobile = UserMobile(user=user, mobile_number=mobile)

#         # Save the UserMobile object to the database
#         user_mobile.save()

#         return redirect('user_profile:user_profile')

#     # If the request method is not POST, render the edit_user_mobile.html template
#     return render(request, 'user_details/edit_user_mobile.html',{'mobile':user_mobile})

# @login_required(login_url='home:signin')
# def edit_user_firstname(request):
#     user = request.user

#     if request.method == 'POST':
#         firstname = request.POST.get('firstname', '').strip()

#         # Check if firstname is not just a space
#         if not firstname:
#             messages.error(request, 'Please enter a valid first name.')
#             return redirect('user_profile:edit_user_firstname')

#         # Update user details
#         user.first_name = firstname

#         # Save the changes
#         user.save()
#         return redirect('user_profile:user_profile')

#     return render(request, 'user_details/edit_user_firstname.html', {'firstname': user.first_name})

# @login_required(login_url='home:signin')
# def edit_user_lastname(request):
#     user = request.user

#     if request.method == 'POST':
#         lastname = request.POST.get('lastname', '').strip()

#         # Check if lastname is not just a space
#         if not lastname:
#             messages.error(request, 'Please enter a valid last name.')
#             return redirect('user_profile:edit_user_lastname')

#         # Update user details
#         user.last_name = lastname

#         # Save the changes
#         user.save()
#         return redirect('user_profile:user_profile')

#     return render(request, 'user_details/edit_user_lastname.html', {'lastname': user.last_name})

# @login_required(login_url='home:signin')
# def add_address_checkout(request):
#     if request.method == 'POST':
#         user = request.user
#         name = request.POST.get('name')
#         locality = request.POST.get('locality')
#         pincode = request.POST.get('pincode')
#         address = request.POST.get('address')
#         city = request.POST.get('city')
#         district = request.POST.get('district')
#         state = request.POST.get('state')
#         landmark = request.POST.get('landmark')

#         user_address = UserAddress(
#             user=user,
#             name=name,
#             pincode=pincode,
#             address=address,
#             city=city,
#             district=district,
#             state=state,
#             landmark=landmark,
#             locality = locality
#         )
#         # Save the instance to the database
#         user_address.save()
#         return redirect('cart_management:cart_checkout')
#     return render(request,'user_details/add_user_address.html')
