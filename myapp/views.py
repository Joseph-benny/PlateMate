from django.shortcuts import render,redirect
from .models import *
from decimal import Decimal
import random
from django.conf import settings
from django.core.mail import send_mail
from datetime import date
from django.contrib import messages  # <-- ADD THIS LINE
from django.db.models import Q


def index(request):
    mnu = Menu.objects.all()

    if request.method == 'POST':
        query = request.POST.get('q', '').strip()
        action = request.POST.get('action', '')
        ft=request.POST.get('filter_category','')
        if ft=='all':
            mnu = Menu.objects.all()
        else:
            mnu = Menu.objects.filter(category=ft)
        if query:
            mnu = Menu.objects.filter(
                Q(itemname__icontains=query) |
                Q(category__icontains=query)
            )

        if action == 'combo':
            return redirect('/combo_offers/')
        elif action == 'special':
            return redirect('/special_offer/')

    # Get or create session number
    num = request.session.get('num')
    if not num:
        num = random.randint(1, 99)
        request.session['num'] = num

    # Fetch ALL cart items for this session/table
    regular_cart = Cart.objects.filter(table=num)
    combo_cart = ComboOfferCart.objects.filter(table=num)
    special_cart = SpecialOfferCart.objects.filter(table=num)

    # Fetch ALL orders for this table
    current_orders = Order.objects.filter(table=num)
    pending_orders = current_orders.filter(status__in=['Pending','Preparing'])
    ready_orders = current_orders.filter(status='Ready')
    served_orders = current_orders.filter(status='Served')

    # Process regular cart items
    regular_info = []
    regular_total = Decimal('0.00')

    for cart_entry in regular_cart:
        item = cart_entry.item
        qn = cart_entry.quantity or 0
        price = (item.itemprice or Decimal('0.00')) * Decimal(qn)
        regular_total += price
        regular_info.append({
            'type': 'regular',
            'item': cart_entry,
            'price': price,
        })

    # Process combo cart items
    combo_info = []
    combo_total = Decimal('0.00')

    for combo_entry in combo_cart:
        combo = combo_entry.item
        qn = combo_entry.quantity or 0
        price = (combo.combo_price or Decimal('0.00')) * Decimal(qn)
        combo_total += price
        combo_info.append({
            'type': 'combo',
            'item': combo_entry,
            'price': price,
        })

    # Process special cart items
    special_info = []
    special_total = Decimal('0.00')

    for special_entry in special_cart:
        special = special_entry.item
        qn = special_entry.quantity or 0
        price = (special.offer_price or Decimal('0.00')) * Decimal(qn)
        special_total += price
        special_info.append({
            'type': 'special',
            'item': special_entry,
            'price': price,
        })

    # Combine all items
    all_info = regular_info + combo_info + special_info

    # Calculate grand total
    grand_total = regular_total + combo_total + special_total
    total_items_count = len(all_info)

    # Calculate order totals
    order_total = Decimal('0.00')
    for order in current_orders:
        if order.item:
            order_total += order.item.itemprice * order.quantity
        elif order.combo:
            order_total += order.combo.combo_price * order.quantity
        elif order.special_offer:
            order_total += order.special_offer.offer_price * order.quantity

    context = {
        'mnu': mnu,
        'num': num,
        'regular_cart': regular_cart,
        'combo_cart': combo_cart,
        'special_cart': special_cart,
        'all_info': all_info,
        'regular_total': regular_total,
        'combo_total': combo_total,
        'special_total': special_total,
        'grand_total': grand_total,
        'total_items_count': total_items_count,
        'regular_info': regular_info,
        'combo_info': combo_info,
        'special_info': special_info,
        # Order tracking data
        'current_orders': current_orders,
        'pending_orders': pending_orders,
        'ready_orders': ready_orders,
        'served_orders': served_orders,
        'pending_count': pending_orders.count(),
        'ready_count': ready_orders.count(),
        'served_count': served_orders.count(),
        'order_total': order_total,
    }
    return render(request, 'index.html', context)

def register(request):
    msg=False
    if request.method == "POST":
        n=request.POST.get("name")
        ph=request.POST.get("phone")
        e=request.POST.get("email")
        p=request.POST.get("password")
        reg=Register(name=n,email=e,phone=ph,password=p,rights='Kitchen Handler')
        reg.save()
        msg=True
    return render(request, "register.html",{"msg":msg})

