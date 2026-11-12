import uuid
from django.db.models import Exists, OuterRef
from django.db import transaction
from django.http import request
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Combo, ComboItem, Product, Order, OrderItem, Currency, Sale, Expense
from apps.company.models import Company
from apps.accounts.models import AppUser
from apps.company.mixins import BasePermissionMixin  # Import the BasePermissionMixin

class ComboListView(BasePermissionMixin, View):
    permission_required = 'sales.view_combo'

    def get(self, request):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        combos = Combo.objects.select_related('company', 'created_by').prefetch_related('items__product').filter(company=company)
        return render(request, 'sales/combo/index.html', {'combos': combos})

class CreateComboView(BasePermissionMixin, View):
    permission_required = 'sales.add_combo'

    def get(self, request):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        products = Product.objects.filter(company=company)
        context = {
            'products': products
        }
        return render(request, 'sales/combo/create.html', context)

    def post(self, request):
        name = request.POST.get('name')
        description = request.POST.get('description')
        owner = AppUser.objects.get(id=request.user.id) 
        company = Company.objects.get(selected=True, owner=owner)
        products = Product.objects.filter(company=company)
        context = {
            'name': name,
            'description': description,
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

class UpdateComboView(BasePermissionMixin, View):
    permission_required = 'sales.change_combo'

    def get(self, request, combo_id):
        combo = get_object_or_404(Combo.objects.prefetch_related('items__product'), id=combo_id)
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        products = Product.objects.filter(company=company)
        context = {
            'combo': combo,
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

class DeleteComboView(BasePermissionMixin, View):
    permission_required = 'sales.delete_combo'

    def post(self, request, combo_id):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        combo = get_object_or_404(Combo, id=combo_id,company=company)
        try:
            combo_name = combo.namee
            combo.delete()
            messages.success(request, f'El combo "{combo_name}" fue eliminado correctamente.')
        except Exception as e:
            messages.error(request, 'No se pudo eliminar el combo.')
        return redirect('sales:combo_list')



class OrderListView(BasePermissionMixin, View):
    permission_required = "sales.view_order"

    def get(self, request):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        sold_sales = Sale.objects.filter(order=OuterRef("pk"),status="SOLD")
        orders = (Order.objects.filter(company=company).select_related("company", "currency").annotate(is_sold=Exists(sold_sales)))
        return render(request, "sales/order/index.html", {"orders": orders})


class CreateOrderView(BasePermissionMixin, View):
    permission_required = 'sales.add_order'

    def get(self, request):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        currencies = Currency.objects.filter(company=company)
        products = Product.objects.filter(company=company)
        combos = Combo.objects.filter(company=company)

        context = {
            'currencies': currencies,
            'products': products,
            'combos': combos,
            'status_choices': Order.STATUS_CHOICES
        }
        return render(request, 'sales/order/create.html', context)

    def post(self, request):
        currency_id = request.POST.get('currency')
        status = request.POST.get('status', 'PENDING')
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        customer_name = request.POST.get('customer')
        currencies = Currency.objects.filter(company=company)
        products = Product.objects.filter(company=company)
        combos = Combo.objects.filter(company=company)

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


class UpdateOrderView(BasePermissionMixin, View):
    permission_required = 'sales.change_order'

    def get(self, request, order_id):
        order = get_object_or_404(Order.objects.prefetch_related('items__product', 'items__combo'), id=order_id)
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        currencies = Currency.objects.filter(company=company)
        products = Product.objects.filter(company=company)
        combos = Combo.objects.filter(company=company)

        if order.status == "COMPLETED":
            return redirect('sales:order_list')
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
        currency_id = request.POST.get('currency')
        status = request.POST.get('status')
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
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



class OrderCompleteView(BasePermissionMixin, View):
    permission_required = "sales.change_order"

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        if order.status == "COMPLETED":
            messages.info(request, f"El pedido {order.folio_number} ya estaba completado.")
        elif order.status == "CANCELLED":
            messages.warning(request, f"El pedido {order.folio_number} está cancelado y no se puede completar.")
        else:
            order.status = "COMPLETED"
            order.save(update_fields=["status", "updated_at"])
            messages.success(request, f"Pedido {order.folio_number} marcado como completado.")
        return redirect("sales:order_list")



class OrderSellView(BasePermissionMixin, View):
    permission_required = "sales.add_sale"

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)

        if order.status != "COMPLETED":
            messages.error(
                request,
                f"El pedido {order.folio_number} debe completarse antes de venderse.",
            )
            return redirect("sales:order_list")

        if order.sales.exists():
            messages.info(
                request,
                f"El pedido {order.folio_number} ya tiene una venta registrada.",
            )
            return redirect("sales:order_list")

        try:
            with transaction.atomic():
                Sale.objects.create(
                    order=order,
                    total_amount=order.total_amount,
                    date_sale=timezone.now(),
                    created_by=request.user,
                )
            messages.success(
                request,
                f"Venta registrada para el pedido {order.folio_number}.",
            )
        except Exception as e:
            messages.error(request, f"No se pudo registrar la venta: {e}")

        return redirect("sales:order_list")


class DeleteOrderView(BasePermissionMixin, View):
    permission_required = 'sales.delete_order'

    def post(self, request, order_id):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        order = get_object_or_404(Order, id=order_id, company=company)
        if order.status == "COMPLETED":
            return redirect('sales:order_list')
        try:
            folio = order.folio_number
            order.status = 'CANCELLED' 
            order.save()
            messages.success(request, f'El pedido "{folio}" fue eliminado correctamente.')
        except Exception as e:
            messages.error(request, 'No se pudo eliminar el pedido.')
        return redirect('sales:order_list')



class SaleListView(BasePermissionMixin, View):
    permission_required = 'sales.view_sale'

    def get(self, request):
        sales = Sale.objects.select_related('order', 'created_by').filter().order_by('-date_sale')
        return render(request, 'sales/sales/sale_list.html', {'sales': sales})


class CreateSaleView(BasePermissionMixin, View):
    permission_required = 'sales.add_sale'

    def get(self, request):
        # Solo mostramos órdenes que aún no tengan una venta asociada o todas las disponibles
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        orders = Order.objects.filter(sales__isnull=True, company=company).order_by('-created_at')
        context = {
            'orders': orders,
            'status_choices': Sale.STATUS_CHOICES
        }
        return render(request, 'sales/sales/create.html', context)

    def post(self, request):
        order_id = request.POST.get('order')
        total_amount = request.POST.get('total_amount')
        date_sale = request.POST.get('date_sale')

        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        orders = Order.objects.filter(sales__isnull=True, company=company).order_by('-created_at')
        context = {
            'orders': orders,
            'status_choices': Sale.STATUS_CHOICES,
            'order_id': order_id,
            'total_amount': total_amount,
            'date_sale': date_sale
        }

        if not order_id or not total_amount:
            messages.error(request, 'Debe seleccionar un pedido y especificar el monto total.')
            return render(request, 'sales/sales/create.html', context)

        try:
            order_obj = get_object_or_404(Order, id=order_id, company=company)
            folio = f"SALE-{uuid.uuid4().hex[:8].upper()}"

            Sale.objects.create(
                folio_number=folio,
                order=order_obj,
                total_amount=total_amount,
                date_sale=date_sale if date_sale else timezone.now(),
                created_by=request.user if request.user.is_authenticated else None
            )

            messages.success(request, f'Venta {folio} registrada exitosamente.')
            return redirect('sales:sale_list')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al registrar la venta: {e}')
            return render(request, 'sales/sales/create.html', context)


class UpdateSaleView(BasePermissionMixin, View):
    permission_required = 'sales.change_sale'

    def get(self, request, sale_id):
        sale = get_object_or_404(Sale, id=sale_id)
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        orders = Order.objects.filter(company=company)
        context = {
            'sale': sale,
            'orders': orders,
            'status_choices': Sale.STATUS_CHOICES
        }
        return render(request, 'sales/sales/edit.html', context)

    def post(self, request, sale_id):
        sale = get_object_or_404(Sale, id=sale_id)
        order_id = request.POST.get('order')
        total_amount = request.POST.get('total_amount')
        date_sale = request.POST.get('date_sale')

        if not order_id or not total_amount:
            messages.error(request, 'El pedido y el monto son obligatorios.')
            return redirect('sales:sale_edit', sale_id=sale.id)

        try:
            sale.order = get_object_or_404(Order, id=order_id)
            sale.total_amount = total_amount
            if date_sale:
                sale.date_sale = date_sale
            sale.save()

            messages.success(request, f'Venta {sale.folio_number} actualizada correctamente.')
            return redirect('sales:sale_list')
        except Exception as e:
            messages.error(request, f'Error al actualizar la venta: {e}')
            return redirect('sales:sale_edit', sale_id=sale.id)


class DeleteSaleView(BasePermissionMixin, View):
    permission_required = 'sales.delete_sale'

    def post(self, request, sale_id):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        sale = get_object_or_404(Sale, id=sale_id, company=company)
        try:
            folio = sale.folio_number
            sale.delete()
            messages.success(request, f'La venta "{folio}" fue eliminada correctamente.')
        except Exception as e:
            messages.error(request, 'No se pudo eliminar la venta.')
        return redirect('sales:sale_list')


class ExpenseListView(BasePermissionMixin, View):
    permission_required = 'sales.view_expense'

    def get(self, request):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        expenses = Expense.objects.select_related('company', 'currency', 'created_by').filter(company=company).order_by('-date_expense')
        return render(request, 'sales/expense/index.html', {'expenses': expenses})


class CreateExpenseView(BasePermissionMixin, View):
    permission_required = 'sales.add_expense'

    def get(self, request):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        currencies = Currency.objects.filter(company=company)
        context = {
            'currencies': currencies,
            'status_choices': Expense.STATUS_CHOICES
        }
        return render(request, 'sales/expense/create.html', context)

    def post(self, request):
        amount = request.POST.get('amount')
        currency_id = request.POST.get('currency')
        description = request.POST.get('description')
        status = request.POST.get('status', 'PENDING')
        date_expense = request.POST.get('date_expense')  #   Assuming the logged-in user is the owner of the company
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)   
        currencies = Currency.objects.filter(company=company)

        context = {
            'amount': amount,
            'currency_id': currency_id,
            'description': description,
            'status': status,
            'date_expense': date_expense,
            'currencies': currencies,
            'status_choices': Expense.STATUS_CHOICES
        }

        try:
            currency_obj = Currency.objects.filter(id=currency_id).first() if currency_id else None

            Expense.objects.create(
                amount=amount,
                currency=currency_obj,
                description=description,
                status=status,
                company=company,
                date_expense=date_expense if date_expense else timezone.now(),
                created_by=request.user if request.user.is_authenticated else None
            )

            messages.success(request, 'Gasto registrado exitosamente.')
            return redirect('sales:expense_list')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al registrar el gasto: {e}')
            return render(request, 'sales/expense/create.html', context)


