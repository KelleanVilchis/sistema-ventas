import uuid
from django.http import request
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Combo, ComboItem, Product, Order, OrderItem, Currency
from apps.company.models import Company
from apps.accounts.models import AppUser

class ComboListView(LoginRequiredMixin, View):
    def get(self, request):
        combos = Combo.objects.select_related('company', 'created_by').prefetch_related('items__product').all()
        return render(request, 'sales/combo/index.html', {'combos': combos})

class CreateComboView(LoginRequiredMixin, View):
    def get(self, request):
        companies = Company.objects.all()
        products = Product.objects.all()
        context = {
            'companies': companies,
            'products': products
        }
        return render(request, 'sales/combo/create.html', context)

    def post(self, request):
        name = request.POST.get('name')
        description = request.POST.get('description')
        owner = AppUser.objects.get(id=request.user.id) 
        company = Company.objects.get(owner=owner)
        companies = Company.objects.all()
        products = Product.objects.all()
        context = {
            'name': name,
            'description': description,
            'companies': companies,
            'products': products
        }

        if not name :
            messages.error(request, 'El nombre del combo es obligatorio.')
            return render(request, 'sales/combo/create.html', context)

        try:
            
            
            combo = Combo.objects.create(
                name=name,
                description=description,
                company=company,
                created_by=request.user if request.user.is_authenticated else None
            )

            # Procesamiento de productos seleccionados para el combo (si se envían desde un form dinámico)
            product_ids = request.POST.getlist('products[]')
            quantities = request.POST.getlist('quantities[]')

            for p_id, qty in zip(product_ids, quantities):
                if p_id and qty and int(qty) > 0:
                    product_obj = Product.objects.filter(id=p_id).first()
                    if product_obj:
                        ComboItem.objects.create(
                            combo=combo,
                            product=product_obj,
                            quantity=int(qty),
                            created_by=request.user if request.user.is_authenticated else None
                        )

            messages.success(request, 'Combo creado exitosamente.')
            return redirect('sales:combo_list')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al crear el combo: {e}')
            return render(request, 'sales/combo/create.html', context)

class UpdateComboView(LoginRequiredMixin, View):
    def get(self, request, combo_id):
        combo = get_object_or_404(Combo.objects.prefetch_related('items__product'), id=combo_id)
        companies = Company.objects.all()
        products = Product.objects.all()
        context = {
            'combo': combo,
            'companies': companies,
            'products': products
        }
        return render(request, 'sales/combo/edit.html', context)

    def post(self, request, combo_id):
        combo = get_object_or_404(Combo, id=combo_id)
        name = request.POST.get('name')
        description = request.POST.get('description')
        

        if not name :
            messages.error(request, 'El nombre es obligatorio.')
            return redirect('sales:combo_edit', combo_id=combo.id)

        try:
            combo.name = name
            combo.description = description
            combo.save()

            # Actualizamos los items: eliminamos los anteriores y recreamos los nuevos enviados
            combo.items.all().delete()
            product_ids = request.POST.getlist('products[]')
            quantities = request.POST.getlist('quantities[]')

            for p_id, qty in zip(product_ids, quantities):
                if p_id and qty and int(qty) > 0:
                    product_obj = Product.objects.filter(id=p_id).first()
                    if product_obj:
                        ComboItem.objects.create(
                            combo=combo,
                            product=product_obj,
                            quantity=int(qty),
                            created_by=request.user if request.user.is_authenticated else None
                        )

            messages.success(request, 'Combo actualizado correctamente.')
            return redirect('sales:combo_list')
        except Exception as e:
            messages.error(request, f'Error al actualizar el combo: {e}')
            return redirect('sales:combo_edit', combo_id=combo.id)

class DeleteComboView(LoginRequiredMixin, View):
    def post(self, request, combo_id):
        combo = get_object_or_404(Combo, id=combo_id)
        try:
            combo_name = combo.name
            combo.delete()
            messages.success(request, f'El combo "{combo_name}" fue eliminado correctamente.')
        except Exception as e:
            messages.error(request, 'No se pudo eliminar el combo.')
        return redirect('sales:combo_list')



class OrderListView(LoginRequiredMixin, View):
    def get(self, request):
        orders = Order.objects.all()
        return render(request, 'sales/order/index.html', {'orders': orders})


