from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
# Importa tus modelos aquí (ej. Venta, Cliente, Servicio, etc.)

class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        # Aquí puedes calcular métricas reales de tu barbería Distrito 21
        context = {
            'total_ventas_hoy': 1250, # Ejemplo de datos
            'total_servicios': 18,
            'total_clientes': 142,
            'ingresos_mes': 34800,
        }
        return render(request, 'dashboard/dashboard.html', context)