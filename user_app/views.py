from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from .models import Address, UserContact
from django.db import IntegrityError
import re
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist


@never_cache
@login_required(login_url='login')
def user_show_view(request):
    try:      
            referer = request.META.get('HTTP_REFERER', '')
            from_checkout = 'cart_app:checkout' in referer
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
                'from_checkout': from_checkout,
            }
            return render(request, 'user_side/user_profile/user_profile.html', context)
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

phone_regex = r"^\+?[1-9](?!6)\d{1,14}$"

@never_cache
@login_required(login_url='login')
def edit_profile_view(request):
    try:        
            user = request.user
            if request.method == 'POST':
            
                first_name = request.POST.get('first_name', '').strip()
                last_name = request.POST.get('last_name', '').strip()
                email = request.POST.get('email', '').strip()
                phone_number = request.POST.get('phone', '').strip()  

            
                data = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'phone': phone_number
                }

                if not all(data.values()):
                    messages.error(request, "Please fill in all required fields.")
                    return render(request, 'user_side/user_profile/edit_profile.html', {'data': data})

                if not (first_name.isalpha() and last_name.isalpha()):
                    messages.error(request, "Please enter a valid name with alphabetic characters only.")
                    return render(request, 'user_side/user_profile/edit_profile.html', {'data': data})

                if not re.match(phone_regex,phone_number):
                        messages.error(request, "Please enter a valid 10-digit phone number.")
                        return render(request, 'user_side/user_profile/edit_profile.html', {'data': data})

                user.first_name = first_name
                user.last_name = last_name
                user.email = email
                user.save()

                try:
                    contact, created = UserContact.objects.update_or_create(
                        user=user,
                        contact_type='PRIMARY',
                        defaults={'mobile_number': phone_number}
                    )

                except IntegrityError:
                    messages.error(request, "This phone number is already in use. Please use a different number.")
                    return render(request, 'user_side/user_profile/edit_profile.html', {'data': data})

                messages.success(request, "Profile updated successfully!")
                return redirect('user_app:user_show')

            try:
                user_mobile = UserContact.objects.get(user=user, contact_type='PRIMARY').mobile_number
            except UserContact.DoesNotExist:
                user_mobile = ''

            context = {
                'user': user,
                'user_mobile': user_mobile,
            }
            return render(request, 'user_side/user_profile/edit_profile.html', context)
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)
@never_cache
@login_required(login_url='login')
def address_list_view(request):
    try:        
            addresses = Address.objects.filter(
                user=request.user,
                is_active=True
            ).order_by('-is_default')
            
            return render(request, 'user_side/user_profile/user_profile.html', {
                'addresses': addresses
            })
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)
@never_cache
@login_required(login_url='login')
def add_address_view(request):
    try:       
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
                required_fields = ['name', 'pincode', 'locality', 'address', 'city', 'district', 'state','phone_number']
                
                if not all(data[field] for field in required_fields) :
                    messages.error(request, "Please fill in all required fields.")
                    return render(request, 'user_side/address/add_address.html', {'data': data})

                if not data['name'].isalpha():
                    messages.error(request, "Please enter a valid name with alphabetic characters only.")
                    return render(request, 'user_side/address/add_address.html', {'data': data})

                if not data['pincode'].isdigit() or len(data['pincode']) != 6:
                    messages.error(request, "Please enter a valid 6-digit pincode.")
                    return render(request, 'user_side/address/add_address.html', {'data': data})

                if not data['phone_number'].isdigit() or len(data['phone_number']) != 10:
                    messages.error(request, "Please enter a valid 10-digit phone number.")
                    return render(request, 'user_side/address/add_address.html', {'data': data})

                address = Address.objects.create(user=request.user, **data)

            

                messages.success(request, "Address and phone number added successfully!")
                return redirect('user_app:user_show')  

            return render(request, 'user_side/address/add_address.html', {'data': data})
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)


@never_cache
@login_required(login_url='login')
def edit_address_view(request, address_id):
    try:        
            address = get_object_or_404(Address, id=address_id, user=request.user)

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
                    'is_default': request.POST.get('is_default') == 'on',
                    'phone_number' : request.POST.get('phone_number', '')

                }

                required_fields = ['name', 'pincode', 'locality', 'address', 'city', 'district', 'state','phone_number']
                if not all(data.get(field) for field in required_fields) :
                    messages.error(request, "Please fill in all required fields.")
                    return render(request, 'user_side/address/edit_address.html', {'address': address})
                if not data['name'].isalpha():
                    messages.error(request, "Please enter a valid name with alphabetic characters only.")
                    return render(request, 'user_side/address/add_address.html', {'data': data})

                if not data['pincode'].isdigit() or len(data['pincode']) != 6:
                    messages.error(request, "Please enter a valid 6-digit pincode.")
                    return render(request, 'user_side/address/edit_address.html', {'address': address})

                if not data['phone_number'].isdigit() or len(data['phone_number']) != 10:
                    messages.error(request, "Please enter a valid 10-digit phone number.")
                    return render(request, 'user_side/address/edit_address.html', {'address': address})

                for key, value in data.items():
                    setattr(address, key, value)
                address.save()

            

                messages.success(request, "Address and phone number updated successfully!")
                return redirect('user_app:user_show')

            user_contact = UserContact.objects.filter(user=request.user, contact_type='PRIMARY').first()

            return render(request, 'user_side/address/edit_address.html', {
                'address': address,
                
            })
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

@never_cache
@login_required(login_url='login')
def delete_address(request, address_id):
    try:       
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
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

@never_cache
@login_required(login_url='login')
def set_default_address(request, address_id):
    try:        
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
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

