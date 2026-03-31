# tickets/filters.py
import django_filters
from .models import Ticket


class TicketFilter(django_filters.FilterSet):
    status   = django_filters.CharFilter(
                   field_name='status',        lookup_expr='iexact')
    priority = django_filters.CharFilter(
                   field_name='priority',      lookup_expr='iexact')
    category = django_filters.CharFilter(
                   field_name='category__name',lookup_expr='icontains')
    created_after  = django_filters.DateFilter(
                   field_name='created_at',    lookup_expr='gte')
    created_before = django_filters.DateFilter(
                   field_name='created_at',    lookup_expr='lte')

    class Meta:
        model  = Ticket
        fields = ['status', 'priority', 'category']