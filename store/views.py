from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required


import random


from django.shortcuts import render
from .models import Product, Order, OrderItem

import razorpay
from django.conf import settings

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest





def product_list(request):
    products = Product.objects.all()
    return render(request, 'store/product_list.html', {'products': products})

from django.shortcuts import render, redirect, get_object_or_404
from .models import Product

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session['cart'] = cart
    return redirect('product_list')

def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        subtotal = product.price * quantity
        total += subtotal
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal
        })
    return render(request, 'store/cart.html', {'cart_items': cart_items, 'total': total})

def checkout(request):
    if request.method == 'POST':
        address = request.POST.get('address')
        cart = request.session.get('cart', {})

        # Create order linked to logged-in user
        previous_orders = Order.objects.filter(user=request.user).count()
        order = Order.objects.create(
            user=request.user,
            order_number=previous_orders + 1,
            transaction_id=random.randint(10000, 99999),
            address=address
        )
        # Save each cart item as an OrderItem
        total_amount = 0
        for product_id, quantity in cart.items():
            product = Product.objects.get(id=product_id)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity
            )
            total_amount += product.price * quantity

        # Clear cart
        request.session['cart'] = {}
        
        # Razorpay payment setup
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        payment = client.order.create({
            "amount": int(total_amount * 100),  # convert to paise
            "currency": "INR",
            "payment_capture": "1"
        })

        context = {
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'order_id': payment['id'],  # Add this
            'amount': payment['amount'],  # Optional, for display
            'name': request.user.username
       }

        return render(request, 'store/confirmation.html', context)

    return render(request, 'store/checkout.html')



def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('product_list')
    else:
        form = UserCreationForm()
    return render(request, 'store/register.html', {'form': form})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-date_ordered')
    return render(request, 'store/order_history.html', {'orders': orders})


from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm

def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('product_list')
    else:
        form = AuthenticationForm()
    return render(request, 'store/login.html', {'form': form})


def custom_logout(request):
    logout(request)
    return redirect('login')


@csrf_exempt
def verify_payment(request):
    if request.method == "POST":
        data = request.POST
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': data['razorpay_order_id'],
                'razorpay_payment_id': data['razorpay_payment_id'],
                'razorpay_signature': data['razorpay_signature']
            })
            # Payment verified — you can update order status here
            return redirect('order_history')  # or a success page
        except razorpay.errors.SignatureVerificationError:
            return redirect('payment_failed')
    return HttpResponseBadRequest()


def payment_failed(request):
    return render(request, 'store/payment_failed.html')



