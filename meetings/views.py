# meetings/views.py - CORREÇÃO COMPLETA DOS IMPORTS

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db.models import Q  # ✅ IMPORT FALTANTE
from django.utils import timezone  # ✅ IMPORT FALTANTE
from django.db import transaction

# ✅ IMPORTS DOS MODELOS
from .models import (
    Category, 
    Meeting, 
    Comment, 
    Rating, 
    MeetingParticipation, 
    MeetingCooperation
)

# ✅ IMPORTS DOS SERIALIZERS
from .serializers import (
    CategorySerializer, 
    MeetingListSerializer, 
    MeetingDetailSerializer,
    MeetingCreateUpdateSerializer, 
    CommentSerializer, 
    RatingSerializer,
    MeetingParticipationSerializer,
    MeetingCooperationSerializer
)

# ✅ IMPORTS DAS PERMISSÕES
from .permissions import (
    CanCreateMeeting, 
    IsMeetingCreatorOrCooperator,
    CanManageParticipants
)

# ✅ IMPORTS DO ACCOUNTS
from accounts.models import User


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet para categorias"""
    queryset = Category.objects.filter(is_active=True).order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class MeetingViewSet(viewsets.ModelViewSet):
    """ViewSet para reuniões"""
    queryset = Meeting.objects.all()
    
    def get_permissions(self):
        """Permissões por ação"""
        if self.action == 'create':
            permission_classes = [IsAuthenticated, CanCreateMeeting]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsMeetingCreatorOrCooperator]
        else:
            permission_classes = [AllowAny]  # Lista e detalhes são públicos
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Serializer por ação"""
        if self.action == 'list':
            return MeetingListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return MeetingCreateUpdateSerializer
        else:
            return MeetingDetailSerializer
    
    def get_queryset(self):
        """QuerySet otimizado com filtros"""
        queryset = Meeting.objects.select_related('category', 'creator')
        
        # Filtros baseados no usuário
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status='published')
        else:
            # Usuário autenticado vê suas reuniões + publicadas
            if not self.request.user.is_staff:
                queryset = queryset.filter(
                    Q(status='published') | 
                    Q(creator=self.request.user) |
                    Q(cooperators=self.request.user)
                ).distinct()
        
        return queryset.order_by('-meeting_date', '-meeting_time')
    
    @transaction.atomic
    def perform_create(self, serializer):
        """Criação com lógica adicional"""
        user = self.request.user
        
        # Definir status inicial baseado no tipo de usuário
        if user.user_type == 'criador':
            status_inicial = 'published'
        else:
            status_inicial = 'pending_approval'
        
        meeting = serializer.save(
            creator=user,
            status=status_inicial
        )
        
        # Auto-adicionar criador como participante aprovado
        MeetingParticipation.objects.create(
            meeting=meeting,
            participant=user,
            status='approved'
        )
        
        return meeting


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet para comentários"""
    queryset = Comment.objects.filter(is_active=True).select_related('author', 'meeting')
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar comentários por reunião se especificado"""
        queryset = super().get_queryset()
        meeting_id = self.request.query_params.get('meeting', None)
        if meeting_id:
            queryset = queryset.filter(meeting_id=meeting_id)
        return queryset.order_by('-is_pinned', '-created_at')
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class RatingViewSet(viewsets.ModelViewSet):
    """ViewSet para avaliações"""
    queryset = Rating.objects.all().select_related('user', 'meeting')
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar avaliações por reunião se especificado"""
        queryset = super().get_queryset()
        meeting_id = self.request.query_params.get('meeting', None)
        if meeting_id:
            queryset = queryset.filter(meeting_id=meeting_id)
        
        # Não mostrar avaliações anônimas de outros usuários
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(is_anonymous=False) | Q(user=self.request.user)
            )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ===== VIEWS ESPECÍFICAS =====

class JoinMeetingView(APIView):
    """Solicitar participação em reunião"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, meeting_id):
        meeting = get_object_or_404(Meeting, id=meeting_id)
        
        # Verificar se já está participando
        existing_participation = MeetingParticipation.objects.filter(
            meeting=meeting,
            participant=request.user
        ).first()
        
        if existing_participation:
            return Response({
                'message': f'Você já está participando desta reunião (Status: {existing_participation.get_status_display()})',
                'status': existing_participation.status
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar limite de participantes
        if meeting.max_participants:
            current_count = meeting.get_participant_count()
            if current_count >= meeting.max_participants:
                return Response({
                    'error': 'Reunião já atingiu o limite máximo de participantes'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Criar participação
        participation_status = 'approved' if not meeting.requires_approval else 'pending'
        
        participation = MeetingParticipation.objects.create(
            meeting=meeting,
            participant=request.user,
            status=participation_status,
            message=request.data.get('message', '')
        )
        
        # Incrementar contador de tentativas
        meeting.increment_join_attempts()
        
        return Response({
            'message': 'Participação confirmada!' if participation_status == 'approved' else 'Solicitação enviada, aguarde aprovação.',
            'status': participation.status,
            'requires_approval': meeting.requires_approval
        }, status=status.HTTP_201_CREATED)


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
            
            # Não permitir sair se a reunião já começou
            if meeting.is_in_progress or meeting.is_finished:
                return Response({
                    'error': 'Não é possível cancelar participação em reunião em andamento ou finalizada'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            participation.delete()
            
            return Response({
                'message': 'Participação cancelada com sucesso!'
            }, status=status.HTTP_200_OK)
            
        except MeetingParticipation.DoesNotExist:
            return Response({
                'error': 'Você não está participando desta reunião'
            }, status=status.HTTP_400_BAD_REQUEST)


class UpcomingMeetingsView(APIView):
    """Lista próximas reuniões"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        upcoming_meetings = Meeting.objects.filter(
            status='published',
            meeting_date__gte=timezone.now().date()
        ).select_related('category', 'creator').order_by('meeting_date', 'meeting_time')[:10]
        
        serializer = MeetingListSerializer(
            upcoming_meetings, 
            many=True, 
            context={'request': request}
        )
        
        return Response({
            'count': len(serializer.data),
            'results': serializer.data
        })


class MyMeetingsView(APIView):
    """Reuniões do usuário logado"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Reuniões criadas
        created_meetings = Meeting.objects.filter(
            creator=user
        ).select_related('category').order_by('-created_at')
        
        # Reuniões participando
        participated_meetings = Meeting.objects.filter(
            meetingparticipation__participant=user,
            meetingparticipation__status='approved'
        ).select_related('category', 'creator').order_by('-meeting_date')
        
        # Cooperações
        cooperated_meetings = Meeting.objects.filter(
            meetingcooperation__cooperator=user,
            meetingcooperation__status='approved'
        ).select_related('category', 'creator').order_by('-meeting_date')
        
        return Response({
            'created': MeetingListSerializer(created_meetings, many=True, context={'request': request}).data,
            'participated': MeetingListSerializer(participated_meetings, many=True, context={'request': request}).data,
            'cooperated': MeetingListSerializer(cooperated_meetings, many=True, context={'request': request}).data,
            'stats': {
                'total_created': created_meetings.count(),
                'total_participated': participated_meetings.count(),
                'total_cooperated': cooperated_meetings.count()
            }
        })


class SearchMeetingsView(APIView):
    """Busca avançada de reuniões"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        queryset = Meeting.objects.filter(status='published').select_related('category', 'creator')
        
        # Filtros de busca
        search_term = request.query_params.get('q', '')
        if search_term:
            queryset = queryset.filter(
                Q(title__icontains=search_term) |
                Q(description__icontains=search_term) |
                Q(responsible__icontains=search_term) |
                Q(tags__icontains=search_term)
            )
        
        category_id = request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        meeting_format = request.query_params.get('format')
        if meeting_format:
            queryset = queryset.filter(meeting_format=meeting_format)
        
        upcoming_only = request.query_params.get('upcoming')
        if upcoming_only and upcoming_only.lower() == 'true':
            queryset = queryset.filter(meeting_date__gte=timezone.now().date())
        
        # Ordenação
        order_by = request.query_params.get('order_by', '-meeting_date')
        valid_orders = ['-meeting_date', 'meeting_date', '-created_at', 'title']
        if order_by in valid_orders:
            queryset = queryset.order_by(order_by)
        
        # Paginação manual básica
        page_size = min(int(request.query_params.get('page_size', 20)), 100)
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size
        
        total_count = queryset.count()
        results = queryset[start:end]
        
        serializer = MeetingListSerializer(results, many=True, context={'request': request})
        
        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'results': serializer.data
        })


# ===== VIEWS TEMPORÁRIAS (para desenvolvimento) =====

class ApproveParticipantView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, meeting_id):
        return Response({'message': 'Funcionalidade em desenvolvimento'})

class RejectParticipantView(APIView):
    permission_classes = [IsAuthenticated]  
    def post(self, request, meeting_id):
        return Response({'message': 'Funcionalidade em desenvolvimento'})

class RequestCooperationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, meeting_id):
        return Response({'message': 'Funcionalidade em desenvolvimento'})

class ApproveCooperationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, meeting_id):
        return Response({'message': 'Funcionalidade em desenvolvimento'})

class RejectCooperationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, meeting_id):
        return Response({'message': 'Funcionalidade em desenvolvimento'})

class MeetingCommentsView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, meeting_id):
        meeting = get_object_or_404(Meeting, id=meeting_id)
        comments = Comment.objects.filter(
            meeting=meeting, 
            is_active=True
        ).select_related('author').order_by('-is_pinned', '-created_at')
        
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)

class MeetingRatingsView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, meeting_id):
        meeting = get_object_or_404(Meeting, id=meeting_id)
        ratings = Rating.objects.filter(meeting=meeting).select_related('user')
        
        # Estatísticas
        total_ratings = ratings.count()
        average_rating = meeting.get_average_rating()
        
        # Distribuição por estrelas
        rating_distribution = {}
        for i in range(1, 6):
            rating_distribution[f'{i}_stars'] = ratings.filter(rating=i).count()
        
        return Response({
            'average_rating': average_rating,
            'total_ratings': total_ratings,
            'distribution': rating_distribution,
            'ratings': RatingSerializer(ratings[:10], many=True, context={'request': request}).data
        })

class MyMeetingRatingView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, meeting_id):
        try:
            rating = Rating.objects.get(meeting_id=meeting_id, user=request.user)
            return Response(RatingSerializer(rating, context={'request': request}).data)
        except Rating.DoesNotExist:
            return Response({'message': 'Você ainda não avaliou esta reunião'}, status=404)