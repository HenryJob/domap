def cart_badges(request):
    from cart.cart import Cart
    from cart.wishlist import Wishlist
    cart = Cart(request)
    wishlist = Wishlist(request)
    return {
        'cart_count': cart.total_quantity(),
        'wishlist_count': wishlist.count(),
    }
