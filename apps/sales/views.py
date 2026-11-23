import uuid
from decimal import Decimal
from django.db.models import Exists, OuterRef, Count, Sum
from django.db import transaction
from django.http import request
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Combo, ComboItem, ExchangeRateLog, Product, Order, OrderItem, Sale, Expense, SaleReturn, SaleReturnItem
from apps.company.models import Company
from apps.accounts.models import AppUser
from apps.company.mixins import BasePermissionMixin  # Import the BasePermissionMixin
from django.http import JsonResponse
from apps.sales.models import Shift



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
            combo_name = combo.name
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

        # Cualquier venta (SOLD, RETURNED, CANCELLED) bloquea la re-venta
        any_sale = Sale.objects.filter(order=OuterRef("pk"))

        orders = (
            Order.objects
            .filter(company=company)
            .select_related("company")
            .annotate(is_sold=Exists(any_sale))   # ← nombre igual, lógica distinta
            .order_by("-created_at")
        )
        return render(request, "sales/order/index.html", {"orders": orders})

class CreateOrderView(BasePermissionMixin, View):
    permission_required = 'sales.add_order'

    def get(self, request):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        products = Product.objects.filter(company=company)
        combos = Combo.objects.filter(company=company)

        context = {
            'products': products,
            'combos': combos,
            'status_choices': Order.STATUS_CHOICES
        }
        return render(request, 'sales/order/create.html', context)

    def post(self, request):
        status = request.POST.get('status', 'PENDING')
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        customer_name = request.POST.get('customer')
        products = Product.objects.filter(company=company)
        combos = Combo.objects.filter(company=company)

        context = {
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
            # Calculamos el total iniciaL
            total_amount = 0
            for qty, prc in zip(quantities, prices):
                if qty and prc:
                    total_amount += int(qty) * float(prc)

            order = Order.objects.create(
                customer=customer_name,
                company=company,
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
        products = Product.objects.filter(company=company)
        combos = Combo.objects.filter(company=company)

        if order.status == "COMPLETED":
            return redirect('sales:order_list')
        context = {
            'order': order,
            'products': products,
            'combos': combos,
            'status_choices': Order.STATUS_CHOICES
        }
        return render(request, 'sales/order/edit.html', context)

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)
        status = request.POST.get('status')
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        customer_name = request.POST.get('customer')

        item_types = request.POST.getlist('item_types[]')
        item_ids = request.POST.getlist('item_ids[]')
        quantities = request.POST.getlist('quantities[]')
        prices = request.POST.getlist('prices[]')

        # ─── VALIDACIÓN: pedido no vacío ───
        if not item_ids:
            messages.error(request, "El pedido debe tener al menos un producto.")
            return redirect('sales:order_edit', order_id=order.id)

        try:
            order.customer = customer_name
            order.company = company
            order.status = status

            # Recreamos los ítems
            order.items.all().delete()

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
            messages.error(request, f"El pedido {order.folio_number} debe completarse antes de venderse.")
            return redirect("sales:order_list")

        if order.sales.exists():
            messages.info(
                request,
                f"El pedido {order.folio_number} ya tuvo una venta registrada. "
                f"Crea un pedido nuevo si necesitas revenderlo."
            )
            return redirect("sales:order_list")

        try:
            with transaction.atomic():
                Sale.objects.create(
                    order=order,
                    company=order.company,   # ← AGREGAR
                    total_amount=order.total_amount,
                    date_sale=timezone.now(),
                    created_by=request.user,
                )
            messages.success(request, f"Venta registrada para el pedido {order.folio_number}.")
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



from django.db.models import Sum, Q

class SaleListView(BasePermissionMixin, View):
    permission_required = 'sales.view_sale'

    def get(self, request):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)

        status_filter = request.GET.get('status', 'ALL')
        method_filter = request.GET.get('method', 'ALL')

        sales_qs = (
            Sale.objects
            .select_related('order', 'created_by')
            .filter(company=company)
            .order_by('-date_sale')
        )

        if status_filter in ('SOLD', 'RETURNED', 'CANCELLED', 'PENDING'):
            sales_qs = sales_qs.filter(status=status_filter)
        else:
            status_filter = 'ALL'

        if method_filter in ('CASH_MXN', 'CASH_USD', 'MIXED', 'TRANSFER'):
            sales_qs = sales_qs.filter(payment_method=method_filter)
        else:
            method_filter = 'ALL'

        # Conteos por estado
        counts_qs = (
            Sale.objects
            .filter(company=company)
            .values('status')
            .annotate(n=Count('id'))
        )
        counts = {row['status']: row['n'] for row in counts_qs}
        counts['ALL'] = sum(counts.values()) if counts else 0

        # Totales por método de pago (sobre el listado filtrado)
        totals = sales_qs.aggregate(
            total_mxn=Sum('paid_mxn'),
            total_usd=Sum('paid_usd'),
            total=Sum('total_amount'),
        )

        return render(request, 'sales/sales/sale_list.html', {
            'sales': sales_qs,
            'status_filter': status_filter,
            'method_filter': method_filter,
            'counts': counts,
            'totals': totals,
            'company': company,
        })


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
                company=company,   # ← AGREGAR
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

        expenses = (
            Expense.objects
            .filter(company=company)
            .select_related('company', 'created_by')
            .order_by('-date_expense')
        )

        return render(request, 'sales/expense/index.html', {
            'expenses': expenses,
            'type_choices': Expense.TYPE_CHOICES,
        })


