from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone

from .models import Category, Meeting, Comment, Rating, MeetingParticipation, MeetingCooperation
from .serializers import (
    CategorySerializer, MeetingListSerializer, MeetingDetailSerializer,
    MeetingCreateUpdateSerializer, CommentSerializer, RatingSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet para categorias"""
    queryset = Category.objects.filter(is_active=True).order_by('display_order', 'name')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class MeetingViewSet(viewsets.ModelViewSet):
    """ViewSet para reuniões"""
    queryset = Meeting.objects.all()
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MeetingListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return MeetingCreateUpdateSerializer
        else:
            return MeetingDetailSerializer
    
    def get_queryset(self):
        queryset = Meeting.objects.select_related('category', 'creator')
        
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status='published')
        
        return queryset.order_by('-meeting_date', '-meeting_time')
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet para comentários"""
    queryset = Comment.objects.filter(is_active=True)
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class RatingViewSet(viewsets.ModelViewSet):
    """ViewSet para avaliações"""
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Views específicas simplificadas
class JoinMeetingView(APIView):
    """Solicitar participação em reunião"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, meeting_id):
        meeting = get_object_or_404(Meeting, id=meeting_id)
        
        participation, created = MeetingParticipation.objects.get_or_create(
            meeting=meeting,
            participant=request.user,
            defaults={
                'status': 'approved' if not meeting.requires_approval else 'pending',
                'message': request.data.get('message', '')
            }
        )
        
        if created:
            return Response({
                'message': 'Solicitação enviada com sucesso!' if meeting.requires_approval else 'Participação confirmada!',
                'status': participation.status
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
            
            return Response({'message': 'Participação cancelada com sucesso!'})
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
        ).order_by('meeting_date', 'meeting_time')[:3]
        
        serializer = MeetingListSerializer(upcoming_meetings, many=True, context={'request': request})
        return Response(serializer.data)


class MyMeetingsView(APIView):
    """Reuniões do usuário logado"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        created = Meeting.objects.filter(creator=user)
        participated = Meeting.objects.filter(
            meetingparticipation__participant=user,
            meetingparticipation__status='approved'
        )
        
        return Response({
            'created': MeetingListSerializer(created, many=True, context={'request': request}).data,
            'participated': MeetingListSerializer(participated, many=True, context={'request': request}).data
        })


# Views temporárias básicas
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
        return Response({'message': 'Funcionalidade em desenvolvimento'})

class MeetingRatingsView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, meeting_id):
        return Response({'message': 'Funcionalidade em desenvolvimento'})

class MyMeetingRatingView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, meeting_id):
        return Response({'message': 'Funcionalidade em desenvolvimento'})

class SearchMeetingsView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response({'message': 'Funcionalidade em desenvolvimento'})