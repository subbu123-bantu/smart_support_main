import django_filters
from tickets.models import Ticket

class TicketFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    priority = django_filters.CharFilter(field_name='priority', lookup_expr='iexact')  # ✅ fixed typo
    
    class Meta:
        model = Ticket
        fields = ['status', 'priority']