class CreateExpenseView(BasePermissionMixin, View):
    permission_required = 'sales.add_expense'

    def get(self, request):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        return render(request, 'sales/expense/create.html', {
            'type_choices': Expense.TYPE_CHOICES,
        })

    def post(self, request):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)

        amount_raw = request.POST.get('amount') or 0
        description = request.POST.get('description', '')
        expense_type = request.POST.get('expense_type', 'OPERATIVE')
        date_expense = request.POST.get('date_expense')

        try:

            amount = Decimal(str(amount_raw))
            if amount <= 0:
                raise ValueError("El monto debe ser mayor a 0.")

            Expense.objects.create(
                amount=amount,
                description=description,
                status='APPROVED',
                expense_type=expense_type,
                company=company,
                date_expense=date_expense or timezone.now(),
                created_by=request.user,
            )

            messages.success(request, 'Gasto registrado correctamente.')
            return redirect('sales:expense_list')

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error al registrar el gasto: {e}')

        return redirect('sales:expense_create')


class UpdateExpenseView(BasePermissionMixin, View):
    permission_required = 'sales.change_expense'

    def get(self, request, expense_id):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        expense = get_object_or_404(Expense, id=expense_id, company=company)

        return render(request, 'sales/expense/edit.html', {
            'expense': expense,
            'type_choices': Expense.TYPE_CHOICES,
        })

    def post(self, request, expense_id):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        expense = get_object_or_404(Expense, id=expense_id, company=company)

        try:
            amount = Decimal(str(request.POST.get('amount') or 0))
            if amount <= 0:
                raise ValueError("El monto debe ser mayor a 0.")

            expense.amount = amount
            expense.description = request.POST.get('description', '')
            expense.expense_type = request.POST.get('expense_type', expense.expense_type)

            date_expense = request.POST.get('date_expense')
            if date_expense:
                expense.date_expense = date_expense

            expense.save()
            messages.success(request, 'Gasto actualizado correctamente.')

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error al actualizar: {e}')

        return redirect('sales:expense_list')


class DeleteExpenseView(BasePermissionMixin, View):
    permission_required = 'sales.delete_expense'

    def post(self, request, expense_id):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        expense = get_object_or_404(Expense, id=expense_id, company=company)

        try:
            expense.delete()
            messages.success(request, 'Gasto eliminado.')
        except Exception as e:
            messages.error(request, f'Error al eliminar: {e}')

        return redirect('sales:expense_list')