def login(request):
    msg=False
    if request.method == "POST":
        e=request.POST.get("email")
        p=request.POST.get("password")
        log=Register.objects.filter(email=e,password=p)
        if log:
            for i in log:
                r=i.rights
                if r=='Kitchen Handler':
                    kid=request.session.get('kid')
                    return redirect("/kitchenhandlerindex/")
                elif r=='Admin':
                    return redirect("/adminp/")
        else:
            msg=True
    return render(request, "login.html",{'msg':msg})

def logout(request):
    request.session.clear()
    return redirect("/")

def admin(request):
    kt=Register.objects.all()
    cm=Order.objects.filter(status='payment successful')
    pe=Order.objects.filter(status='Pending')
    return render(request, "admin/admin.html",{'kt':kt,'cm':cm,'pe':pe})

def kitchenhandler(request):
    kit=Register.objects.filter(rights='Kitchen Handler')
    if request.method == "POST":
        e = request.POST.get("email")
        p = request.POST.get("password")
        # Provider.objects.filter().update(email=e, password=p)
    return render(request, "admin/kitchenhandler.html",{'kit':kit})

def vieworders(request):
    vo=Order.objects.exclude(status='payment successful')
    pc=Order.objects.filter(status='Pending')
    pp=Order.objects.filter(status='Preparing')
    rd=Order.objects.filter(status='Ready')
    sd=Order.objects.filter(status='Served')
    return render(request,"kitchenhandler/vieworders.html",{'vo':vo,'pc':pc,'pp':pp,'rd':rd,'sd':sd })

def kitchenhandlerindex(request):
    return render(request,"kitchenhandler/kitchenhandlerindex.html")

def menu(request):
    msg=False
    m=Menu.objects.all()
    if request.method == "POST":
        act=request.POST.get('action')
        if act == 'menubtn':
            n=request.POST.get("itemname")
            c=request.POST.get("category")
            im=request.FILES['itemimage']
            p=request.POST.get("itemprice")
            of=request.POST.get("special")
            m=Menu(itemname=n,category=c,itemimage=im,itemprice=p,special=of)
            m.save()
            msg=True
            return redirect('/menu/')
        else:
            q = request.POST.get("q")
            m = Menu.objects.filter(itemname__icontains=q)

    return render(request, "kitchenhandler/menu.html",{"msg":msg,'m':m})


def add_to_cart(request, id, qn):
    text = ''
    try:
        mn = Menu.objects.get(id=id)
        text = 'menu'
    except Menu.DoesNotExist:
        try:
            mn = SpecialOffer.objects.get(id=id)
            text = 'special'
        except SpecialOffer.DoesNotExist:
            try:
                mn = ComboOffer.objects.get(id=id)
                text = 'combo'
            except ComboOffer.DoesNotExist:
                messages.error(request, "Item not found!")
                return redirect('/')

    num = request.session.get('num')


    if text == 'menu':
        cart_item = Cart.objects.filter(item=mn, table=num).first()
        if cart_item:
            cart_item.quantity = cart_item.quantity + int(qn)
            cart_item.save()
        else:
            cart_item = Cart(table=num, item=mn, quantity=qn)
            cart_item.save()
        messages.success(request, f"Added {mn.itemname} to cart!")
        return redirect('/#menu')

    elif text == 'special':
        cart_item = SpecialOfferCart.objects.filter(item=mn, table=num).first()
        if cart_item:
            cart_item.quantity = cart_item.quantity + int(qn)
            cart_item.save()
        else:
            cart_item = SpecialOfferCart(table=num, item=mn, quantity=qn)
            cart_item.save()
        return redirect('/special_offer#menu')

    elif text == 'combo':
        cart_item = ComboOfferCart.objects.filter(item=mn, table=num).first()
        if cart_item:
            cart_item.quantity = cart_item.quantity + int(qn)
            cart_item.save()
        else:
            cart_item = ComboOfferCart(table=num, item=mn, quantity=qn)
            cart_item.save()
        messages.success(request, f"Added {mn.combo_name} combo to cart!")
        return redirect('/combooffer#menu')
    return redirect('/')

