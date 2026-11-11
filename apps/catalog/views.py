from django.http import request
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Currency, ProductCategory, Product
from apps.company.models import Company  # Assuming you have a Company model in the company app
from apps.accounts.models import AppUser  # Assuming you have an AppUser model in the accounts app
import random
import string
from apps.company.mixins import BasePermissionMixin  # Import the BasePermissionMixin

class CurrencyListView(BasePermissionMixin, View):
    permission_required = 'catalog.view_currency'

    def get(self, request):
        company = Company.objects.get(selected=True)
        currencies = Currency.objects.filter(company=company)
        return render(request, 'catalog/currency/index.html', {'currencies': currencies})


class CreateCurrencyView(BasePermissionMixin, View):
    permission_required = 'catalog.add_currency'

    def get(self, request):
        return render(request, 'catalog/currency/create.html')

    def post(self, request):
        name = request.POST.get('name')
        code = request.POST.get('code')
        company = Company.objects.get(selected=True)  # Assuming the user is the owner of the company
        context = {'name': name, 'code': code}

        if not name or not code:
            messages.error(request, 'Por favor, completa todos los campos obligatorios.')
            return render(request, 'catalog/currency/create.html', context)

        try:
            Currency.objects.create(
                name=name,
                code=code,
                company=company,
                created_by=request.user if request.user.is_authenticated else None
            )
            messages.success(request, 'Moneda creada exitosamente.')
            return redirect('catalog:currency_list')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al crear la moneda: {e}')
            return render(request, 'catalog/currency/create.html', context)


class UpdateCurrencyView(BasePermissionMixin, View):
    permission_required = 'catalog.change_currency'

    def get(self, request, currency_id):
        user = AppUser.objects.get(id=request.user.id)
        currency = get_object_or_404(Currency, id=currency_id, created_by=user)
        return render(request, 'catalog/currency/edit.html', {'currency': currency})

    def post(self, request, currency_id):
        user = AppUser.objects.get(id=request.user.id)
        currency = get_object_or_404(Currency, id=currency_id, created_by=user)
        name = request.POST.get('name')
        code = request.POST.get('code')

        context = {'currency': currency}

        if not name or not code:
            messages.error(request, 'Por favor, completa todos los campos obligatorios.')
            return render(request, 'catalog/currency/edit.html', context)

        try:
            currency.name = name
            currency.code = code
            currency.save()
            messages.success(request, 'Moneda actualizada exitosamente.')
            return redirect('catalog:currency_list')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al actualizar: {e}')
            return render(request, 'catalog/currency/edit.html', context)


class DeleteCurrencyView(BasePermissionMixin, View):
    permission_required = 'catalog.delete_currency'

    def post(self, request, currency_id):
        user = AppUser.objects.get(id=request.user.id)
        currency = get_object_or_404(Currency, id=currency_id, created_by=user)
        try:
            currency_name = currency.name
            currency.delete()
            messages.success(request, f'La moneda "{currency_name}" ha sido eliminada correctamente.')
        except Exception as e:
            messages.error(request, 'No se pudo eliminar la moneda. Es posible que esté asignada a productos activos.')
        return redirect('catalog:currency_list')


class ProductCategoryListView(BasePermissionMixin, View):
    permission_required = 'catalog.view_productcategory'

    def get(self, request):
        company = Company.objects.get(selected=True)
        categories = ProductCategory.objects.filter(company=company)
        return render(request, 'catalog/product_category/index.html', {'categories': categories})


class CreateProductCategoryView(BasePermissionMixin, View):
    permission_required = 'catalog.add_productcategory'

    def get(self, request):
        return render(request, 'catalog/product_category/create.html')

    def post(self, request):
        name = request.POST.get('name')
        description = request.POST.get('description')
        company = Company.objects.get(selected=True)  # Assuming the user is the owner of the company
        context = {'name': name, 'description': description}

        if not name:
            messages.error(request, 'El nombre de la categoría es obligatorio.')
            return render(request, 'catalog/product_category/create.html', context)

        try:
            ProductCategory.objects.create(
                name=name,
                description=description,
                company=company,
                created_by=request.user if request.user.is_authenticated else None
            )
            messages.success(request, 'Categoría creada exitosamente.')
            return redirect('catalog:category_list')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al crear la categoría: {e}')
            return render(request, 'catalog/product_category/create.html', context)


class UpdateProductCategoryView(BasePermissionMixin, View):
    permission_required = 'catalog.change_productcategory'

    def get(self, request, category_id):
        user = AppUser.objects.get(id=request.user.id)
        category = get_object_or_404(ProductCategory, id=category_id, created_by=user)
        return render(request, 'catalog/product_category/edit.html', {'category': category})

    def post(self, request, category_id):
        user = AppUser.objects.get(id=request.user.id)
        category = get_object_or_404(ProductCategory, id=category_id, created_by=user)
        name = request.POST.get('name')
        description = request.POST.get('description')

        context = {'category': category}

        if not name:
            messages.error(request, 'El nombre de la categoría es obligatorio.')
            return render(request, 'catalog/product_category/edit.html', context)

        try:
            category.name = name
            category.description = description
            category.save()
            messages.success(request, 'Categoría actualizada exitosamente.')
            return redirect('catalog:category_list')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al actualizar: {e}')
            return render(request, 'catalog/product_category/edit.html', context)


class DeleteProductCategoryView(BasePermissionMixin, View):
    permission_required = 'catalog.delete_productcategory'

    def post(self, request, category_id):
        user = AppUser.objects.get(id=request.user.id)
        category = get_object_or_404(ProductCategory, id=category_id, created_by=user)
        try:
            category_name = category.name
            category.delete()
            messages.success(request, f'La categoría "{category_name}" ha sido eliminada correctamente.')
        except Exception as e:
            messages.error(request, 'No se pudo eliminar la categoría. Es posible que tenga productos asociados.')
        return redirect('catalog:category_list')