class SaleReturnListView(BasePermissionMixin, View):
    permission_required = "sales.view_salereturn"

    def get(self, request):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        returns = (
            SaleReturn.objects
            .filter(company=company)
            .select_related("sale", "order", "created_by")
            .prefetch_related("items__product")
            .order_by("-created_at")
        )
        return render(request, "sales/return/index.html", {"returns": returns})



class SaleReturnView(BasePermissionMixin, View):
    permission_required = "sales.change_sale"

    def post(self, request, sale_id):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        sale = get_object_or_404(Sale, id=sale_id, company=company)

        # Permitir devolución mientras la venta tenga items pendientes
        if sale.status == "CANCELLED":
            messages.error(request, "No se puede devolver una venta cancelada.")
            return redirect("sales:sale_list")

        item_ids = request.POST.getlist("item_ids[]")
        quantities = request.POST.getlist("quantities[]")
        reason = request.POST.get("reason", "").strip()

        if not item_ids:
            messages.error(request, "Debes seleccionar al menos un producto para devolver.")
            return redirect("sales:sale_list")

        try:
            with transaction.atomic():
                sale_return = SaleReturn.objects.create(
                    sale=sale,
                    order=sale.order,
                    company=company,
                    reason=reason,
                    created_by=request.user,
                )

                total_refunded = Decimal("0")
                items_devueltos = 0

                for item_id, qty_str in zip(item_ids, quantities):
                    order_item = OrderItem.objects.filter(id=item_id, order=sale.order).first()
                    if not order_item:
                        continue

                    try:
                        qty = int(qty_str or 0)
                    except (TypeError, ValueError):
                        continue

                    # Validar contra la cantidad DISPONIBLE (no la original)
                    if qty <= 0 or qty > order_item.available_quantity:
                        continue

                    unit_price = Decimal(str(order_item.price))
                    subtotal = unit_price * qty

                    SaleReturnItem.objects.create(
                        sale_return=sale_return,
                        order_item=order_item,
                        product=order_item.product,
                        quantity=qty,
                        unit_price=unit_price,
                        subtotal=subtotal,
                    )

                    total_refunded += subtotal
                    items_devueltos += 1

                if items_devueltos == 0:
                    # Nada válido que devolver → cancelar la SaleReturn
                    sale_return.delete()
                    messages.warning(request, "No se registró ninguna devolución válida.")
                    return redirect("sales:sale_list")

                sale_return.total_refunded = total_refunded
                sale_return.save(update_fields=["total_refunded"])

                # ─── ¿Se devolvió TODO? ───
                # Recalcular desde la BD (porque las propiedades cachean)
                todos_devueltos = all(
                    item.available_quantity <= 0
                    for item in sale.order.items.all()
                )

                # Si es devolución total → RETURNED
                # Si es parcial → sigue SOLD (se puede devolver más)
                sale.status = "RETURNED" if todos_devueltos else "SOLD"
                sale.total_amount = sale.total_amount - total_refunded   # ← RESTAR
                sale.save(update_fields=["total_amount", "status", "updated_at"])
            if todos_devueltos:
                messages.success(
                    request,
                    f"Devolución total registrada. {sale_return.folio_number} por ${total_refunded}."
                )
            else:
                messages.success(
                    request,
                    f"Devolución parcial registrada. {sale_return.folio_number} por ${total_refunded}. "
                    f"La venta sigue activa."
                )

        except Exception as e:
            messages.error(request, f"No se pudo registrar la devolución: {e}")

        return redirect("sales:sale_list")



