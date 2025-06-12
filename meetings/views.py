from rest_framework import viewsets, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db import models
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from datetime import datetime, timedelta

from .models import (
    Category, Meeting, Comment, Rating, MeetingParticipation, 
    MeetingCooperation, Notification
)
from .serializers import (
    CategorySerializer, MeetingListSerializer, MeetingDetailSerializer,
    MeetingCreateUpdateSerializer, CommentSerializer, RatingSerializer,
    MeetingParticipationSerializer, MeetingCooperationSerializer,
    NotificationSerializer, JoinMeetingSerializer
)
# Imports comentados temporariamente até criar os arquivos
# from .filters import MeetingFilter
# from .permissions import IsMeetingCreatorOrCooperator, CanManageParticipants


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet completo para categorias"""
    queryset = Category.objects.filter(is_active=True).order_by('display_order', 'name')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'display_order', 'created_at']
    ordering = ['display_order', 'name']
    
    def get_permissions(self):
        """Apenas admins podem criar/editar/deletar categorias"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
            # Aqui você pode adicionar verificação se é admin/staff
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'])
    def meetings(self, request, pk=None):
        """Lista reuniões de uma categoria específica"""
        category = self.get_object()
        meetings = Meeting.objects.filter(
            category=category,
            status='published'
        ).order_by('-meeting_date', '-meeting_time')
        
        serializer = MeetingListSerializer(meetings, many=True, context={'request': request})
        return Response(serializer.data)


class MeetingViewSet(viewsets.ModelViewSet):
    """ViewSet completo para reuniões"""
    queryset = Meeting.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # filterset_class = MeetingFilter  # Comentado temporariamente
    search_fields = ['title', 'description', 'responsible', 'agenda', 'tags']
    ordering_fields = ['meeting_date', 'meeting_time', 'created_at', 'view_count']
    ordering = ['-meeting_date', '-meeting_time']
    
    def get_serializer_class(self):
        """Usa serializer apropriado para cada ação"""
        if self.action == 'list':
            return MeetingListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return MeetingCreateUpdateSerializer
        else:
            return MeetingDetailSerializer
    
    def get_permissions(self):
        """Controla permissões baseado na ação"""
        if self.action in ['create']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]  # Simplificado temporariamente
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filtra reuniões baseado no usuário e parâmetros"""
        queryset = Meeting.objects.select_related('category', 'creator').prefetch_related(
            'meetingparticipation_set', 'ratings'
        )
        
        # Se usuário não autenticado, mostrar apenas publicadas
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status='published')
        else:
            user = self.request.user
            if user.is_staff:
                # Admin vê tudo
                pass
            else:
                # Usuário normal vê: publicadas + suas próprias + onde é cooperador
                queryset = queryset.filter(
                    Q(status='published') | 
                    Q(creator=user) |
                    Q(cooperators=user)
                ).distinct()
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Override retrieve para incrementar visualizações"""
        instance = self.get_object()
        instance.increment_view_count()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        """Define o criador automaticamente"""
        serializer.save(creator=self.request.user)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Lista próximas reuniões (próximas 3)"""
        upcoming_meetings = Meeting.objects.filter(
            status='published',
            meeting_date__gte=timezone.now().date()
        ).order_by('meeting_date', 'meeting_time')[:3]
        
        serializer = MeetingListSerializer(
            upcoming_meetings, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_meetings(self, request):
        """Reuniões do usuário logado"""
        user = request.user
        
        # Reuniões criadas
        created = Meeting.objects.filter(creator=user).order_by('-created_at')
        
        # Reuniões onde é participante aprovado
        participated = Meeting.objects.filter(
            meetingparticipation__participant=user,
            meetingparticipation__status='approved'
        ).order_by('-meeting_date')
        
        # Reuniões onde é cooperador aprovado
        cooperated = Meeting.objects.filter(
            meetingcooperation__cooperator=user,
            meetingcooperation__status='approved'
        ).order_by('-meeting_date')
        
        return Response({
            'created': MeetingListSerializer(created, many=True, context={'request': request}).data,
            'participated': MeetingListSerializer(participated, many=True, context={'request': request}).data,
            'cooperated': MeetingListSerializer(cooperated, many=True, context={'request': request}).data
        })
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Busca avançada de reuniões"""
        filter_serializer = SearchFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        
        filters = filter_serializer.validated_data
        queryset = self.get_queryset()
        
        # Aplicar filtros
        if filters.get('q'):
            q = filters['q']
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(responsible__icontains=q) |
                Q(agenda__icontains=q) |
                Q(tags__icontains=q)
            )
        
        if filters.get('category'):
            queryset = queryset.filter(category_id=filters['category'])
        
        if filters.get('date_from'):
            queryset = queryset.filter(meeting_date__gte=filters['date_from'])
        
        if filters.get('date_to'):
            queryset = queryset.filter(meeting_date__lte=filters['date_to'])
        
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        
        if filters.get('format'):
            queryset = queryset.filter(meeting_format=filters['format'])
        
        if filters.get('upcoming'):
            queryset = queryset.filter(meeting_date__gte=timezone.now().date())
        
        if filters.get('has_slots'):
            # Reuniões com vagas disponíveis
            queryset = queryset.annotate(
                current_participants=Count('meetingparticipation', 
                                         filter=Q(meetingparticipation__status='approved'))
            ).filter(
                Q(max_participants__isnull=True) |
                Q(max_participants__gt=models.F('current_participants'))
            )
        
        if filters.get('min_rating'):
            queryset = queryset.annotate(
                avg_rating=Avg('ratings__rating')
            ).filter(avg_rating__gte=filters['min_rating'])
        
        if filters.get('tags'):
            tags = [tag.strip() for tag in filters['tags'].split(',')]
            for tag in tags:
                queryset = queryset.filter(tags__icontains=tag)
        
        # Ordenar por relevância/data
        queryset = queryset.order_by('-meeting_date', '-meeting_time')
        
        # Paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MeetingListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = MeetingListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estatísticas gerais das reuniões"""
        stats = {
            'total_meetings': Meeting.objects.count(),
            'published_meetings': Meeting.objects.filter(status='published').count(),
            'upcoming_meetings': Meeting.objects.filter(
                status='published',
                meeting_date__gte=timezone.now().date()
            ).count(),
            'finished_meetings': Meeting.objects.filter(status='finished').count(),
            'total_participants': MeetingParticipation.objects.filter(
                status='approved'
            ).count(),
            'average_rating': Rating.objects.aggregate(
                avg=Avg('rating')
            )['avg'] or 0,
        }
        
        # Estatísticas por categoria
        categories_stats = {}
        for category in Category.objects.filter(is_active=True):
            categories_stats[category.name] = {
                'total': category.meetings.count(),
                'published': category.meetings.filter(status='published').count(),
                'upcoming': category.meetings.filter(
                    status='published',
                    meeting_date__gte=timezone.now().date()
                ).count()
            }
        
        stats['categories_stats'] = categories_stats
        
        serializer = MeetingStatsSerializer(stats)
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet para comentários"""
    queryset = Comment.objects.filter(is_active=True)
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['meeting', 'parent']
    ordering_fields = ['created_at', 'likes_count']
    ordering = ['-is_pinned', '-created_at']
    
    def get_queryset(self):
        queryset = Comment.objects.filter(is_active=True).select_related(
            'author', 'meeting', 'parent'
        )
        
        meeting_id = self.request.query_params.get('meeting', None)
        if meeting_id:
            queryset = queryset.filter(meeting__id=meeting_id)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Curtir comentário"""
        comment = self.get_object()
        comment.likes_count += 1
        comment.save(update_fields=['likes_count'])
        return Response({'likes_count': comment.likes_count})