def add_combo_cart(request, id, qn):
    num = request.session.get('num')

    try:
        combo = ComboOffer.objects.get(id=id)

        # Check if this combo is already in the cart for this table
        cart_item = ComboOfferCart.objects.filter(item=combo, table=num).first()

        if cart_item:
            # Update quantity if already exists
            cart_item.quantity = cart_item.quantity + int(qn)
            cart_item.save()
        else:
            # Create new cart entry
            cart_item = ComboOfferCart(table=num, item=combo, quantity=qn)
            cart_item.save()

    except ComboOffer.DoesNotExist:
        # Handle error - combo not found
        messages.error(request, "Combo offer not found!")

    # Redirect back to combo offers page
    return redirect('/combo_offers#menu')


def get_cart_count(request):
    num = request.session.get('num')
    if not num:
        return JsonResponse({'combo_count': 0})

    combo_count = ComboOfferCart.objects.filter(table=num).count()
    return JsonResponse({'combo_count': combo_count})

def delete_cart(request, cart_id):
    try:
        cart_item = Cart.objects.get(id=cart_id)
        cart_item.delete()
    except Cart.DoesNotExist:
        pass
    return redirect(request.META.get('HTTP_REFERER', '/'))

def delete_combo_cart(request, cart_id):
    try:
        cart_item = ComboOfferCart.objects.get(id=cart_id)
        cart_item.delete()
    except ComboOfferCart.DoesNotExist:
        pass
    return redirect(request.META.get('HTTP_REFERER', '/'))

def delete_special_cart(request, cart_id):
    try:
        cart_item = SpecialOfferCart.objects.get(id=cart_id)
        cart_item.delete()
    except SpecialOfferCart.DoesNotExist:
        pass
    return redirect(request.META.get('HTTP_REFERER', '/'))


def make_order(request):
    num = request.session.get('num')

    # Handle regular cart items
    cart_items = Cart.objects.filter(table=num)
    for item in cart_items:
        order = Order(
            table=num,
            item=item.item,
            quantity=item.quantity,
            status='Pending'
        )
        order.save()
    # Delete regular cart items after saving all
    cart_items.delete()

    # Handle combo offer cart items
    combo_cart_items = ComboOfferCart.objects.filter(table=num)
    for item in combo_cart_items:
        order = Order(
            table=num,
            combo=item.item,
            quantity=item.quantity,
            status='Pending'
        )
        order.save()
    # Delete combo cart items after saving all
    combo_cart_items.delete()

    # Handle special offer cart items
    special_cart_items = SpecialOfferCart.objects.filter(table=num)
    for item in special_cart_items:
        order = Order(
            table=num,
            special_offer=item.item,
            quantity=item.quantity,
            status='Pending'
        )
        order.save()
    # Delete special cart items after saving all
    special_cart_items.delete()

    return redirect('/confirm_order/')

from django.http import JsonResponse
import json

