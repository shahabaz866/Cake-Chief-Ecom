from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Wishlist, Product,Variant
from dashboard.models import Product, Variant
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse


@never_cache
@login_required(login_url='login')
def wishlist(request):
    try:        
            wishlist_items = Wishlist.objects.select_related('variant', 'product').filter(user=request.user)
            
            wishlist = []
            for item in wishlist_items:
                if not item.variant:
                    variant = Variant.objects.filter(product=item.product).first()
                else:
                    variant = item.variant
                    
                price = variant.price if variant else item.product.price
                wishlist_count = Wishlist.objects.filter(user=request.user).count()
                if wishlist_count == 0:
                  request.session.pop('wishlist_count',None)
                else:
                  request.session['wishlist_count'] = wishlist_count
                
                wishlist.append({
                    'id': item.id, 
                    'product': item.product,
                    'variant': variant,
                    'price': price
                })
            
            context = {'wishlist': wishlist}
            return render(request, 'user_side/wishlist/wishlist.html', context)
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)
@never_cache
@login_required(login_url='login')
def add_to_wishlist(request, product_id, variant_id):
    try:       
            product = get_object_or_404(Product, id=product_id)
            variant = None if variant_id == 0 else get_object_or_404(Variant, id=variant_id)

            


            if variant and variant.product != product:
                messages.error(request, "Invalid variant selection.")
                return redirect('wishlist_app:wishlist')

            wishlist_item, created = Wishlist.objects.get_or_create(
                user=request.user,
                product=product,
                variant=variant,
            )
            
            wishlist_count = Wishlist.objects.filter(user=request.user).count()
            if wishlist_count == 0:
                  request.session.pop('wishlist_count',None)
            else:
                  request.session['wishlist_count'] = wishlist_count
            if created:
                messages.success(request, "Item added to your wishlist.")
                
            else:
                messages.info(request, "Item is already in your wishlist.")

            return redirect('wishlist_app:wishlist') 
    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)
    


@never_cache
@login_required(login_url='login')
def remove_from_wishlist(request,wishlist_item_id):
    try:    
                wishlist_item = get_object_or_404(Wishlist, id=wishlist_item_id, user=request.user)
        
                wishlist_item.delete()
        #     messages.success(request, "Item removed from your wishlist.")
                wishlist_count = Wishlist.objects.filter(user=request.user).count()
              
                if wishlist_count == 0:
                       
                        request.session.pop('wishlist_count', None)
                else:
                       
                        request.session['wishlist_count'] = wishlist_count

                return redirect('wishlist_app:wishlist')

    except Http404:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except ObjectDoesNotExist:
            return render(request, 'user_side/error/error_page.html', {'error_code': 404}, status=404)

    except Exception as e:
                
            return render(request, 'user_side/error/error_page.html', {'error_code': 500}, status=500)