class RatingViewSet(viewsets.ModelViewSet):
    """ViewSet para avaliações"""
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['meeting', 'rating']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Rating.objects.select_related('user', 'meeting')
        
        meeting_id = self.request.query_params.get('meeting', None)
        if meeting_id:
            queryset = queryset.filter(meeting__id=meeting_id)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Views específicas para ações de reunião
class JoinMeetingView(APIView):
    """Solicitar participação em reunião"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, meeting_id):
        meeting = get_object_or_404(Meeting, id=meeting_id)
        serializer = JoinMeetingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Verificar se já existe participação
        participation, created = MeetingParticipation.objects.get_or_create(
            meeting=meeting,
            participant=request.user,
            defaults={
                'status': 'approved' if not meeting.requires_approval else 'pending',
                'message': serializer.validated_data.get('message', '')
            }
        )
        
        if created:
            meeting.increment_join_attempts()
            
            # Criar notificação para o criador
            if meeting.requires_approval:
                Notification.objects.create(
                    user=meeting.creator,
                    type='participation_request',
                    title=f'Nova solicitação de participação',
                    message=f'{request.user.get_full_name()} solicitou participar da reunião "{meeting.title}"',
                    meeting=meeting
                )
            
            return Response({
                'message': 'Solicitação enviada com sucesso!' if meeting.requires_approval else 'Participação confirmada!',
                'status': participation.status,
                'requires_approval': meeting.requires_approval
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'message': f'Você já tem uma solicitação com status: {participation.get_status_display()}',
                'status': participation.status
            }, status=status.HTTP_400_BAD_REQUEST)


class LeaveMeetingView(APIView):
    """Cancelar participação em reunião"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, meeting_id):
        meeting = get_object_or_404(Meeting, id=meeting_id)
        
        try:
            participation = MeetingParticipation.objects.get(
                meeting=meeting,
                participant=request.user
            )
            participation.status = 'cancelled'
            participation.save()
            
            return Response({
                'message': 'Participação cancelada com sucesso!'
            })
        except MeetingPartic