class UpdateExpenseView(BasePermissionMixin, View):
    permission_required = 'sales.change_expense'

    def get(self, request, expense_id):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        expense = get_object_or_404(Expense, id=expense_id)
        currencies = Currency.objects.filter(company=company)
        context = {
            'expense': expense,
            'currencies': currencies,
            'status_choices': Expense.STATUS_CHOICES
        }
        return render(request, 'sales/expense/edit.html', context)

    def post(self, request, expense_id):
        expense = get_object_or_404(Expense, id=expense_id)
        amount = request.POST.get('amount')
        currency_id = request.POST.get('currency')
        description = request.POST.get('description')
        status = request.POST.get('status')
        date_expense = request.POST.get('date_expense')

        try:
            expense.amount = amount
            expense.currency = Currency.objects.filter(id=currency_id).first() if currency_id else None
            expense.description = description
            expense.status = status
            if date_expense:
                expense.date_expense = date_expense
            expense.save()

            messages.success(request, 'Gasto actualizado correctamente.')
            return redirect('sales:expense_list')
        except Exception as e:
            messages.error(request, f'Error al actualizar el gasto: {e}')
            return redirect('sales:expense_edit', expense_id=expense.id)


class DeleteExpenseView(BasePermissionMixin, View):
    permission_required = 'sales.delete_expense'

    def post(self, request, expense_id):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        expense = get_object_or_404(Expense, id=expense_id, company=company)
        try:
            expense.delete()
            messages.success(request, 'El gasto fue eliminado correctamente.')
        except Exception as e:
            messages.error(request, 'No se pudo eliminar el gasto.')
        return redirect('sales:expense_list')