class ProductListView(BasePermissionMixin, View):
    permission_required = 'catalog.view_product'

    def get(self, request):
        company = (
            Company.objects
            .filter(owner=request.user, selected=True)
            .first()
        )

        if company is None:
            messages.warning(
                request,
                "No tienes una empresa seleccionada. Selecciona una para continuar.",
            )
            return redirect("company:company_list")

        products = Product.objects.filter(company=company).select_related("company")

        return render(
            request,
            "catalog/product/index.html",
            {"products": products, "company": company},
        )

def random_sku(company, length=8):
    company = Company.objects.get(id=company.id)
    prefix = company.name[:3].upper() if company.name else "PRD"
    digits = ''.join(random.choices(string.digits, k=length))
    return f"{prefix}-{digits}"


class CreateProductView(BasePermissionMixin, View):
    permission_required = 'catalog.add_product'

    def get(self, request):
        owner = AppUser.objects.get(id=request.user.id)  
        company = Company.objects.get(selected=True, owner=owner)
        categories = ProductCategory.objects.filter(company=company)
        currencies = Currency.objects.filter(company=company)
        
        context = {
            'categories': categories,
            'currencies': currencies,
            'sku_code': random_sku(company),
        }
        return render(request, 'catalog/product/create.html', context)

    def post(self, request):
        sku = request.POST.get('sku')
        name = request.POST.get('name')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        purchase_price = request.POST.get('purchase_price')
        sale_price = request.POST.get('sale_price')
        currency_id = request.POST.get('currency')
        company = Company.objects.get(selected=True)  # Assuming the user is the owner of the company
        categories = ProductCategory.objects.filter(company=company)
        currencies = Currency.objects.filter(company=company)
        context = {
            'sku': sku,
            'name': name,
            'description': description,
            'category_id': category_id,
            'purchase_price': purchase_price,
            'sale_price': sale_price,
            'currency_id': currency_id,
            'categories': categories,
            'currencies': currencies,
        }

        if not sku or not name or not purchase_price or not sale_price:
            messages.error(request, 'Por favor, completa los campos obligatorios (SKU, Nombre y Precios).')
            return render(request, 'catalog/product/create.html', context)

        if Product.objects.filter(sku=sku).exists():
            messages.error(request, f'El SKU "{sku}" ya se encuentra registrado.')
            return render(request, 'catalog/product/create.html', context)

        try:
            category_obj = ProductCategory.objects.filter(id=category_id).first() if category_id else None
            currency_obj = Currency.objects.filter(id=currency_id).first() if currency_id else None

            Product.objects.create(
                sku=sku,
                name=name,
                description=description,
                company=company,
                status=Product.Status.ACTIVE,
                category=category_obj,
                purchase_price=purchase_price,
                sale_price=sale_price,
                currency=currency_obj,
                created_by=request.user if request.user.is_authenticated else None
            )
            messages.success(request, 'Producto creado exitosamente.')
            return redirect('catalog:product_list')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al registrar el producto: {e}')
            return render(request, 'catalog/product/create.html', context)


class ProductToggleStatusView(BasePermissionMixin, View):
    permission_required = "catalog.change_product"

    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)

        if product.status == Product.Status.ACTIVE:
            product.status = Product.Status.INACTIVE
            messages.success(request, f"Producto '{product.name}' dado de baja.")
        else:
            product.status = Product.Status.ACTIVE
            messages.success(request, f"Producto '{product.name}' reactivado.")

        product.save(update_fields=["status", "date_updated"])
        return redirect("catalog:product_list")


class UpdateProductView(BasePermissionMixin, View):
    permission_required = 'catalog.change_product'

    def get(self, request, product_id):
        user = AppUser.objects.get(id=request.user.id)
        product = get_object_or_404(Product, id=product_id, created_by=user)
        categories = ProductCategory.objects.filter(created_by=user)
        currencies = Currency.objects.filter(created_by=user)
        context = {
            'product': product,
            'categories': categories,
            'currencies': currencies,
        }
        return render(request, 'catalog/product/edit.html', context)

    def post(self, request, product_id):
        user = AppUser.objects.get(id=request.user.id)
        product = get_object_or_404(Product, id=product_id, created_by=user)
        sku = request.POST.get('sku')
        name = request.POST.get('name')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        purchase_price = request.POST.get('purchase_price')
        sale_price = request.POST.get('sale_price')
        currency_id = request.POST.get('currency')

        company = Company.objects.get(selected=True)
        categories = ProductCategory.objects.filter(company=company)
        currencies = Currency.objects.filter(company=company)

        context = {
            'product': product,
            'categories': categories,
            'currencies': currencies,
        }

        if not sku or not name or not purchase_price or not sale_price:
            messages.error(request, 'Por favor, completa los campos obligatorios.')
            return render(request, 'catalog/product/edit.html', context)

        if Product.objects.filter(sku=sku).exclude(id=product.id).exists():
            messages.error(request, f'El SKU "{sku}" ya pertenece a otro producto.')
            return render(request, 'catalog/product/edit.html', context)

        try:
            product.sku = sku
            product.name = name
            product.description = description
            product.category = ProductCategory.objects.filter(id=category_id, created_by=user).first() if category_id else None
            product.purchase_price = purchase_price
            product.sale_price = sale_price
            product.currency = Currency.objects.filter(id=currency_id, created_by=user).first() if currency_id else None
            product.save()

            messages.success(request, 'Producto actualizado exitosamente.')
            return redirect('catalog:product_list')
        except Exception as e:
            messages.error(request, f'Ocurrió un error al actualizar: {e}')
            return render(request, 'catalog/product/edit.html', context)
