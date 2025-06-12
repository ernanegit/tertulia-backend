import django_filters
from django.db.models import Q
from django.utils import timezone
from .models import Meeting, Category


class MeetingFilter(django_filters.FilterSet):
    """Filtros para reuniões"""
    
    # Filtros por texto
    title = django_filters.CharFilter(lookup_expr='icontains')
    responsible = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    
    # Filtros por categoria
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all())
    category_name = django_filters.CharFilter(field_name='category__name', lookup_expr='icontains')
    
    # Filtros por data
    date_from = django_filters.DateFilter(field_name='meeting_date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='meeting_date', lookup_expr='lte')
    month = django_filters.NumberFilter(field_name='meeting_date__month')
    year = django_filters.NumberFilter(field_name='meeting_date__year')
    
    # Filtros por status
    status = django_filters.ChoiceFilter(choices=Meeting.STATUS_CHOICES)
    access_type = django_filters.ChoiceFilter(choices=Meeting.ACCESS_TYPE_CHOICES)
    meeting_format = django_filters.ChoiceFilter(choices=Meeting.MEETING_FORMATS)
    
    # Filtros booleanos
    upcoming = django_filters.BooleanFilter(method='filter_upcoming')
    has_slots = django_filters.BooleanFilter(method='filter_has_slots')
    allow_comments = django_filters.BooleanFilter()
    allow_ratings = django_filters.BooleanFilter()
    is_recurring = django_filters.BooleanFilter()
    
    # Filtros por criador
    creator = django_filters.NumberFilter(field_name='creator__id')
    creator_name = django_filters.CharFilter(field_name='creator__first_name', lookup_expr='icontains')
    
    # Filtro por tags
    tags = django_filters.CharFilter(method='filter_tags')
    
    # Busca geral
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Meeting
        fields = {
            'duration_minutes': ['exact', 'gte', 'lte'],
            'max_participants': ['exact', 'gte', 'lte'],
            'view_count': ['gte'],
            'created_at': ['gte', 'lte'],
        }
    
    def filter_upcoming(self, queryset, name, value):
        """Filtrar reuniões futuras"""
        if value:
            return queryset.filter(meeting_date__gte=timezone.now().date())
        return queryset
    
    def filter_has_slots(self, queryset, name, value):
        """Filtrar reuniões com vagas disponíveis"""
        if value:
            from django.db.models import Count, F
            return queryset.annotate(
                current_participants=Count('meetingparticipation', 
                                         filter=Q(meetingparticipation__status='approved'))
            ).filter(
                Q(max_participants__isnull=True) |
                Q(max_participants__gt=F('current_participants'))
            )
        return queryset
    
    def filter_tags(self, queryset, name, value):
        """Filtrar por tags (suporta múltiplas tags separadas por vírgula)"""
        if value:
            tags = [tag.strip() for tag in value.split(',') if tag.strip()]
            for tag in tags:
                queryset = queryset.filter(tags__icontains=tag)
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Busca geral em múltiplos campos"""
        if value:
            return queryset.filter(
                Q(title__icontains=value) |
                Q(description__icontains=value) |
                Q(responsible__icontains=value) |
                Q(agenda__icontains=value) |
                Q(tags__icontains=value) |
                Q(category__name__icontains=value)
            )
        return queryset