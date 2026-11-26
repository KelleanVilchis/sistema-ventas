from decimal import Decimal

from django.db.models import Sum, Count, Q
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.company.mixins import BasePermissionMixin
from apps.company.models import Company
from apps.accounts.models import AppUser
from apps.sales.models import Sale, SaleReturn, Expense, Order


class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        # Empresa activa del usuario
        owner = AppUser.objects.get(id=request.user.id)
        company = Company.objects.filter(selected=True, owner=owner).first()

        if company is None:
            return render(request, 'dashboard/dashboard.html', {
                'sin_empresa': True,
            })

        hoy = timezone.now().date()
        inicio_mes = hoy.replace(day=1)

        # ─── VENTAS ───
        ventas_qs = Sale.objects.filter(company=company, status='SOLD')

        ventas_hoy_qs = ventas_qs.filter(date_sale__date=hoy)
        ventas_mes_qs = ventas_qs.filter(date_sale__date__gte=inicio_mes)

        total_ventas_hoy = ventas_hoy_qs.aggregate(t=Sum('total_amount'))['t'] or Decimal('0')
        total_ventas_mes = ventas_mes_qs.aggregate(t=Sum('total_amount'))['t'] or Decimal('0')

        num_ventas_hoy = ventas_hoy_qs.count()
        num_ventas_mes = ventas_mes_qs.count()

        # ─── GASTOS ───
        gastos_mes_qs = Expense.objects.filter(
            company=company,
            date_expense__date__gte=inicio_mes,
        )
        total_gastos_mes = gastos_mes_qs.aggregate(t=Sum('amount'))['t'] or Decimal('0')

        # Desglose por tipo
        gastos_por_tipo = (
            gastos_mes_qs
            .values('expense_type')
            .annotate(total=Sum('amount'), cantidad=Count('id'))
            .order_by('-total')
        )

        # ─── DEVOLUCIONES ───
        devoluciones_mes_qs = SaleReturn.objects.filter(
            company=company,
            created_at__date__gte=inicio_mes,
        )
        total_devoluciones_mes = devoluciones_mes_qs.aggregate(t=Sum('total_refunded'))['t'] or Decimal('0')

        # ─── GANANCIA NETA ───
        ganancia_mes = total_ventas_mes - total_gastos_mes

        # ─── PEDIDOS PENDIENTES ───
        pedidos_pendientes = Order.objects.filter(
            company=company,
            status__in=['PENDING', 'ACCEPTED'],
        ).count()

        # ─── ACTIVIDAD RECIENTE (últimas 5 ventas) ───
        ventas_recientes = (
            Sale.objects
            .filter(company=company)
            .select_related('order', 'created_by')
            .order_by('-created_at')[:5]
        )
        # Desglose por método de pago (mes actual)
        pagos_mes = (
            ventas_mes_qs
            .values('payment_method')
            .annotate(
                total=Sum('total_amount'),
                cantidad=Count('id'),
                total_mxn=Sum('paid_mxn'),
                total_usd=Sum('paid_usd'),
            )
        )

        # Totales separados
        total_mxn_mes = ventas_mes_qs.aggregate(t=Sum('paid_mxn'))['t'] or Decimal('0')
        total_usd_mes = ventas_mes_qs.aggregate(t=Sum('paid_usd'))['t'] or Decimal('0')
        context = {
            'company': company,

            'total_ventas_hoy': total_ventas_hoy,
            'total_ventas_mes': total_ventas_mes,
            'num_ventas_hoy': num_ventas_hoy,
            'num_ventas_mes': num_ventas_mes,

            'total_gastos_mes': total_gastos_mes,
            'total_devoluciones_mes': total_devoluciones_mes,
            'ganancia_mes': ganancia_mes,

            'pagos_mes': pagos_mes,
            'total_mxn_mes': total_mxn_mes,
            'total_usd_mes': total_usd_mes,
            
            'gastos_por_tipo': gastos_por_tipo,
            'pedidos_pendientes': pedidos_pendientes,
            'ventas_recientes': ventas_recientes,
        }
        return render(request, 'dashboard/dashboard.html', context)


class ListUsersView(BasePermissionMixin, View):
    permission_required = 'accounts.view_appuser'

    def get(self, request):
        user = AppUser.objects.get(id=request.user.id)
        if user.user_type == "EMP":
            return redirect('dashboard')
        users = AppUser.objects.all()
        return render(request, 'accounts/index.html', {'users': users})