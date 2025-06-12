# meetings/serializers.py - VERSÃO COMPLETA COM TODOS OS SERIALIZERS

from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q

# Imports dos modelos
from .models import (
    Category, 
    Meeting, 
    Comment, 
    Rating, 
    MeetingParticipation, 
    MeetingCooperation,
    Notification
)


# ===== SERIALIZERS BÁSICOS =====

class UserBasicSerializer(serializers.ModelSerializer):
    """Serializer básico para usuário (sem informações sensíveis)"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name']


# ===== CATEGORY SERIALIZERS =====

class CategorySerializer(serializers.ModelSerializer):
    """Serializer completo para categorias"""
    meetings_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'color', 'icon', 'is_active',
            'display_order', 'meetings_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_meetings_count(self, obj):
        """Conta reuniões ativas da categoria"""
        return obj.meetings.filter(status='published').count()


# ===== MEETING SERIALIZERS =====

class MeetingBasicSerializer(serializers.ModelSerializer):
    """Serializer básico para reunião"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Meeting
        fields = ['id', 'title', 'description', 'meeting_date', 'meeting_time', 'category_name']


class MeetingListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de reuniões"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    creator_name = serializers.CharField(source='creator.get_full_name', read_only=True)
    participant_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    is_upcoming = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Meeting
        fields = [
            'id', 'title', 'responsible', 'description', 'category', 'category_name',
            'category_color', 'meeting_date', 'meeting_time', 'duration_minutes',
            'duration_formatted', 'meeting_format', 'creator', 'creator_name',
            'status', 'max_participants', 'participant_count', 'average_rating',
            'is_upcoming', 'view_count', 'created_at'
        ]
        read_only_fields = ['id', 'creator', 'view_count', 'created_at']
    
    def get_participant_count(self, obj):
        return MeetingParticipation.objects.filter(meeting=obj, status='approved').count()
    
    def get_average_rating(self, obj):
        ratings = Rating.objects.filter(meeting=obj)
        if ratings.exists():
            return round(sum(r.rating for r in ratings) / len(ratings), 1)
        return 0
    
    def get_is_upcoming(self, obj):
        return obj.meeting_date >= timezone.now().date()
    
    def get_duration_formatted(self, obj):
        hours = obj.duration_minutes // 60
        minutes = obj.duration_minutes % 60
        if hours and minutes:
            return f"{hours}h {minutes}min"
        elif hours:
            return f"{hours}h"
        else:
            return f"{minutes}min"


class MeetingDetailSerializer(serializers.ModelSerializer):
    """Serializer detalhado para reuniões"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    creator_name = serializers.CharField(source='creator.get_full_name', read_only=True)
    participant_count = serializers.SerializerMethodField()
    cooperator_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_upcoming = serializers.SerializerMethodField()
    is_in_progress = serializers.SerializerMethodField()
    duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Meeting
        fields = [
            'id', 'title', 'responsible', 'description', 'category', 'category_name',
            'meeting_date', 'meeting_time', 'duration_minutes', 'duration_formatted',
            'timezone', 'meeting_format', 'meeting_url', 'backup_url',
            'meeting_password', 'max_participants', 'requires_approval',
            'allow_comments', 'allow_ratings', 'is_recurring',
            'agenda', 'prerequisites', 'materials', 'tags',
            'creator', 'creator_name', 'status', 'approved_at', 'rejection_reason',
            'participant_count', 'cooperator_count', 'average_rating', 'comments_count',
            'is_upcoming', 'is_in_progress', 'view_count', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'creator', 'approved_at', 'view_count', 'created_at', 'updated_at'
        ]
    
    def get_participant_count(self, obj):
        return MeetingParticipation.objects.filter(meeting=obj, status='approved').count()
    
    def get_cooperator_count(self, obj):
        return MeetingCooperation.objects.filter(
            meeting=obj, 
            status='approved',
            expires_at__gt=timezone.now()
        ).count()
    
    def get_average_rating(self, obj):
        ratings = Rating.objects.filter(meeting=obj)
        if ratings.exists():
            return round(sum(r.rating for r in ratings) / len(ratings), 1)
        return 0
    
    def get_comments_count(self, obj):
        return Comment.objects.filter(meeting=obj, is_active=True).count()
    
    def get_is_upcoming(self, obj):
        return obj.meeting_date >= timezone.now().date()
    
    def get_is_in_progress(self, obj):
        now = timezone.now()
        meeting_datetime = timezone.make_aware(
            timezone.datetime.combine(obj.meeting_date, obj.meeting_time)
        )
        end_datetime = meeting_datetime + timezone.timedelta(minutes=obj.duration_minutes)
        return meeting_datetime <= now <= end_datetime
    
    def get_duration_formatted(self, obj):
        hours = obj.duration_minutes // 60
        minutes = obj.duration_minutes % 60
        if hours and minutes:
            return f"{hours}h {minutes}min"
        elif hours:
            return f"{hours}h"
        else:
            return f"{minutes}min"


class MeetingCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criação/edição de reuniões"""
    
    class Meta:
        model = Meeting
        fields = [
            'title', 'responsible', 'description', 'category',
            'meeting_date', 'meeting_time', 'duration_minutes', 'timezone',
            'meeting_format', 'meeting_url', 'backup_url', 'meeting_password',
            'max_participants', 'requires_approval', 'allow_comments', 
            'allow_ratings', 'is_recurring', 'agenda', 'prerequisites', 
            'materials', 'tags'
        ]
    
    def validate_meeting_date(self, value):
        """Valida se a data não é no passado"""
        if value < timezone.now().date():
            raise serializers.ValidationError("A data da reunião não pode ser no passado.")
        return value
    
    def validate_duration_minutes(self, value):
        """Valida duração"""
        if value < 15 or value > 480:
            raise serializers.ValidationError("Duração deve ser entre 15 minutos e 8 horas.")
        return value


