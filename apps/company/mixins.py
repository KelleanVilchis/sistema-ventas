from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect

class BasePermissionMixin(PermissionRequiredMixin):
    raise_exception = False

    def handle_no_permission(self):
        messages.error(self.request, "No tienes los permisos necesarios para realizar esta acción.")
        return redirect('dashboard')  # O la ruta que prefieras como fallback