from django.shortcuts import render, redirect
from django.views import View
from django.shortcuts import render, get_object_or_404
from .models import AppUser
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from .models import AppUser, UserType
from .forms import LoginForm
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

class CreateUserView(View):
    def get(self, request):
        # Pasamos los tipos de usuario disponibles (ADM / EMP) para llenar el <select> en el HTML
        context = {
            'user_types': UserType.choices
        }
        return render(request, 'accounts/register.html', context)

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        user_type = request.POST.get('user_type')

        context = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'user_type': user_type,
            'user_types': UserType.choices
        }

        # Validación básica
        if not email or not password or not first_name or not last_name:
            messages.error(request, 'Por favor, completa todos los campos obligatorios.')
            return render(request, 'accounts/register.html', context)

        try:
            # Creación usando el manager personalizado
            user = AppUser.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Asignación del tipo de usuario (Administrador / Empleado)
            if user_type:
                user.user_type = user_type
                user.save()

            messages.success(request, 'Usuario registrado exitosamente en Distrito 21.')
            return redirect('accounts:list_users') # Lo ideal al tener éxito es redirigir a la lista
            
        except Exception as e:
            messages.error(request, f'Ocurrió un error al registrar el usuario: {e}')
            return render(request, 'accounts/register.html', context)

class ListUsersView(View):
    def get(self, request):
        users = AppUser.objects.all()
        return render(request, 'accounts/index.html', {'users': users})


class DeleteUserView(View):
    def post(self, request, user_id):
        user = get_object_or_404(AppUser, id=user_id)
        user.delete()
        messages.success(request, 'Usuario eliminado exitosamente.')
        return redirect('accounts:list_users')



class EditUserView(View):
    def get(self, request, user_id):
        user_obj = get_object_or_404(AppUser, id=user_id)
        context = {
            'edit_user': user_obj,
            'user_types': UserType.choices
        }
        return render(request, 'accounts/edit.html', context)

    def post(self, request, user_id):
        user_obj = get_object_or_404(AppUser, id=user_id)
        
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        user_type = request.POST.get('user_type')
        is_active = True if request.POST.get('is_active') == 'on' else False
        password = request.POST.get('password') # Opcional por si desea cambiarla

        context = {
            'edit_user': user_obj,
            'user_types': UserType.choices
        }

        if not email or not first_name or not last_name:
            messages.error(request, 'Por favor, completa los campos obligatorios.')
            return render(request, 'accounts/edit.html', context)

        try:
            user_obj.first_name = first_name
            user_obj.last_name = last_name
            user_obj.email = email
            user_obj.user_type = user_type
            user_obj.is_active = is_active

            # Si ingresó una nueva contraseña, la actualizamos cifrada
            if password:
                user_obj.set_password(password)

            user_obj.save()
            messages.success(request, 'Usuario actualizado exitosamente.')
            return redirect('accounts:list_users')
            
        except Exception as e:
            messages.error(request, f'Ocurrió un error al actualizar: {e}')
            return render(request, 'accounts/edit.html', context)


class LoginView(View):
    def get(self, request):
        # Si el usuario ya está autenticado, lo mandamos al dashboard
        if request.user.is_authenticated:
            return redirect('dashboard')
            
        form = LoginForm()
        return render(request, 'accounts/login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            
            # Como tu modelo usa email para autenticar, Django valida con 'username=email'
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, '¡Bienvenido de nuevo a Distrito 21!')
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Tu cuenta se encuentra inactiva.')
            else:
                # Agregamos error para que se active la alerta roja en el template
                form.add_error(None, 'Correo o contraseña incorrectos.')
                
        return render(request, 'accounts/login.html', {'form': form})


def logout(request):    
    auth_logout(request)
    
    return redirect('accounts:login')