class POSView(BasePermissionMixin, View):
    """Interfaz táctil de venta rápida."""
    permission_required = "sales.add_sale"

    def get(self, request):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)

        shift = Shift.objects.filter(company=company, status='OPEN').first()

        if shift is None:
            # No hay turno abierto → pedir fondo de caja
            return render(request, 'pos/start_shift.html', {'company': company})

        products = (
            Product.objects
            .filter(company=company)
            .select_related('category')
            .order_by('category__name', 'name')
        )
        combos = Combo.objects.filter(company=company).prefetch_related('items__product')

        # Categorías únicas para los tabs
        categories = (
            Product.objects
            .filter(company=company, category__isnull=False)
            .values_list('category__id', 'category__name')
            .distinct()
            .order_by('category__name')
        )

        return render(request, 'pos/index.html', {
            'company': company,
            'shift': shift,
            'products': products,
            'combos': combos,
            'categories': categories,
        })

    def post(self, request):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)

        shift = Shift.objects.filter(company=company, status='OPEN').first()
        if shift is None:
            messages.error(request, "No hay un turno abierto. Inicia el día primero.")
            return redirect("sales:pos")

        import json
        from decimal import Decimal

        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            payment_method = data.get('payment_method', 'CASH_MXN')
            paid_mxn_raw = Decimal(str(data.get('paid_mxn', 0) or 0))
            paid_usd_raw = Decimal(str(data.get('paid_usd', 0) or 0))
            customer = (data.get('customer') or '').strip() or 'Cliente general'
            exchange_rate = Decimal(str(company.usd_exchange_rate))

            if not items:
                return JsonResponse({'ok': False, 'error': 'El carrito está vacío.'}, status=400)

            if payment_method not in ('CASH_MXN', 'CASH_USD', 'MIXED', 'TRANSFER'):
                return JsonResponse({'ok': False, 'error': 'Método de pago inválido.'}, status=400)

            with transaction.atomic():
                # 1. Crear Order (COMPLETED) + OrderItems
                total = Decimal('0')
                order = Order.objects.create(
                    customer=customer,
                    status='COMPLETED',
                    company=company,
                    total_amount=0,
                    created_by=request.user,
                )

                for item in items:
                    item_type = item.get('type')
                    item_id = item.get('id')
                    qty = int(item.get('qty', 0))
                    price = Decimal(str(item.get('price', 0)))

                    if qty <= 0 or price < 0:
                        continue

                    product_obj = None
                    combo_obj = None

                    if item_type == 'product':
                        product_obj = Product.objects.filter(id=item_id, company=company).first()
                    elif item_type == 'combo':
                        combo_obj = Combo.objects.filter(id=item_id, company=company).first()

                    if not (product_obj or combo_obj):
                        continue

                    OrderItem.objects.create(
                        order=order,
                        product=product_obj,
                        combo=combo_obj,
                        quantity=qty,
                        price=price,
                    )
                    total += price * qty

                order.total_amount = total
                order.save(update_fields=['total_amount'])

                # 2. Calcular montos pagados según método
                if payment_method == 'CASH_MXN':
                    paid_mxn = paid_mxn_raw
                    paid_usd = Decimal('0')
                elif payment_method == 'CASH_USD':
                    paid_mxn = Decimal('0')
                    paid_usd = paid_usd_raw
                elif payment_method == 'MIXED':
                    paid_mxn = paid_mxn_raw
                    paid_usd = paid_usd_raw
                else:  # TRANSFER
                    paid_mxn = total
                    paid_usd = Decimal('0')

                # 3. Validar que el pago cubra el total
                paid_in_mxn = paid_mxn + (paid_usd * exchange_rate)
                if payment_method != 'TRANSFER' and paid_in_mxn < total:
                    return JsonResponse({
                        'ok': False,
                        'error': f'El pago (${paid_in_mxn}) es menor al total (${total}).'
                    }, status=400)

                # 4. Crear Sale con datos de pago
                sale = Sale.objects.create(
                    order=order,
                    company=company,
                    total_amount=total,
                    status='SOLD',
                    date_sale=timezone.now(),
                    payment_method=payment_method,
                    paid_mxn=paid_mxn,
                    paid_usd=paid_usd,
                    exchange_rate=exchange_rate,
                    created_by=request.user,
                )

            change = max(Decimal('0'), paid_in_mxn - total)

            return JsonResponse({
                'ok': True,
                'sale_folio': sale.folio_number,
                'total': str(total),
                'change': str(change),
                'paid_usd': str(paid_usd),
                'exchange_rate': str(exchange_rate),
            })

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=500)