class CreateOrderView(LoginRequiredMixin, View):
    def get(self, request):
        customers = AppUser.objects.all()
        companies = Company.objects.all()
        currencies = Currency.objects.all()
        products = Product.objects.all()
        combos = Combo.objects.all()

        context = {
            'customers': customers,
            'companies': companies,
            'currencies': currencies,
            'products': products,
            'combos': combos,
            'status_choices': Order.STATUS_CHOICES
        }
        return render(request, 'sales/order/create.html', context)

    def post(self, request):
        currency_id = request.POST.get('currency')
        status = request.POST.get('status', 'PENDING')
        owner = AppUser.objects.get(id=request.user.id)  #   Assuming the logged-in user is the owner of the company
        company = Company.objects.get(owner=owner)
        customer_name = request.POST.get('customer')
        currencies = Currency.objects.all()
        products = Product.objects.all()
        combos = Combo.objects.all()

        context = {
            'currencies': currencies,
            'products': products,
            'combos': combos,
            'status_choices': Order.STATUS_CHOICES
        }
        item_types = request.POST.getlist('item_types[]')
        item_ids = request.POST.getlist('item_ids[]')
        quantities = request.POST.getlist('quantities[]')
        prices = request.POST.getlist('prices[]')

        if not item_ids or len(item_ids) == 0:
            messages.error(request, 'Debe incluir al menos un producto o combo en el pedido.')
            return render(request, 'sales/order/create.html', context)

        try:
            currency_obj = Currency.objects.filter(id=currency_id).first() if currency_id else None
            
            folio = f"ORD-{uuid.uuid4().hex[:8].upper()}"

            # Calculamos el total iniciaL
            total_amount = 0
            for qty, prc in zip(quantities, prices):
                if qty and prc:
                    total_amount += int(qty) * float(prc)

            order = Order.objects.create(
                folio_number=folio,
                customer=customer_name,
                company=company,
                currency=currency_obj,
                status=status,
                total_amount=total_amount,
                created_by=request.user if request.user.is_authenticated else None
            )

            # Creamos los items del pedido
            for item_type, item_id, qty, prc in zip(item_types, item_ids, quantities, prices):
                if item_id and qty and prc:
                    product_obj = None
                    combo_obj = None

                    if item_type == 'PRODUCT':
                        product_obj = Product.objects.filter(id=item_id).first()
                    elif item_type == 'COMBO':
                        combo_obj = Combo.objects.filter(id=item_id).first()

                    if product_obj or combo_obj:
                        OrderItem.objects.create(
                            order=order,
                            product=product_obj,
                            combo=combo_obj,
                            quantity=int(qty),
                            price=float(prc)
                        )

            messages.success(request, f'Pedido {order.folio_number} registrado correctamente.')
            return redirect('sales:order_list')

        except Exception as e:
            messages.error(request, f'Ocurrió un error al crear el pedido: {e}')
            return render(request, 'sales/order/create.html', context)


class UpdateOrderView(LoginRequiredMixin, View):
    def get(self, request, order_id):
        order = get_object_or_404(Order.objects.prefetch_related('items__product', 'items__combo'), id=order_id)
        currencies = Currency.objects.all()
        products = Product.objects.all()
        combos = Combo.objects.all()

        context = {
            'order': order,
            'currencies': currencies,
            'products': products,
            'combos': combos,
            'status_choices': Order.STATUS_CHOICES
        }
        return render(request, 'sales/order/edit.html', context)

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        customer_id = request.POST.get('customer')
        company_id = request.POST.get('company')
        currency_id = request.POST.get('currency')
        status = request.POST.get('status')
        owner = AppUser.objects.get(id=request.user.id)  #   Assuming the logged-in user is the owner of the company
        company = Company.objects.get(owner=owner)
        customer_name = request.POST.get('customer')

        try:
            order.customer = customer_name
            order.company = company
            order.currency = Currency.objects.filter(id=currency_id).first() if currency_id else None
            order.status = status

            # Recreamos los ítems
            order.items.all().delete()
            
            item_types = request.POST.getlist('item_types[]')
            item_ids = request.POST.getlist('item_ids[]')
            quantities = request.POST.getlist('quantities[]')
            prices = request.POST.getlist('prices[]')

            total_amount = 0
            for item_type, item_id, qty, prc in zip(item_types, item_ids, quantities, prices):
                if item_id and qty and prc:
                    product_obj = None
                    combo_obj = None

                    if item_type == 'PRODUCT':
                        product_obj = Product.objects.filter(id=item_id).first()
                    elif item_type == 'COMBO':
                        combo_obj = Combo.objects.filter(id=item_id).first()

                    if product_obj or combo_obj:
                        item_total = int(qty) * float(prc)
                        total_amount += item_total
                        OrderItem.objects.create(
                            order=order,
                            product=product_obj,
                            combo=combo_obj,
                            quantity=int(qty),
                            price=float(prc)
                        )

            order.total_amount = total_amount
            order.save()

            messages.success(request, f'Pedido {order.folio_number} actualizado exitosamente.')
            return redirect('sales:order_list')

        except Exception as e:
            messages.error(request, f'Ocurrió un error al actualizar el pedido: {e}')
            return redirect('sales:order_edit', order_id=order.id)


class DeleteOrderView(LoginRequiredMixin, View):
    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        try:
            folio = order.folio_number
            order.delete()
            messages.success(request, f'El pedido "{folio}" fue eliminado correctamente.')
        except Exception as e:
            messages.error(request, 'No se pudo eliminar el pedido.')
        return redirect('sales:order_list')