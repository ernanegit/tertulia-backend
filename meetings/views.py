# meetings/views.py - ARQUIVO COMPLETO COM TODOS OS IMPORTS E PARTICIPANTES

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, F, Count
from django.utils import timezone
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


# ===== VIEWS ESPECÍFICAS DE REUNIÕES =====

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


# ===== VIEWS DE PARTICIPANTES =====

class MeetingParticipantsView(APIView):
    """Listar participantes de uma reunião"""
    permission_classes = [AllowAny]  # Público pode ver participantes
    
    def get(self, request, meeting_id):
        meeting = get_object_or_404(Meeting, id=meeting_id)
        
        # Filtrar por status se especificado
        status_filter = request.query_params.get('status', 'approved')
        
        participations = MeetingParticipation.objects.filter(
            meeting=meeting
        ).select_related('participant')
        
        # Aplicar filtro de status
        if status_filter != 'all':
            participations = participations.filter(status=status_filter)
        
        # Ordenar por data de participação
        participations = participations.order_by('-created_at')
        
        # Serializar dados
        participants_data = []
        for participation in participations:
            participant_info = {
                'id': participation.id,
                'participant': {
                    'id': participation.participant.id,
                    'name': participation.participant.get_full_name(),
                    'email': participation.participant.email if request.user.is_staff or meeting.can_edit(request.user) else None,
                    'user_type': participation.participant.user_type,
                },
                'status': participation.status,
                'message': participation.message if participation.message else None,
                'attended': participation.attended,
                'joined_at': participation.joined_at,
                'created_at': participation.created_at,
                'response_message': participation.response_message if participation.response_message else None,
            }
            participants_data.append(participant_info)
        
        # Estatísticas
        stats = {
            'total': participations.count(),
            'approved': participations.filter(status='approved').count(),
            'pending': participations.filter(status='pending').count(),
            'rejected': participations.filter(status='rejected').count(),
        }
        
        return Response({
            'meeting': {
                'id': meeting.id,
                'title': meeting.title,
                'meeting_date': meeting.meeting_date,
                'max_participants': meeting.max_participants,
            },
            'stats': stats,
            'participants': participants_data
        })