class ShiftOpenView(BasePermissionMixin, View):
    """Abre un turno con fondo de caja inicial."""
    permission_required = "sales.add_sale"

    def post(self, request):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)

        if Shift.objects.filter(company=company, status='OPEN').exists():
            messages.info(request, "Ya hay un turno abierto.")
            return redirect("sales:pos")

        try:
            opening_cash = Decimal(str(request.POST.get('opening_cash') or 0))
            if opening_cash < 0:
                raise ValueError("El fondo de caja no puede ser negativo.")

            Shift.objects.create(
                company=company,
                opening_cash=opening_cash,
                opened_by=request.user,
            )
            messages.success(request, f"Turno abierto con fondo de ${opening_cash}.")
            return redirect("sales:pos")
        except Exception as e:
            messages.error(request, f"Error al abrir turno: {e}")
            return redirect("sales:pos")


class ShiftCloseView(BasePermissionMixin, View):
    """Cierra el turno y calcula la diferencia de efectivo."""
    permission_required = "sales.add_sale"

    def get(self, request):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        shift = Shift.objects.filter(company=company, status='OPEN').first()

        if shift is None:
            messages.error(request, "No hay turno abierto.")
            return redirect("sales:pos")

        # Calcular movimientos del turno
        ventas = Sale.objects.filter(
            company=company,
            status='SOLD',
            date_sale__gte=shift.opened_at,
        ).aggregate(t=Sum('total_amount'))['t'] or Decimal('0')

        devoluciones = SaleReturn.objects.filter(
            company=company,
            created_at__gte=shift.opened_at,
        ).aggregate(t=Sum('total_refunded'))['t'] or Decimal('0')

        gastos = Expense.objects.filter(
            company=company,
            date_expense__gte=shift.opened_at,
        ).aggregate(t=Sum('amount'))['t'] or Decimal('0')

        expected = shift.opening_cash + ventas - gastos   

        return render(request, 'pos/close_shift.html', {
            'shift': shift,
            'ventas': ventas,
            'devoluciones': devoluciones,
            'gastos': gastos,
            'expected': expected,
        })

    def post(self, request):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        shift = Shift.objects.filter(company=company, status='OPEN').first()

        if shift is None:
            messages.error(request, "No hay turno abierto.")
            return redirect("sales:pos")

        try:
            closing_cash = Decimal(str(request.POST.get('closing_cash') or 0))
            notes = request.POST.get('notes', '')

            # Recalcular esperado
            ventas = Sale.objects.filter(
                company=company, status='SOLD', date_sale__gte=shift.opened_at,
            ).aggregate(t=Sum('total_amount'))['t'] or Decimal('0')
            devoluciones = SaleReturn.objects.filter(
                company=company, created_at__gte=shift.opened_at,
            ).aggregate(t=Sum('total_refunded'))['t'] or Decimal('0')
            gastos = Expense.objects.filter(
                company=company, date_expense__gte=shift.opened_at,
            ).aggregate(t=Sum('amount'))['t'] or Decimal('0')

            expected = shift.opening_cash + ventas - gastos   
            difference = closing_cash - expected

            shift.status = 'CLOSED'
            shift.closing_cash = closing_cash
            shift.expected_cash = expected
            shift.difference = difference
            shift.notes = notes
            shift.closed_at = timezone.now()
            shift.closed_by = request.user
            shift.save()

            messages.success(request, f"Turno cerrado. Diferencia: ${difference}.")
            return redirect("dashboard")
        except Exception as e:
            messages.error(request, f"Error al cerrar turno: {e}")
            return redirect("sales:shift_close")



