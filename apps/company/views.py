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
        owner = AppUser.objects.get(id=request.user.id)  # Asignamos el usuario actual como propietario

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
        if not name or not address or not phone:
            messages.error(request, 'Por favor, completa todos los campos obligatorios.')
            return render(request, 'company/create.html', context)

        try:
            # Creamos la compañía vinculando al usuario como propietario y el usuario actual como creador
            Company.objects.create(
                name=name,
                address=address,
                phone=phone,
                description=description,
                selected=selected,
                owner=owner,
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
        user = AppUser.objects.get(id=request.user.id)
        if company_obj.owner != user:
            messages.error(request, 'No tienes permiso para editar esta compañía.')
            return redirect('company:company_index')
        context = {
            'company': company_obj,
        }
        return render(request, 'company/edit.html', context)

    def post(self, request, pk):
        company_obj = get_object_or_404(Company, id=pk)
        
        name = request.POST.get('name')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        description = request.POST.get('description')
        selected = True if request.POST.get('selected') == 'on' else False
        context = {
            'company': company_obj
        }

        # Validación básica
        if not name or not address or not phone :
            messages.error(request, 'Por favor, completa los campos obligatorios.')
            return render(request, 'company/edit.html', context)

        try:         
            company_obj.name = name
            company_obj.address = address
            company_obj.phone = phone
            company_obj.description = description
            company_obj.selected = selected
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
        user = AppUser.objects.get(id=request.user.id)
        if company_obj.owner != user:
            messages.error(request, 'No tienes permiso para eliminar esta compañía.')
            return redirect('company:company_index')
        try:
            company_name = company_obj.name
            company_obj.delete()
            messages.success(request, f'La compañía "{company_name}" ha sido eliminada correctamente.')
        except Exception as e:
            messages.error(request, f'No se pudo eliminar la compañía. Es posible que tenga registros dependientes.')
        return redirect('company:company_index')


class ToggleCompanyStatusView(BasePermissionMixin, View):
    permission_required = 'company.change_company'

    def post(self, request, company_id):
        company_obj = get_object_or_404(Company, id=company_id)
        company_obj.selected = not company_obj.selected
        company_obj.save()
        status_text = "activada" if company_obj.selected else "desactivada"
        messages.success(request, f'La compañía "{company_obj.name}" ha sido {status_text} correctamente.')
        return redirect('company:company_index')