# ===== COOPERATION SERIALIZERS =====

class CooperationSerializer(serializers.ModelSerializer):
    """Serializer completo para cooperação"""
    cooperator = UserBasicSerializer(read_only=True)
    meeting = MeetingBasicSerializer(read_only=True)
    
    # Campos calculados
    is_active = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = MeetingCooperation
        fields = [
            'id', 'cooperator', 'meeting', 'permissions', 'status', 'status_display',
            'message', 'response_message', 'created_at', 'approved_at', 
            'expires_at', 'is_active', 'days_until_expiry'
        ]
    
    def get_is_active(self, obj):
        """Verifica se a cooperação está ativa"""
        if obj.status != 'approved':
            return False
        if not obj.expires_at:
            return False
        return obj.expires_at > timezone.now()
    
    def get_days_until_expiry(self, obj):
        """Calcula dias até expirar"""
        if obj.status != 'approved' or not obj.expires_at:
            return None
        delta = obj.expires_at - timezone.now()
        return max(0, delta.days)
    
    def get_status_display(self, obj):
        """Texto amigável para status"""
        status_map = {
            'pending': 'Pendente',
            'approved': 'Aprovado',
            'rejected': 'Rejeitado'
        }
        return status_map.get(obj.status, obj.status)


# Alias para compatibilidade
MeetingCooperationSerializer = CooperationSerializer


# ===== PARTICIPATION SERIALIZERS =====

class MeetingParticipationSerializer(serializers.ModelSerializer):
    """Serializer para participações em reuniões"""
    participant_name = serializers.CharField(source='participant.get_full_name', read_only=True)
    meeting_title = serializers.CharField(source='meeting.title', read_only=True)
    
    class Meta:
        model = MeetingParticipation
        fields = [
            'id', 'meeting', 'meeting_title', 'participant', 'participant_name',
            'status', 'message', 'response_message', 'attended', 
            'joined_at', 'left_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'participant', 'created_at', 'updated_at']


# ===== COMMENT SERIALIZERS =====

class CommentSerializer(serializers.ModelSerializer):
    """Serializer para comentários"""
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    meeting_title = serializers.CharField(source='meeting.title', read_only=True)
    replies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'meeting', 'meeting_title', 'author', 'author_name',
            'content', 'parent', 'is_active', 'is_pinned', 'likes_count',
            'replies_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'author', 'likes_count', 'created_at', 'updated_at']
    
    def get_replies_count(self, obj):
        return Comment.objects.filter(parent=obj, is_active=True).count()
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['author'] = request.user
        return super().create(validated_data)


# ===== RATING SERIALIZERS =====

class RatingSerializer(serializers.ModelSerializer):
    """Serializer para avaliações"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    meeting_title = serializers.CharField(source='meeting.title', read_only=True)
    rating_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Rating
        fields = [
            'id', 'meeting', 'meeting_title', 'user', 'user_name',
            'rating', 'rating_display', 'review', 'is_anonymous',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_rating_display(self, obj):
        """Retorna rating como estrelas"""
        return '★' * obj.rating + '☆' * (5 - obj.rating)
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("A avaliação deve ser entre 1 e 5 estrelas.")
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)


# ===== SERIALIZERS AUXILIARES =====

class CooperationRequestSerializer(serializers.Serializer):
    """Serializer para solicitação de cooperação"""
    permissions = serializers.ListField(
        child=serializers.CharField(),
        min_length=1,
        help_text="Lista de permissões solicitadas"
    )
    message = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Mensagem opcional explicando o motivo da solicitação"
    )
    
    def validate_permissions(self, value):
        """Validar permissões"""
        valid_permissions = ['view', 'edit', 'moderate', 'manage_participants']
        invalid = [p for p in value if p not in valid_permissions]
        if invalid:
            raise serializers.ValidationError(
                f"Permissões inválidas: {invalid}. Válidas: {valid_permissions}"
            )
        return value


class CooperationManageSerializer(serializers.Serializer):
    """Serializer para gerenciar cooperação"""
    cooperation_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    response_message = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Mensagem de resposta opcional"
    )


class JoinMeetingSerializer(serializers.Serializer):
    """Serializer para solicitação de participação"""
    message = serializers.CharField(
        max_length=500, 
        required=False, 
        allow_blank=True,
        help_text="Mensagem opcional ao solicitar participação"
    )