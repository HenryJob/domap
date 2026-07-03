from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from orders.models import Order
from .forms import SignUpForm, SavedAddressForm
from .models import SavedAddress


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'¡Bienvenido/a, {user.first_name or user.username}!')
            return redirect(request.GET.get('next') or 'core:home')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})


@login_required(login_url='accounts:login')
def profile(request):
    addresses = request.user.addresses.all()
    return render(request, 'accounts/profile.html', {'addresses': addresses})


@login_required(login_url='accounts:login')
def order_history(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'accounts/order_history.html', {'orders': orders})


@login_required(login_url='accounts:login')
def address_add(request):
    if request.method == 'POST':
        form = SavedAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, 'Dirección guardada.')
            return redirect('accounts:profile')
    else:
        form = SavedAddressForm()
    return render(request, 'accounts/address_form.html', {'form': form})


@login_required(login_url='accounts:login')
def address_edit(request, address_id):
    address = get_object_or_404(SavedAddress, id=address_id, user=request.user)
    if request.method == 'POST':
        form = SavedAddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dirección actualizada.')
            return redirect('accounts:profile')
    else:
        form = SavedAddressForm(instance=address)
    return render(request, 'accounts/address_form.html', {'form': form})


@login_required(login_url='accounts:login')
def address_delete(request, address_id):
    address = get_object_or_404(SavedAddress, id=address_id, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Dirección eliminada.')
        return redirect('accounts:profile')
    return render(request, 'accounts/address_confirm_delete.html', {'address': address})
