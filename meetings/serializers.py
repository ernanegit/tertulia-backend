from rest_framework import serializers
from .models import Category, Meeting, Comment, Rating, MeetingParticipation, MeetingCooperation


class CategorySerializer(serializers.ModelSerializer):
    """Serializer para categorias"""
    
    meetings_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'color', 'is_active', 'meetings_count', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_meetings_count(self, obj):
        """Conta reuniões ativas da categoria"""
        return obj.meetings.filter(status='published').count()


class MeetingSerializer(serializers.ModelSerializer):
    """Serializer para reuniões"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    creator_name = serializers.CharField(source='creator.get_full_name', read_only=True)
    participant_count = serializers.SerializerMethodField()
    can_join = serializers.SerializerMethodField()
    is_upcoming = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Meeting
        fields = [
            'id', 'title', 'responsible', 'description', 'category', 'category_name',
            'meeting_date', 'meeting_time', 'meeting_url', 'creator', 'creator_name',
            'status', 'participant_count', 'can_join', 'is_upcoming', 'created_at'
        ]
        read_only_fields = ['id', 'creator', 'created_at']
    
    def get_participant_count(self, obj):
        """Conta participantes aprovados"""
        return obj.meetingparticipation_set.filter(status='approved').count()
    
    def get_can_join(self, obj):
        """Verifica se o usuário atual pode participar"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_join(request.user)
        return False
    
    def validate_meeting_date(self, value):
        """Valida se a data não é no passado"""
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("A data da reunião não pode ser no passado.")
        return value


class CommentSerializer(serializers.ModelSerializer):
    """Serializer para comentários"""
    
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    meeting_title = serializers.CharField(source='meeting.title', read_only=True)
    
    class Meta:
        model = Comment
        fields = [
            'id', 'meeting', 'meeting_title', 'author', 'author_name', 
            'content', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']


class RatingSerializer(serializers.ModelSerializer):
    """Serializer para avaliações"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    meeting_title = serializers.CharField(source='meeting.title', read_only=True)
    
    class Meta:
        model = Rating
        fields = [
            'id', 'meeting', 'meeting_title', 'user', 'user_name',
            'rating', 'review', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate_rating(self, value):
        """Valida se o rating está entre 1 e 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("A avaliação deve ser entre 1 e 5 estrelas.")
        return value


class MeetingParticipationSerializer(serializers.ModelSerializer):
    """Serializer para participações em reuniões"""
    
    participant_name = serializers.CharField(source='participant.get_full_name', read_only=True)
    meeting_title = serializers.CharField(source='meeting.title', read_only=True)
    
    class Meta:
        model = MeetingParticipation
        fields = [
            'id', 'meeting', 'meeting_title', 'participant', 'participant_name',
            'status', 'message', 'attended', 'created_at'
        ]
        read_only_fields = ['id', 'participant', 'created_at']


class MeetingCooperationSerializer(serializers.ModelSerializer):
    """Serializer para cooperações em reuniões"""
    
    cooperator_name = serializers.CharField(source='cooperator.get_full_name', read_only=True)
    meeting_title = serializers.CharField(source='meeting.title', read_only=True)
    
    class Meta:
        model = MeetingCooperation
        fields = [
            'id', 'meeting', 'meeting_title', 'cooperator', 'cooperator_name',
            'status', 'created_at'
        ]
        read_only_fields = ['id', 'cooperator', 'created_at']