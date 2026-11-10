from django.shortcuts import render, redirect
from django.views import View
from django.shortcuts import render, get_object_or_404
from .models import Company
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from apps.accounts.models import AppUser
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .mixins import BasePermissionMixin  # O heredar directamente de PermissionRequiredMixin

class ListCompanyView(BasePermissionMixin, View):
    permission_required = 'company.view_company'  

    def get(self, request):
        user = AppUser.objects.get(id=request.user.id)
        companies = Company.objects.filter(owner=user)
        context = {
            'companies': companies
        }
        return render(request, 'company/index.html', context)


class CreateCompanyView(BasePermissionMixin, View):
    permission_required = 'company.add_company'

    def get(self, request):
        # Obtenemos la lista de usuarios para los selectores de Propietario y Creador
        users = AppUser.objects.all()
        context = {
            'users': users
        }
        return render(request, 'company/create.html', context)

    def post(self, request):
        name = request.POST.get('name')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        description = request.POST.get('description')
        selected = True if request.POST.get('selected') == 'on' else False
        owner_id = request.POST.get('owner')

        users = AppUser.objects.all()
        context = {
            'name': name,
            'address': address,
            'phone': phone,
            'description': description,
            'selected': selected,
            'users': users
        }

        # Validación básica
        if not name or not address or not phone or not owner_id:
            messages.error(request, 'Por favor, completa todos los campos obligatorios.')
            return render(request, 'company/create.html', context)

        try:
            owner_obj = AppUser.objects.get(id=owner_id)
            
            # Creamos la compañía vinculando al usuario como propietario y el usuario actual como creador
            Company.objects.create(
                name=name,
                address=address,
                phone=phone,
                description=description,
                selected=selected,
                owner=owner_obj,
                created_by=request.user if request.user.is_authenticated else None
            )

            messages.success(request, 'Compañía creada exitosamente.')
            return redirect('company:company_index') # Asegúrate de que tu ruta de lista tenga este nombre
            
        except Exception as e:
            messages.error(request, f'Ocurrió un error al crear la compañía: {e}')
            return render(request, 'company/create.html', context)


class EditCompanyView(BasePermissionMixin, View):
    permission_required = 'company.change_company'

    def get(self, request, pk):
        company_obj = get_object_or_404(Company, id=pk)
        users = AppUser.objects.all()
        
        context = {
            'company': company_obj,
            'users': users
        }
        return render(request, 'company/edit.html', context)

    def post(self, request, pk):
        company_obj = get_object_or_404(Company, id=pk)
        
        name = request.POST.get('name')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        description = request.POST.get('description')
        selected = True if request.POST.get('selected') == 'on' else False
        owner_id = request.POST.get('owner')

        users = AppUser.objects.all()
        context = {
            'company': company_obj,
            'users': users
        }

        # Validación básica
        if not name or not address or not phone or not owner_id:
            messages.error(request, 'Por favor, completa los campos obligatorios.')
            return render(request, 'company/edit.html', context)

        try:
            owner_obj = AppUser.objects.get(id=owner_id)
            
            company_obj.name = name
            company_obj.address = address
            company_obj.phone = phone
            company_obj.description = description
            company_obj.selected = selected
            company_obj.owner = owner_obj
            company_obj.save()

            messages.success(request, 'Compañía actualizada exitosamente.')
            return redirect('company:company_index')
            
        except Exception as e:
            messages.error(request, f'Ocurrió un error al actualizar: {e}')
            return render(request, 'company/edit.html', context)


class DeleteCompanyView(BasePermissionMixin, View):
    permission_required = 'company.delete_company'

    def post(self, request, company_id):
        company_obj = get_object_or_404(Company, id=company_id)
        
        try:
            company_name = company_obj.name
            company_obj.delete()
            messages.success(request, f'La compañía "{company_name}" ha sido eliminada correctamente.')
        except Exception as e:
            messages.error(request, f'No se pudo eliminar la compañía. Es posible que tenga registros dependientes.')
        return redirect('company:company_index')


