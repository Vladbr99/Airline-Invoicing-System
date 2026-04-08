from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from .models import Customer, Flight, Invoice, InvoiceItem, UserProfile
from django.contrib.auth import logout

# Role helper
def user_has_role(user, role_name):
    # Admin override
    if user.username == "Admin":
        return True

    return hasattr(user, 'userprofile') and user.userprofile.role == role_name

# LOGIN
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('invoice_list')

        return render(request, 'login.html', {'error': 'Invalid username or password'})

    return render(request, 'login.html')

# LOGOUT
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# 1. View all invoices (Everyone)
@login_required
def invoice_list(request):
    invoices = Invoice.objects.all()
    return render(request, 'invoice_list.html', {'invoices': invoices})


# 2. Create invoice (SalesAgent only)
@login_required
def create_invoice(request):
    if not user_has_role(request.user, 'SalesAgent'):
        return render(request, 'no_permission.html')

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        customer = Customer.objects.get(id=customer_id)

        invoice = Invoice.objects.create(
            customer=customer,
            created_by=request.user,
            status="Pending",
            total=0
        )
        return redirect('add_invoice_item', invoice_id=invoice.id)

    customers = Customer.objects.all()
    return render(request, 'create_invoice.html', {'customers': customers})


# 3. Add invoice items (SalesAgent only)
@login_required
def add_invoice_item(request, invoice_id):
    if not user_has_role(request.user, 'SalesAgent'):
        return render(request, 'no_permission.html')

    invoice = get_object_or_404(Invoice, id=invoice_id)

    if request.method == 'POST':
        flight_id = request.POST.get('flight')
        quantity = int(request.POST.get('quantity'))

        flight = Flight.objects.get(id=flight_id)
        line_total = flight.base_price * quantity

        InvoiceItem.objects.create(
            invoice=invoice,
            flight=flight,
            quantity=quantity,
            line_total=line_total
        )

        invoice.total += line_total
        invoice.save()

        return redirect('invoice_list')

    flights = Flight.objects.all()
    return render(request, 'add_invoice_item.html', {
        'invoice': invoice,
        'flights': flights
    })


# 4. Update invoice status (Accountant only)
@login_required
def update_invoice_status(request, invoice_id):
    if not user_has_role(request.user, 'Accountant'):
        return render(request, 'no_permission.html')

    invoice = get_object_or_404(Invoice, id=invoice_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        invoice.status = new_status
        invoice.save()
        return redirect('invoice_list')

    return render(request, 'update_invoice_status.html', {'invoice': invoice})


# 5. Customer invoice report (Manager only)
@login_required
def customer_report(request):
    if not user_has_role(request.user, 'Manager'):
        return render(request, 'no_permission.html')

    customers = Customer.objects.all()
    invoices = None

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        invoices = Invoice.objects.filter(customer_id=customer_id)

    return render(request, 'customer_report.html', {
        'customers': customers,
        'invoices': invoices
    })