def update_order_status(request, order_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_status = data.get('status')

            order = Order.objects.get(id=order_id)
            order.status = new_status
            order.save()

            return JsonResponse({'success': True, 'new_status': new_status})
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Order not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def confirm_order(request):
    num = request.session.get('num')

    # Get all orders for this table
    orders = Order.objects.filter(table=num)

    # Calculate total
    total = 0
    for order in orders:
        if order.item:
            total += float(order.item.itemprice) * order.quantity
        elif order.combo:
            total += float(order.combo.combo_price) * order.quantity
        elif order.special_offer:
            total += float(order.special_offer.offer_price) * order.quantity

    return render(request, 'user/confirmorder.html', {
        'ord': orders,
        'total': total
    })
from django.db import transaction



def payment(request):
    num = request.session.get('num')

    orders = Order.objects.filter(table=num)

    # Calculate total considering all possible item types
    total = 0
    for order in orders:
        if order.item:
            total += order.item.itemprice * order.quantity
        elif order.combo:
            total += order.combo.combo_price * order.quantity
        elif order.special_offer:
            total += order.special_offer.offer_price * order.quantity

    if request.method == "POST":
        payment_method = request.POST.get('payment_method', 'cash')

        try:
            with transaction.atomic():
                # Update all orders at once
                orders.update(status='payment successful')

                # Clear all cart types for this table
                Cart.objects.filter(table=num).delete()
                SpecialOfferCart.objects.filter(table=num).delete()
                ComboOfferCart.objects.filter(table=num).delete()

                # Clear the session table number
                if 'num' in request.session:
                    del request.session['num']

                return redirect('/submit/')

        except Exception as e:
            messages.error(request, f"Payment failed: {str(e)}")
            return render(request, 'user/payment.html', {'total': total})

    return render(request, 'user/payment.html', {'total': total, 'orders': orders})

def submit(request):
    return render(request, 'user/submit.html')

def email(request):
    msg=''
    if request.method == "POST":
        e=request.POST.get("email")
        reg=Register.objects.filter(email=e)
        if reg:
            subject='PlateMate'
            o=str(random.randint(0000, 9999))
            message=f'Single time OTP:{o}'
            request.session['otp']=o
            request.session['email']=e
            email_from=settings.EMAIL_HOST_USER
            recipient_list=[e]
            send_mail(subject, message, email_from, recipient_list)
            msg="Email"
            return redirect('/otp/')
        else:
            msg="invalid"
    return render (request, "email.html")

def otp(request):
    msg=False
    if request.method == "POST":
        o=request.POST.get("otp")
        otp=request.session.get('otp')
        if otp==o:
            return redirect('/password/')
        else:
            msg=True
    return render (request,"otp.html",{'msg':msg})

def password (request):
    msg=False
    email = request.session['email']
    if request.method =="POST":
        p=request.POST.get("password")
        np=request.POST.get("npassword")
        if p==np:
            Register.objects.filter(email=email).update(password=np)
            return redirect('/login/')
        else:
            msg=True
    return render (request,"password.html",{'msg':msg})

def delete_menu(request,id):
    Menu.objects.filter(id=id).delete()
    return redirect('/menu/')


def sales(request):
    msg = False
    kt = Register.objects.all()

    # Fix typo in status
    cm = Order.objects.filter(status='payment successful')
    pe = Order.objects.filter(status__in=['Pending', 'ready', 'served'])
    vo = Order.objects.all()

    # Initialize totals
    total_revenue = 0
    total_orders_count = 0

    if request.method == "POST":
        date_from = request.POST.get("date_from")
        date_to = request.POST.get("date_to")

        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()

        # Apply date filters if provided
        if date_from and date_to:
            vo = Order.objects.filter(date__range=[date_from, date_to])
            cm = Order.objects.filter(status='payment successful', date__range=[date_from, date_to])
            pe = Order.objects.filter(status__in=['Pending', 'ready', 'served'], date__range=[date_from, date_to])
        elif date_from:
            today = date.today()
            vo = Order.objects.filter(date__range=[date_from, today])
            cm = Order.objects.filter(status='payment successful', date__range=[date_from, today])
            pe = Order.objects.filter(status__in=['Pending', 'ready', 'served'], date__range=[date_from, today])
        elif date_to:
            # Handle case when only end date is provided
            vo = Order.objects.filter(date__lte=date_to)
            cm = Order.objects.filter(status='payment successful', date__lte=date_to)
            pe = Order.objects.filter(status__in=['Pending', 'ready', 'served'], date__lte=date_to)

    # Calculate total revenue from completed orders
    for order in cm:
        if order.item:
            total_revenue += order.item.itemprice * order.quantity
        elif order.combo:
            total_revenue += float(order.combo.combo_price) * order.quantity
        elif order.special_offer:
            total_revenue += float(order.special_offer.offer_price) * order.quantity

    total_orders_count = vo.count()
    completed_orders_count = cm.count()
    pending_orders_count = pe.count()

    context = {
        'kt': kt,
        'cm': cm,
        'pe': pe,
        'vo': vo,
        'total_revenue': total_revenue,
        'total_orders': total_orders_count,
        'completed_orders': completed_orders_count,
        'pending_orders': pending_orders_count,
        'msg': msg
    }

    return render(request, "admin/sales.html", context)


def add_special_offer(request):
    """
    Handles displaying menu items and creating a new SpecialOffer.
    """
    # Fetch all menu items to display for selection
    menu_items = Menu.objects.all().order_by('itemname')
    if request.method == 'POST':
        offer_name = request.POST.get('offer_name')
        selected_item_ids = request.POST.get('selected_items')
        mn = Menu.objects.get(id=selected_item_ids)
        # RETRIEVE THE CALCULATED PRICE from the hidden input field
        try:
            # Convert to float for safety, though it comes as a string
            offer_price = float(request.POST.get('offer_price', 0))
        except ValueError:
            messages.error(request, "Invalid price amount submitted.")
            return redirect('add_special_offer')

        if not offer_name or not selected_item_ids:
            messages.error(request, "Please enter a name and select items for the special offer.")
            return redirect('add_special_offer')

        try:
            # 1. Create the new SpecialOffer object, including the calculated price
            new_offer = SpecialOffer.objects.create(
                offer_name=offer_name,
                offer_price=offer_price ,
                items=mn
            )

            # 2. Add the selected menu items


            messages.success(request, f"Special Offer '{offer_name}' created successfully at ₹{offer_price:.2f}!")
            return redirect('add_special_offer')

        except Exception as e:
            messages.error(request, f"Error creating special offer: {e}")
            return redirect('add_special_offer')


    # For GET request (initial page load)
    context = {
        'menu_items': menu_items,
        # You might also want to display existing offers
        'existing_offers': SpecialOffer.objects.all().order_by('-created_at')
    }
    return render(request, 'kitchenhandler/special_offer.html', context)
def manage_menu_page(request):
    # This is the function that renders your main menu page (the one you provided)
    # It fetches all menu items and passes them to the template
    m = Menu.objects.all()
    # ... logic for adding menu items, search, etc. ...
    return render(request, 'menu_page.html', {'m': m}) # Assuming your main menu template is 'menu_page.html'


def add_combo_offer(request):
    """
    Handles displaying menu items, processing form submission,
    and enforcing the 2-item minimum for combo creation.
    """
    # Fetch all menu items and existing combos
    menu_items = Menu.objects.all().order_by('itemname')
    existing_combos = ComboOffer.objects.all().order_by('-created_at')

    if request.method == 'POST':
        print("Pressed")
        # Retrieve data from the submitted form (using name attributes)
        combo_name = request.POST.get('combo_name')
        selected_item_ids = request.POST.getlist('selected_items')
        image = request.FILES['image']

        # The price is calculated by JavaScript and sent via a hidden input
        try:
            combo_price = float(request.POST.get('combo_price', 0))
        except ValueError:
            messages.error(request, "Invalid price amount submitted.")
            return redirect('add_combo_offer')

        # --- Validation Checks ---
        if not combo_name:
            messages.error(request, "Please enter a name for the combo offer.")
            return redirect('add_combo_offer')

        if len(selected_item_ids) < 2:
            messages.error(request, "A combo offer must contain at least two items.")
            return redirect('add_combo_offer')
        # -------------------------

        try:
            # Create the new ComboOffer object
            new_combo = ComboOffer.objects.create(
                combo_name=combo_name,
                combo_price=combo_price,
                image=image # Save the 15% discounted price
            )

            # Link the selected menu items
            new_combo.items.set(selected_item_ids)

            messages.success(request, f"Combo Offer '{combo_name}' created successfully at ₹{combo_price:.2f}!")
            return redirect('add_combo_offer')

        except Exception as e:
            messages.error(request, f"Error creating combo offer: {e}")
            return redirect('add_combo_offer')

    # For GET request (initial page load)
    context = {
        'm': menu_items,  # Using 'm' to match your template variable
        'existing_combos': existing_combos,
    }
    # Assuming the template file is named 'addcombo.html'
    return render(request, 'kitchenhandler/addcombo.html', context)


def combooffer(request):
    # all combos (for listing on page)
    mnu = ComboOffer.objects.all()

    # ensure a session identifier exists before querying the cart
    num = request.session.get('num')
    if not num:
        num = random.randint(1, 999999)
        request.session['num'] = num

    # Fetch ALL cart items for this session/table
    regular_cart = Cart.objects.filter(table=num)
    combo_cart = ComboOfferCart.objects.filter(table=num)
    special_cart = SpecialOfferCart.objects.filter(table=num)

    # Process regular cart items
    regular_info = []
    regular_total = Decimal('0.00')

    for cart_entry in regular_cart:
        item = cart_entry.item
        qn = cart_entry.quantity or 0
        price = (item.itemprice or Decimal('0.00')) * Decimal(qn)
        regular_total += price
        regular_info.append({
            'type': 'regular',
            'cart_entry': cart_entry,
            'item': item,
            'price': price,
        })

    # Process combo cart items
    combo_info = []
    combo_total = Decimal('0.00')

    for cart_entry in combo_cart:
        combo = cart_entry.item
        qn = cart_entry.quantity or 0
        price = (combo.combo_price or Decimal('0.00')) * Decimal(qn)
        combo_total += price
        combo_items = list(combo.items.all())
        combo_info.append({
            'type': 'combo',
            'cart_entry': cart_entry,
            'combo': combo,
            'combo_items': combo_items,
            'price': price,
        })

    # Process special cart items
    special_info = []
    special_total = Decimal('0.00')

    for cart_entry in special_cart:
        special = cart_entry.item
        qn = cart_entry.quantity or 0
        price = (special.offer_price or Decimal('0.00')) * Decimal(qn)
        special_total += price
        special_info.append({
            'type': 'special',
            'cart_entry': cart_entry,
            'item': special,
            'price': price,
        })

    # Combine all items for the order summary
    all_info = regular_info + combo_info + special_info

    # Calculate grand total
    grand_total = regular_total + combo_total + special_total

    # Calculate total count of all items
    total_items_count = len(all_info)

    context = {
        'mnu': mnu,
        'num': num,
        'regular_cart': regular_cart,
        'combo_cart': combo_cart,
        'special_cart': special_cart,
        'regular_info': regular_info,
        'combo_info': combo_info,
        'special_info': special_info,
        'all_info': all_info,
        'regular_total': regular_total,
        'combo_total': combo_total,
        'special_total': special_total,
        'grand_total': grand_total,
        'total_items_count': total_items_count,
        # For backward compatibility (keep existing variable names)
        'cart': combo_cart,
        'info': combo_info,
        'total': grand_total,
    }
    return render(request, 'user/combooffer.html', context)


def specialoffer(request):
    # All special offers for display
    mnu = SpecialOffer.objects.all()

    # Get or create session number
    num = request.session.get('num')
    if not num:
        num = random.randint(1, 999999)
        request.session['num'] = num

    # Fetch ALL cart items for this session/table
    regular_cart = Cart.objects.filter(table=num)
    combo_cart = ComboOfferCart.objects.filter(table=num)
    special_cart = SpecialOfferCart.objects.filter(table=num)

    # Process regular cart items
    regular_info = []
    regular_total = Decimal('0.00')

    for cart_entry in regular_cart:
        item = cart_entry.item
        qn = cart_entry.quantity or 0
        price = (item.itemprice or Decimal('0.00')) * Decimal(qn)
        regular_total += price
        regular_info.append({
            'type': 'regular',
            'cart_entry': cart_entry,
            'item': item,
            'price': price,
        })

    # Process combo cart items
    combo_info = []
    combo_total = Decimal('0.00')

    for cart_entry in combo_cart:
        combo = cart_entry.item
        qn = cart_entry.quantity or 0
        price = (combo.combo_price or Decimal('0.00')) * Decimal(qn)
        combo_total += price
        combo_items = list(combo.items.all())
        combo_info.append({
            'type': 'combo',
            'cart_entry': cart_entry,
            'combo': combo,
            'combo_items': combo_items,
            'price': price,
        })

    # Process special cart items
    special_info = []
    special_total = Decimal('0.00')

    for cart_entry in special_cart:
        special = cart_entry.item
        qn = cart_entry.quantity or 0
        price = (special.offer_price or Decimal('0.00')) * Decimal(qn)
        special_total += price
        special_info.append({
            'type': 'special',
            'cart_entry': cart_entry,
            'item': special,
            'price': price,
        })

    # Combine all items for the order summary
    all_info = regular_info + combo_info + special_info

    # Calculate grand total
    grand_total = regular_total + combo_total + special_total

    # Calculate total count of all items
    total_items_count = len(all_info)

    context = {
        'mnu': mnu,
        'num': num,
        'regular_cart': regular_cart,
        'combo_cart': combo_cart,
        'special_cart': special_cart,
        'regular_info': regular_info,
        'combo_info': combo_info,
        'special_info': special_info,
        'all_info': all_info,
        'regular_total': regular_total,
        'combo_total': combo_total,
        'special_total': special_total,
        'grand_total': grand_total,
        'total_items_count': total_items_count,
        # For backward compatibility
        'cart': special_cart,
        'info': special_info,
        'total': grand_total,
    }
    return render(request, 'user/specialoffer.html', context)

def orders(request):
    return render(request, 'user/orders.html')