class ShiftListView(BasePermissionMixin, View):
    """Historial de turnos (cortes de caja)."""
    permission_required = "sales.view_shift"

    def get(self, request):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)

        shifts = (
            Shift.objects
            .filter(company=company)
            .select_related('opened_by', 'closed_by')
            .order_by('-opened_at')
        )

        # Resumen global
        total_shifts = shifts.count()
        abiertos = shifts.filter(status='OPEN').count()

        return render(request, 'pos/shift_list.html', {
            'shifts': shifts,
            'total_shifts': total_shifts,
            'abiertos': abiertos,
        })


class ShiftDetailView(BasePermissionMixin, View):
    """Detalle de un turno: ventas, gastos, devoluciones y cuadre."""
    permission_required = "sales.view_shift"

    def get(self, request, shift_id):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)
        shift = get_object_or_404(Shift, id=shift_id, company=company)

        # Ventas del turno
        ventas = (
            Sale.objects
            .filter(
                company=company,
                date_sale__gte=shift.opened_at,
                date_sale__lte=shift.closed_at or timezone.now(),
            )
            .select_related('order', 'created_by')
            .order_by('-date_sale')
        )

        # Gastos del turno
        gastos = (
            Expense.objects
            .filter(
                company=company,
                date_expense__gte=shift.opened_at,
                date_expense__lte=shift.closed_at or timezone.now(),
            )
            .order_by('-date_expense')
        )

        # Devoluciones del turno
        devoluciones = (
            SaleReturn.objects
            .filter(
                company=company,
                created_at__gte=shift.opened_at,
                created_at__lte=shift.closed_at or timezone.now(),
            )
            .select_related('sale', 'order')
            .order_by('-created_at')
        )

        total_ventas = ventas.aggregate(t=Sum('total_amount'))['t'] or Decimal('0')
        total_gastos = gastos.aggregate(t=Sum('amount'))['t'] or Decimal('0')
        total_devoluciones = devoluciones.aggregate(t=Sum('total_refunded'))['t'] or Decimal('0')

        return render(request, 'pos/shift_detail.html', {
            'shift': shift,
            'ventas': ventas,
            'gastos': gastos,
            'devoluciones': devoluciones,
            'total_ventas': total_ventas,
            'total_gastos': total_gastos,
            'total_devoluciones': total_devoluciones,
        })


class ExchangeRateUpdateView(BasePermissionMixin, View):
    """Formulario para editar el tipo de cambio USD→MXN de la empresa activa."""
    permission_required = "company.change_company"

    def get(self, request):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)

        logs = (
            ExchangeRateLog.objects
            .filter(company=company)
            .select_related('changed_by')
            .order_by('-changed_at')[:20]
        )

        return render(request, 'config/exchange_rate.html', {
            'company': company,
            'logs': logs,
        })

    def post(self, request):
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.get(selected=True, owner=owner)

        try:
            new_rate = Decimal(str(request.POST.get('exchange_rate') or 0))
            if new_rate <= 0:
                raise ValueError("El tipo de cambio debe ser mayor a 0.")

            old_rate = company.usd_exchange_rate

            if new_rate == old_rate:
                messages.info(request, "El tipo de cambio no cambió.")
                return redirect('sales:exchange_rate')

            company.usd_exchange_rate = new_rate
            company.save(update_fields=['usd_exchange_rate', 'date_updated'])

            ExchangeRateLog.objects.create(
                company=company,
                old_rate=old_rate,
                new_rate=new_rate,
                changed_by=request.user,
                notes=request.POST.get('notes', '')[:255],
            )

            messages.success(
                request,
                f"Tipo de cambio actualizado: ${old_rate} → ${new_rate} MXN/USD."
            )
            return redirect('sales:exchange_rate')

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"Error al actualizar TC: {e}")

        return redirect('sales:exchange_rate')



