from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Combo, ComboItem, Product
from apps.company.models import Company
from apps.accounts.models import AppUser

class ComboListView(LoginRequiredMixin, View):
    def get(self, request):
        combos = Combo.objects.select_related('company', 'created_by').prefetch_related('items__product').all()
        return render(request, 'combo/index.html', {'combos': combos})

class CreateComboView(LoginRequiredMixin, View):
    def get(self, request):
        companies = Company.objects.all()
        products = Product.objects.all()
        context = {
            'companies': companies,
            'products': products
        }
        return render(request, 'combo/create.html', context)

    def post(self, request):
        name = request.POST.get('name')
        description = request.POST.get('description')
        owner = AppUser.objects.get(id=request.user.id)  # Assuming the logged-in user is the owner of the company
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
            return render(request, 'combo/create.html', context)

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
            return render(request, 'combo/create.html', context)

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
        return render(request, 'combo/edit.html', context)

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



