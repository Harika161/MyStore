from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .models import Product, Order, OrderItem,Category
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

@login_required
def my_orders(request):
    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'orders.html', {
        'orders': orders,
    })
def home(request):
    search_query = request.GET.get('search', '')

    if search_query:
        products = Product.objects.filter(
            name__icontains=search_query
        ).order_by('-created_at')
    else:
        products = Product.objects.all().order_by('-created_at')

    cart = request.session.get('cart', {})

    for product in products:
        product.cart_quantity = cart.get(str(product.id), 0)

    return render(request, 'home.html', {
        'products': products,
        'search_query': search_query,
        'categories': Category.objects.all(),
    })


def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id)

    cart = request.session.get('cart', {})
    product_id = str(product_id)

    current_quantity = cart.get(product_id, 0)

    if current_quantity < product.stock:
        cart[product_id] = current_quantity + 1
        request.session['cart'] = cart

    return redirect('home')


def cart(request):
    cart = request.session.get('cart', {})

    products = Product.objects.filter(id__in=cart.keys())

    cart_items = []
    total = 0

    for product in products:
        quantity = cart[str(product.id)]
        subtotal = product.price * quantity
        total += subtotal

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total': total,
    })


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})

    product_id = str(product_id)

    if product_id in cart:
        del cart[product_id]

    request.session['cart'] = cart

    return redirect('cart')


def increase_quantity(request, product_id):
    cart = request.session.get('cart', {})

    product_id = str(product_id)

    if product_id in cart:
        product = Product.objects.get(id=int(product_id))
        current_quantity = cart[product_id]

        if current_quantity < product.stock:
            cart[product_id] += 1

    request.session['cart'] = cart

    return redirect('cart')

def checkout(request):
    cart = request.session.get('cart', {})

    products = Product.objects.filter(id__in=cart.keys())

    cart_items = []
    total = 0

    for product in products:
        quantity = cart[str(product.id)]
        subtotal = product.price * quantity
        total += subtotal

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })

    if request.method == 'POST':

        # Check stock before creating the order
        for item in cart_items:
            if item['quantity'] > item['product'].stock:
                return render(request, 'checkout.html', {
                    'cart_items': cart_items,
                    'total': total,
                    'error': f"{item['product'].name} does not have enough stock."
                })

        customer_name = request.POST.get('customer_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')

        order = Order.objects.create(
            user=request.user,
            customer_name=customer_name,
            email=email,
            phone=phone,
            address=address,
            total_amount=total
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['product'].price
            )

            item['product'].stock -= item['quantity']
            item['product'].save()

        request.session['cart'] = {}

        return redirect('order_success', order_id=order.id)

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total': total,
    })


def order_success(request, order_id):
    return render(request, 'order_success.html', {
        'order_id': order_id,
    })
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {
                'error': 'Username already exists.'
            })

        user = User.objects.create_user(
            username=username,
            password=password
        )

        login(request, user)

        return redirect('home')

    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('home')

        return render(request, 'login.html', {
            'error': 'Invalid username or password.'
        })

    return render(request, 'login.html')
def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def order_detail(request, order_id):
    order = Order.objects.get(
        id=order_id,
        user=request.user
    )

    return render(request, 'order_detail.html', {
        'order': order,
    })

def product_detail(request, product_id):
    product = Product.objects.get(id=product_id)

    return render(request, 'product_detail.html', {
        'product': product,
    })

def category_products(request, category_id):
    category = Category.objects.get(id=category_id)

    products = Product.objects.filter(
        category=category
    ).order_by('-created_at')

    return render(request, 'category_products.html', {
        'category': category,
        'products': products,
    })