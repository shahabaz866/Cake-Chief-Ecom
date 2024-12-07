from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Wishlist, Product,Variant
from dashboard.models import Product, Variant
from django.contrib import messages
from django.views.decorators.cache import never_cache


@never_cache
@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.select_related('variant', 'product').filter(user=request.user)

    wishlist = []
    for item in wishlist_items:
        # Use variant price if available, otherwise fallback to product price
        price = item.variant.price if item.variant else item.product.price
        wishlist.append({
            'product': item.product,
            'variant': item.variant,
            'price': price
        })
        # for variant in Variant.objects.all():
        #     print(f"Variant: {variant.product.title} - {variant.weight}, Price: {variant.price}")

        wishlist = []
    for item in wishlist_items:
    # Debug print
        print(f"Processing item: {item.product.title}")
    if item.variant:
        print(f"Variant Price: {item.variant.price}")
        price = item.variant.price
    else:
        print(f"Product Price: {item.product.price}")
        price = item.product.price

    wishlist.append({
        'product': item.product,
        'variant': item.variant,
        'price': price
    })

    context = {'wishlist': wishlist}
    return render(request, 'user_side/wishlist/wishlist.html', context)

def add_to_wishlist(request, product_id, variant_id):
    product = get_object_or_404(Product, id=product_id)
    variant = None if variant_id == "0" else get_object_or_404(Variant, id=variant_id)

    # Check if the item already exists in the wishlist
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product,
        variant=variant,
    )

    if created:
        messages.success(request, "Item added to your wishlist.")
    else:
        messages.info(request, "Item is already in your wishlist.")

    return redirect('wishlist_app:wishlist')


@login_required
def remove_from_wishlist(request, product_id, variant_id=0):
    """
    Removes a specific product or variant from the user's wishlist.
    """
    # Get the current user's wishlist
    wishlist_item = get_object_or_404(
        Wishlist,
        user=request.user,
        product_id=product_id,
        variant_id=variant_id if variant_id != 0 else None
    )
    
    # Delete the wishlist item
    wishlist_item.delete()
    
    # Redirect to the wishlist page
    return redirect('wishlist_app:wishlist')