class ManageParticipantView(APIView):
    """Aprovar/Rejeitar participantes"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, meeting_id):
        meeting = get_object_or_404(Meeting, id=meeting_id)
        
        # Verificar permissão
        if not meeting.can_edit(request.user):
            return Response(
                {'error': 'Sem permissão para gerenciar participantes desta reunião'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        participant_id = request.data.get('participant_id')
        action = request.data.get('action')  # 'approve' ou 'reject'
        response_message = request.data.get('response_message', '')
        
        if not participant_id or not action:
            return Response(
                {'error': 'participant_id e action são obrigatórios'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if action not in ['approve', 'reject']:
            return Response(
                {'error': 'action deve ser "approve" ou "reject"'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            participation = MeetingParticipation.objects.get(
                meeting=meeting,
                participant_id=participant_id
            )
        except MeetingParticipation.DoesNotExist:
            return Response(
                {'error': 'Participação não encontrada'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar se já não foi processada
        if participation.status != 'pending':
            return Response(
                {'error': f'Participação já está {participation.status}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar limite de participantes (apenas para aprovação)
        if action == 'approve' and meeting.max_participants:
            current_approved = meeting.get_participant_count()
            if current_approved >= meeting.max_participants:
                return Response(
                    {'error': 'Reunião já atingiu o limite máximo de participantes'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Atualizar participação
        new_status = 'approved' if action == 'approve' else 'rejected'
        participation.status = new_status
        participation.response_message = response_message
        participation.approved_by = request.user
        participation.save()
        
        # Enviar notificação (usar utils)
        from .utils import MeetingUtils
        notification_type = 'participation_approved' if action == 'approve' else 'participation_rejected'
        MeetingUtils.send_meeting_notification(
            meeting, notification_type, [participation.participant]
        )
        
        return Response({
            'message': f'Participação {"aprovada" if action == "approve" else "rejeitada"} com sucesso',
            'participation': {
                'participant_name': participation.participant.get_full_name(),
                'status': participation.status,
                'response_message': participation.response_message
            }
        })


class ParticipantActionsView(APIView):
    """Ações em lote para participantes"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, meeting_id):
        meeting = get_object_or_404(Meeting, id=meeting_id)
        
        # Verificar permissão
        if not meeting.can_edit(request.user):
            return Response(
                {'error': 'Sem permissão para gerenciar participantes desta reunião'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        participant_ids = request.data.get('participant_ids', [])
        action = request.data.get('action')  # 'approve_all', 'reject_all', 'remove_all'
        response_message = request.data.get('response_message', '')
        
        if not participant_ids or not action:
            return Response(
                {'error': 'participant_ids e action são obrigatórios'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if action not in ['approve_all', 'reject_all', 'remove_all']:
            return Response(
                {'error': 'action inválida'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar participações
        participations = MeetingParticipation.objects.filter(
            meeting=meeting,
            participant_id__in=participant_ids
        )
        
        if not participations.exists():
            return Response(
                {'error': 'Nenhuma participação encontrada'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        processed_count = 0
        errors = []
        
        for participation in participations:
            try:
                if action == 'approve_all':
                    if participation.status == 'pending':
                        # Verificar limite
                        if meeting.max_participants:
                            current_approved = meeting.get_participant_count()
                            if current_approved >= meeting.max_participants:
                                errors.append(f'Limite atingido - {participation.participant.get_full_name()}')
                                continue
                        
                        participation.status = 'approved'
                        participation.response_message = response_message
                        participation.approved_by = request.user
                        participation.save()
                        processed_count += 1
                
                elif action == 'reject_all':
                    if participation.status == 'pending':
                        participation.status = 'rejected'
                        participation.response_message = response_message
                        participation.approved_by = request.user
                        participation.save()
                        processed_count += 1
                
                elif action == 'remove_all':
                    participation.delete()
                    processed_count += 1
                    
            except Exception as e:
                errors.append(f'Erro com {participation.participant.get_full_name()}: {str(e)}')
        
        return Response({
            'message': f'{processed_count} participações processadas',
            'processed_count': processed_count,
            'errors': errors if errors else None
        })


class MyParticipationsView(APIView):
    """Listar participações do usuário logado"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Buscar participações do usuário
        participations = MeetingParticipation.objects.filter(
            participant=user
        ).select_related('meeting', 'meeting__category').order_by('-created_at')
        
        # Filtrar por status se especificado
        status_filter = request.query_params.get('status')
        if status_filter:
            participations = participations.filter(status=status_filter)
        
        # Filtrar por período
        period = request.query_params.get('period')  # 'upcoming', 'past', 'today'
        if period == 'upcoming':
            participations = participations.filter(
                meeting__meeting_date__gte=timezone.now().date()
            )
        elif period == 'past':
            participations = participations.filter(
                meeting__meeting_date__lt=timezone.now().date()
            )
        elif period == 'today':
            participations = participations.filter(
                meeting__meeting_date=timezone.now().date()
            )
        
        # Serializar dados
        participations_data = []
        for participation in participations:
            meeting = participation.meeting
            meeting_info = {
                'id': meeting.id,
                'title': meeting.title,
                'responsible': meeting.responsible,
                'meeting_date': meeting.meeting_date,
                'meeting_time': meeting.meeting_time,
                'duration_formatted': meeting.duration_formatted,
                'category_name': meeting.category.name,
                'status': meeting.status,
                'is_upcoming': meeting.is_upcoming,
                'is_in_progress': meeting.is_in_progress,
                'meeting_url': meeting.meeting_url if participation.status == 'approved' else None,
            }
            
            participation_info = {
                'id': participation.id,
                'status': participation.status,
                'message': participation.message,
                'response_message': participation.response_message,
                'attended': participation.attended,
                'joined_at': participation.joined_at,
                'created_at': participation.created_at,
                'meeting': meeting_info
            }
            participations_data.append(participation_info)
        
        # Estatísticas
        all_participations = MeetingParticipation.objects.filter(participant=user)
        stats = {
            'total': all_participations.count(),
            'approved': all_participations.filter(status='approved').count(),
            'pending': all_participations.filter(status='pending').count(),
            'attended': all_participations.filter(attended=True).count(),
        }
        
        return Response({
            'stats': stats,
            'participations': participations_data
        })


# ===== VIEWS GERAIS =====

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
        return Response({'message': 'Use /manage-participant/ com action=approve'})

class RejectParticipantView(APIView):
    permission_classes = [IsAuthenticated]  
    def post(self, request, meeting_id):
        return Response({'message': 'Use /manage-participant/ com action=reject'})

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