# meetings/views.py - VERSÃO MÍNIMA FUNCIONAL

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action, api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

# Imports dos modelos
from .models import (
    Category, 
    Meeting, 
    Comment, 
    Rating, 
    MeetingParticipation, 
    MeetingCooperation
)

# Imports dos serializers
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

from accounts.models import User


# ===== VIEWSETS PRINCIPAIS =====

class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet para categorias"""
    queryset = Category.objects.filter(is_active=True).order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class MeetingViewSet(viewsets.ModelViewSet):
    """ViewSet para reuniões"""
    queryset = Meeting.objects.all()
    permission_classes = [AllowAny]  # Simplificado para teste
    
    def get_serializer_class(self):
        """Serializer por ação"""
        if self.action == 'list':
            return MeetingListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return MeetingCreateUpdateSerializer
        else:
            return MeetingDetailSerializer
    
    def get_queryset(self):
        """QuerySet otimizado"""
        queryset = Meeting.objects.select_related('category', 'creator')
        
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status='published')
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Criação com usuário"""
        user = self.request.user if self.request.user.is_authenticated else None
        if user:
            serializer.save(creator=user)
        else:
            serializer.save()


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet para comentários"""
    queryset = Comment.objects.filter(is_active=True).select_related('author', 'meeting')
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class RatingViewSet(viewsets.ModelViewSet):
    """ViewSet para avaliações"""
    queryset = Rating.objects.all().select_related('user', 'meeting')
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ===== VIEWS DE PARTICIPAÇÃO =====

class JoinMeetingView(APIView):
    """Solicitar participação em reunião"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, meeting_id):
        meeting = get_object_or_404(Meeting, id=meeting_id)
        
        # Verificar se já participa
        existing = MeetingParticipation.objects.filter(
            meeting=meeting,
            participant=request.user
        ).first()
        
        if existing:
            return Response({
                'message': f'Você já está participando (Status: {existing.status})'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Criar participação
        participation_status = 'approved' if not meeting.requires_approval else 'pending'
        
        MeetingParticipation.objects.create(
            meeting=meeting,
            participant=request.user,
            status=participation_status,
            message=request.data.get('message', '')
        )
        
        return Response({
            'message': 'Participação confirmada!' if participation_status == 'approved' else 'Solicitação enviada!',
            'status': participation_status
        }, status=status.HTTP_201_CREATED)


class LeaveMeetingView(APIView):
    """Cancelar participação"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, meeting_id):
        meeting = get_object_or_404(Meeting, id=meeting_id)
        
        try:
            participation = MeetingParticipation.objects.get(
                meeting=meeting,
                participant=request.user
            )
            participation.delete()
            
            return Response({
                'message': 'Participação cancelada com sucesso!'
            })
            
        except MeetingParticipation.DoesNotExist:
            return Response({
                'error': 'Você não está participando desta reunião'
            }, status=status.HTTP_400_BAD_REQUEST)


class MeetingParticipantsView(APIView):
    """Listar participantes"""
    permission_classes = [AllowAny]
    
    def get(self, request, meeting_id):
        meeting = get_object_or_404(Meeting, id=meeting_id)
        
        participations = MeetingParticipation.objects.filter(
            meeting=meeting
        ).select_related('participant')
        
        status_filter = request.query_params.get('status', 'approved')
        if status_filter != 'all':
            participations = participations.filter(status=status_filter)
        
        participants_data = []
        for p in participations:
            participants_data.append({
                'id': p.id,
                'participant': {
                    'id': p.participant.id,
                    'name': p.participant.get_full_name(),
                    'username': p.participant.username
                },
                'status': p.status,
                'message': p.message,
                'created_at': p.created_at
            })
        
        return Response({
            'total': participations.count(),
            'participants': participants_data
        })


class ManageParticipantView(APIView):
    """Gerenciar participantes"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, meeting_id):
        meeting = get_object_or_404(Meeting, id=meeting_id)
        
        if meeting.creator != request.user:
            return Response({
                'error': 'Sem permissão'
            }, status=status.HTTP_403_FORBIDDEN)
        
        participant_id = request.data.get('participant_id')
        action = request.data.get('action')
        
        if not participant_id or action not in ['approve', 'reject']:
            return Response({
                'error': 'participant_id e action (approve/reject) são obrigatórios'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            participation = MeetingParticipation.objects.get(
                meeting=meeting,
                participant_id=participant_id
            )
            
            participation.status = 'approved' if action == 'approve' else 'rejected'
            participation.response_message = request.data.get('response_message', '')
            participation.save()
            
            return Response({
                'message': f'Participação {"aprovada" if action == "approve" else "rejeitada"}'
            })
            
        except MeetingParticipation.DoesNotExist:
            return Response({
                'error': 'Participação não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)


class MyParticipationsView(APIView):
    """Minhas participações"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        participations = MeetingParticipation.objects.filter(
            participant=request.user
        ).select_related('meeting')
        
        participations_data = []
        for p in participations:
            participations_data.append({
                'id': p.id,
                'meeting': {
                    'id': p.meeting.id,
                    'title': p.meeting.title,
                    'meeting_date': p.meeting.meeting_date,
                    'meeting_time': p.meeting.meeting_time
                },
                'status': p.status,
                'created_at': p.created_at
            })
        
        return Response({
            'total': participations.count(),
            'participations': participations_data
        })


# ===== VIEWS DE COOPERADORES =====

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_cooperators(request, meeting_id):
    """Listar cooperadores de uma reunião"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id)
        
        status_filter = request.GET.get('status', 'approved')
        cooperations = MeetingCooperation.objects.filter(meeting=meeting)
        
        if status_filter == 'pending':
            cooperations = cooperations.filter(status='pending')
        elif status_filter == 'approved':
            cooperations = cooperations.filter(
                status='approved',
                expires_at__gt=timezone.now()
            )
        elif status_filter != 'all':
            return Response({
                'error': 'Status inválido. Use: pending, approved ou all'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cooperations = cooperations.select_related('cooperator')
        
        cooperators_data = []
        for cooperation in cooperations:
            cooperators_data.append({
                'id': cooperation.id,
                'cooperator': {
                    'id': cooperation.cooperator.id,
                    'name': cooperation.cooperator.get_full_name(),
                    'username': cooperation.cooperator.username
                },
                'status': cooperation.status,
                'permissions': cooperation.permissions,
                'created_at': cooperation.created_at,
                'expires_at': cooperation.expires_at
            })
        
        return Response({
            'success': True,
            'total': cooperations.count(),
            'cooperators': cooperators_data
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_cooperation(request, meeting_id):
    """Solicitar cooperação"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id)
        
        if meeting.creator == request.user:
            return Response({
                'error': 'Não pode solicitar cooperação em sua própria reunião'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar se já existe
        existing = MeetingCooperation.objects.filter(
            meeting=meeting,
            cooperator=request.user
        ).first()
        
        if existing:
            return Response({
                'error': f'Já existe solicitação (Status: {existing.status})'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Criar solicitação
        permissions = request.data.get('permissions', ['view'])
        valid_permissions = ['view', 'edit', 'moderate', 'manage_participants']
        
        if not all(p in valid_permissions for p in permissions):
            return Response({
                'error': f'Permissões inválidas. Válidas: {valid_permissions}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cooperation = MeetingCooperation.objects.create(
            meeting=meeting,
            cooperator=request.user,
            permissions=permissions,
            message=request.data.get('message', ''),
            status='pending'
        )
        
        return Response({
            'success': True,
            'message': 'Solicitação enviada com sucesso',
            'cooperation_id': cooperation.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def manage_cooperation(request, meeting_id):
    """Gerenciar cooperação"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id)
        
        if meeting.creator != request.user:
            return Response({
                'error': 'Sem permissão'
            }, status=status.HTTP_403_FORBIDDEN)
        
        cooperation_id = request.data.get('cooperation_id')
        action = request.data.get('action')
        
        if not cooperation_id or action not in ['approve', 'reject']:
            return Response({
                'error': 'cooperation_id e action (approve/reject) obrigatórios'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cooperation = get_object_or_404(
            MeetingCooperation,
            id=cooperation_id,
            meeting=meeting
        )
        
        if cooperation.status != 'pending':
            return Response({
                'error': 'Solicitação já processada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cooperation.status = 'approved' if action == 'approve' else 'rejected'
        if action == 'approve':
            cooperation.expires_at = timezone.now() + timedelta(days=30)
        cooperation.response_message = request.data.get('response_message', '')
        cooperation.save()
        
        return Response({
            'success': True,
            'message': f'Cooperação {"aprovada" if action == "approve" else "rejeitada"}'
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cooperation_batch_actions(request, meeting_id):
    """Ações em lote"""
    return Response({
        'message': 'Endpoint em desenvolvimento'
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def manage_cooperation_permissions(request, meeting_id, cooperation_id):
    """Gerenciar permissões"""
    try:
        meeting = get_object_or_404(Meeting, id=meeting_id)
        cooperation = get_object_or_404(MeetingCooperation, id=cooperation_id, meeting=meeting)
        
        if meeting.creator != request.user:
            return Response({
                'error': 'Sem permissão'
            }, status=status.HTTP_403_FORBIDDEN)
        
        permissions = request.data.get('permissions', [])
        valid_permissions = ['view', 'edit', 'moderate', 'manage_participants']
        
        if not all(p in valid_permissions for p in permissions):
            return Response({
                'error': f'Permissões inválidas. Válidas: {valid_permissions}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cooperation.permissions = permissions
        cooperation.save()
        
        return Response({
            'success': True,
            'message': 'Permissões atualizadas'
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_cooperations(request):
    """Minhas cooperações"""
    cooperations = MeetingCooperation.objects.filter(
        cooperator=request.user
    ).select_related('meeting')
    
    cooperations_data = []
    for c in cooperations:
        cooperations_data.append({
            'id': c.id,
            'meeting': {
                'id': c.meeting.id,
                'title': c.meeting.title,
                'creator': c.meeting.creator.get_full_name()
            },
            'status': c.status,
            'permissions': c.permissions,
            'created_at': c.created_at,
            'expires_at': c.expires_at
        })
    
    return Response({
        'total': cooperations.count(),
        'cooperations': cooperations_data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cooperation_stats(request):
    """Estatísticas"""
    user_meetings = Meeting.objects.filter(creator=request.user)
    
    stats = {
        'total_meetings': user_meetings.count(),
        'total_cooperators': MeetingCooperation.objects.filter(
            meeting__creator=request.user,
            status='approved'
        ).count(),
        'pending_requests': MeetingCooperation.objects.filter(
            meeting__creator=request.user,
            status='pending'
        ).count()
    }
    
    return Response({
        'success': True,
        'stats': stats
    })


# ===== VIEWS ADICIONAIS =====

class UpcomingMeetingsView(APIView):
    """Próximas reuniões"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        meetings = Meeting.objects.filter(
            status='published',
            meeting_date__gte=timezone.now().date()
        ).select_related('category', 'creator')[:10]
        
        serializer = MeetingListSerializer(meetings, many=True, context={'request': request})
        return Response(serializer.data)


class MyMeetingsView(APIView):
    """Minhas reuniões"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        created = Meeting.objects.filter(creator=request.user)
        serializer = MeetingListSerializer(created, many=True, context={'request': request})
        return Response({'created': serializer.data})


class SearchMeetingsView(APIView):
    """Busca"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        meetings = Meeting.objects.filter(status='published')
        
        q = request.query_params.get('q')
        if q:
            meetings = meetings.filter(
                Q(title__icontains=q) | Q(description__icontains=q)
            )
        
        serializer = MeetingListSerializer(meetings[:20], many=True, context={'request': request})
        return Response(serializer.data)


# Views vazias para compatibilidade
class MeetingCommentsView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, meeting_id):
        return Response([])

class MeetingRatingsView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, meeting_id):
        return Response([])

class MyMeetingRatingView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, meeting_id):
        return Response({'message': 'Nenhuma avaliação'})

class ApproveParticipantView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, meeting_id):
        return Response({'message': 'Use manage-participant'})

class RejectParticipantView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, meeting_id):
        return Response({'message': 'Use manage-participant'})

class ApproveCooperationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, meeting_id):
        return Response({'message': 'Use manage-cooperation'})

class RejectCooperationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, meeting_id):
        return Response({'message': 'Use manage-cooperation'})