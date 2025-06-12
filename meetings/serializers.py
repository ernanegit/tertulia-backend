# meetings/serializers.py - CORREÇÃO COMPLETA DOS IMPORTS

from rest_framework import serializers  # ✅ IMPORT PRINCIPAL
from django.utils import timezone  # ✅ IMPORT FALTANTE
from django.db.models import Q  # ✅ PARA CONSULTAS COMPLEXAS

# ✅ IMPORTS DOS MODELOS
from .models import (
    Category, 
    Meeting, 
    Comment, 
    Rating, 
    MeetingParticipation, 
    MeetingCooperation, 
    Notification
)


class CategorySerializer(serializers.ModelSerializer):
    """Serializer completo para categorias"""
    
    meetings_count = serializers.SerializerMethodField()
    active_meetings_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'color', 'icon', 'is_active',
            'display_order', 'meetings_count', 'active_meetings_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_meetings_count(self, obj):
        """Conta todas as reuniões da categoria"""
        return obj.meetings.count()
    
    def get_active_meetings_count(self, obj):
        """Conta reuniões ativas da categoria"""
        return obj.get_active_meetings_count()


class MeetingListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de reuniões"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    creator_name = serializers.CharField(source='creator.get_full_name', read_only=True)
    participant_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    can_join = serializers.SerializerMethodField()
    user_participation_status = serializers.SerializerMethodField()
    time_until_start = serializers.SerializerMethodField()
    tags_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Meeting
        fields = [
            'id', 'title', 'responsible', 'description', 'category', 'category_name',
            'category_color', 'meeting_date', 'meeting_time', 'duration_minutes',
            'duration_formatted', 'meeting_format', 'creator', 'creator_name',
            'status', 'access_type', 'max_participants', 'participant_count',
            'average_rating', 'can_join', 'user_participation_status',
            'is_upcoming', 'is_in_progress', 'is_finished', 'time_until_start',
            'tags_list', 'view_count', 'created_at'
        ]
        read_only_fields = [
            'id', 'creator', 'duration_formatted', 'is_upcoming', 'is_in_progress',
            'is_finished', 'view_count', 'created_at'
        ]
    
    def get_participant_count(self, obj):
        return obj.get_participant_count()
    
    def get_average_rating(self, obj):
        return obj.get_average_rating()
    
    def get_can_join(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_join(request.user)
        return False
    
    def get_user_participation_status(self, obj):
        """Retorna status de participação do usuário atual"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                participation = obj.meetingparticipation_set.get(participant=request.user)
                return participation.status
            except MeetingParticipation.DoesNotExist:
                return None
        return None
    
    def get_time_until_start(self, obj):
        """Tempo até o início em segundos (para countdown)"""
        if obj.is_upcoming:
            delta = obj.time_until_start
            return int(delta.total_seconds())
        return 0
    
    def get_tags_list(self, obj):
        return obj.get_tags_list()


class MeetingDetailSerializer(serializers.ModelSerializer):
    """Serializer detalhado para reuniões"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    creator_name = serializers.CharField(source='creator.get_full_name', read_only=True)
    creator_email = serializers.CharField(source='creator.email', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    # Estatísticas
    participant_count = serializers.SerializerMethodField()
    pending_requests_count = serializers.SerializerMethodField()
    cooperator_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    
    # Status do usuário
    can_join = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    user_participation_status = serializers.SerializerMethodField()
    user_cooperation_status = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    
    # Campos calculados
    meeting_datetime = serializers.DateTimeField(read_only=True)
    end_datetime = serializers.DateTimeField(read_only=True)
    time_until_start = serializers.SerializerMethodField()
    tags_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Meeting
        fields = [
            # Básicos
            'id', 'title', 'responsible', 'description', 'category', 'category_name',
            'category_color', 'meeting_date', 'meeting_time', 'duration_minutes',
            'duration_formatted', 'timezone', 'meeting_datetime', 'end_datetime',
            
            # Formato e acesso
            'meeting_format', 'meeting_url', 'backup_url', 'meeting_password',
            'access_type', 'max_participants', 'requires_approval',
            
            # Configurações
            'allow_comments', 'allow_ratings', 'is_recurring',
            
            # Conteúdo adicional
            'agenda', 'prerequisites', 'materials', 'tags', 'tags_list',
            
            # Relacionamentos
            'creator', 'creator_name', 'creator_email',
            'approved_by', 'approved_by_name', 'approved_at',
            
            # Status
            'status', 'rejection_reason', 'published_at',
            
            # Estatísticas
            'participant_count', 'pending_requests_count', 'cooperator_count',
            'average_rating', 'comments_count', 'view_count', 'join_attempts',
            
            # Status do usuário
            'can_join', 'can_edit', 'user_participation_status',
            'user_cooperation_status', 'user_rating',
            
            # Estados
            'is_upcoming', 'is_in_progress', 'is_finished', 'time_until_start',
            
            # Timestamps
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'creator', 'approved_by', 'approved_at', 'published_at',
            'view_count', 'join_attempts', 'created_at', 'updated_at'
        ]
    
    def get_participant_count(self, obj):
        return obj.get_participant_count()
    
    def get_pending_requests_count(self, obj):
        return obj.get_pending_requests_count()
    
    def get_cooperator_count(self, obj):
        return obj.get_cooperator_count()
    
    def get_average_rating(self, obj):
        return obj.get_average_rating()
    
    def get_comments_count(self, obj):
        return obj.comments.filter(is_active=True).count()
    
    def get_can_join(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_join(request.user)
        return False
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_edit(request.user)
        return False
    
    def get_user_participation_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                participation = obj.meetingparticipation_set.get(participant=request.user)
                return {
                    'status': participation.status,
                    'message': participation.message,
                    'created_at': participation.created_at,
                    'attended': participation.attended
                }
            except MeetingParticipation.DoesNotExist:
                return None
        return None
    
    def get_user_cooperation_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                cooperation = obj.meetingcooperation_set.get(cooperator=request.user)
                return {
                    'status': cooperation.status,
                    'permissions': cooperation.permissions,
                    'created_at': cooperation.created_at
                }
            except MeetingCooperation.DoesNotExist:
                return None
        return None
    
    def get_user_rating(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                rating = obj.ratings.get(user=request.user)
                return {
                    'rating': rating.rating,
                    'review': rating.review,
                    'created_at': rating.created_at
                }
            except Rating.DoesNotExist:
                return None
        return None
    
    def get_time_until_start(self, obj):
        if obj.is_upcoming:
            delta = obj.time_until_start
            return int(delta.total_seconds())
        return 0
    
    def get_tags_list(self, obj):
        return obj.get_tags_list()


class MeetingCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criação/edição de reuniões"""
    
    class Meta:
        model = Meeting
        fields = [
            'title', 'responsible', 'description', 'category',
            'meeting_date', 'meeting_time', 'duration_minutes', 'timezone',
            'meeting_format', 'meeting_url', 'backup_url', 'meeting_password',
            'access_type', 'max_participants', 'requires_approval',
            'allow_comments', 'allow_ratings', 'is_recurring',
            'agenda', 'prerequisites', 'materials', 'tags'
        ]
    
    def validate_meeting_date(self, value):
        """Valida se a data não é no passado"""
        if value < timezone.now().date():
            raise serializers.ValidationError("A data da reunião não pode ser no passado.")
        return value
    
    def validate_meeting_url(self, value):
        """Valida URL básica"""
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL deve começar com http:// ou https://")
        return value
    
    def validate_duration_minutes(self, value):
        """Valida duração"""
        if value < 15 or value > 480:
            raise serializers.ValidationError("Duração deve ser entre 15 minutos e 8 horas.")
        return value
    
    def validate_max_participants(self, value):
        """Valida limite de participantes"""
        if value is not None and (value < 2 or value > 1000):
            raise serializers.ValidationError("Limite deve ser entre 2 e 1000 participantes.")
        return value
    
    def create(self, validated_data):
        """Criar reunião com creator automático"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['creator'] = request.user
        return super().create(validated_data)


class CommentSerializer(serializers.ModelSerializer):
    """Serializer para comentários"""
    
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    meeting_title = serializers.CharField(source='meeting.title', read_only=True)
    replies_count = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'meeting', 'meeting_title', 'author', 'author_name',
            'content', 'parent', 'is_active', 'is_pinned', 'likes_count',
            'replies_count', 'can_edit', 'replies', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'author', 'likes_count', 'created_at', 'updated_at']
    
    def get_replies_count(self, obj):
        return obj.get_replies_count()
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_edit(request.user)
        return False
    
    def get_replies(self, obj):
        """Retorna respostas do comentário (apenas 1 nível)"""
        if obj.parent is None:  # Só buscar replies para comentários principais
            replies = obj.replies.filter(is_active=True)[:5]  # Limite de 5 replies
            return CommentSerializer(replies, many=True, context=self.context).data
        return []
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['author'] = request.user
        return super().create(validated_data)


class RatingSerializer(serializers.ModelSerializer):
    """Serializer para avaliações"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    meeting_title = serializers.CharField(source='meeting.title', read_only=True)
    rating_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Rating
        fields = [
            'id', 'meeting', 'meeting_title', 'user', 'user_name',
            'rating', 'rating_display', 'review', 'aspects', 'is_anonymous',
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


class MeetingParticipationSerializer(serializers.ModelSerializer):
    """Serializer para participações em reuniões"""
    
    participant_name = serializers.CharField(source='participant.get_full_name', read_only=True)
    participant_email = serializers.CharField(source='participant.email', read_only=True)
    meeting_title = serializers.CharField(source='meeting.title', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    duration_attended_display = serializers.SerializerMethodField()
    
    class Meta:
        model = MeetingParticipation
        fields = [
            'id', 'meeting', 'meeting_title', 'participant', 'participant_name',
            'participant_email', 'status', 'message', 'response_message',
            'attended', 'joined_at', 'left_at', 'duration_attended_display',
            'approved_by', 'approved_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'participant', 'approved_by', 'created_at', 'updated_at'
        ]
    
    def get_duration_attended_display(self, obj):
        duration = obj.duration_attended
        if duration:
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            if hours:
                return f"{hours}h {minutes}min"
            return f"{minutes}min"
        return None


class MeetingCooperationSerializer(serializers.ModelSerializer):
    """Serializer para cooperações em reuniões"""
    
    cooperator_name = serializers.CharField(source='cooperator.get_full_name', read_only=True)
    cooperator_email = serializers.CharField(source='cooperator.email', read_only=True)
    meeting_title = serializers.CharField(source='meeting.title', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    permissions_display = serializers.SerializerMethodField()
    
    class Meta:
        model = MeetingCooperation
        fields = [
            'id', 'meeting', 'meeting_title', 'cooperator', 'cooperator_name',
            'cooperator_email', 'status', 'permissions', 'permissions_display',
            'message', 'response_message', 'expires_at', 'approved_by',
            'approved_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'cooperator', 'approved_by', 'created_at', 'updated_at'
        ]
    
    def get_permissions_display(self, obj):
        if obj.permissions:
            return ', '.join(obj.permissions)
        return 'Nenhuma'


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer para notificações"""
    
    meeting_title = serializers.CharField(source='meeting.title', read_only=True)
    meeting_date = serializers.DateField(source='meeting.meeting_date', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'type_display', 'title', 'message',
            'meeting', 'meeting_title', 'meeting_date',
            'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# ===== SERIALIZERS PARA ENDPOINTS ESPECÍFICOS =====

class JoinMeetingSerializer(serializers.Serializer):
    """Serializer para solicitação de participação"""
    message = serializers.CharField(
        max_length=500, 
        required=False, 
        allow_blank=True,
        help_text="Mensagem opcional ao solicitar participação"
    )


class ApproveRejectParticipantSerializer(serializers.Serializer):
    """Serializer para aprovar/rejeitar participante"""
    participant_id = serializers.IntegerField(
        help_text="ID do participante a ser aprovado/rejeitado"
    )
    response_message = serializers.CharField(
        max_length=500, 
        required=False, 
        allow_blank=True,
        help_text="Mensagem de resposta (opcional)"
    )
    
    def validate_participant_id(self, value):
        """Validar se o participante existe"""
        try:
            from accounts.models import User
            User.objects.get(id=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Participante não encontrado.")


class RequestCooperationSerializer(serializers.Serializer):
    """Serializer para solicitação de cooperação"""
    message = serializers.CharField(
        max_length=500, 
        required=False, 
        allow_blank=True,
        help_text="Mensagem da solicitação"
    )
    permissions = serializers.ListField(
        child=serializers.ChoiceField(choices=[
            'view', 'edit', 'moderate', 'manage_participants'
        ]),
        required=False,
        default=list,
        help_text="Lista de permissões solicitadas"
    )


class MeetingStatsSerializer(serializers.Serializer):
    """Serializer para estatísticas de reuniões"""
    total_meetings = serializers.IntegerField()
    published_meetings = serializers.IntegerField()
    upcoming_meetings = serializers.IntegerField()
    finished_meetings = serializers.IntegerField()
    total_participants = serializers.IntegerField()
    average_rating = serializers.FloatField()
    categories_stats = serializers.DictField()
    
    # Estatísticas por período
    meetings_this_month = serializers.IntegerField(required=False)
    meetings_this_week = serializers.IntegerField(required=False)
    growth_percentage = serializers.FloatField(required=False)


class SearchFilterSerializer(serializers.Serializer):
    """Serializer para filtros de busca"""
    q = serializers.CharField(
        required=False, 
        help_text="Termo de busca geral"
    )
    category = serializers.IntegerField(
        required=False, 
        help_text="ID da categoria"
    )
    date_from = serializers.DateField(
        required=False, 
        help_text="Data inicial (YYYY-MM-DD)"
    )
    date_to = serializers.DateField(
        required=False, 
        help_text="Data final (YYYY-MM-DD)"
    )
    status = serializers.ChoiceField(
        choices=Meeting.STATUS_CHOICES,
        required=False, 
        help_text="Status da reunião"
    )
    format = serializers.ChoiceField(
        choices=Meeting.MEETING_FORMATS,
        required=False, 
        help_text="Formato da reunião"
    )
    upcoming = serializers.BooleanField(
        required=False, 
        help_text="Apenas reuniões futuras"
    )
    has_slots = serializers.BooleanField(
        required=False, 
        help_text="Apenas reuniões com vagas disponíveis"
    )
    min_rating = serializers.FloatField(
        required=False, 
        min_value=1.0,
        max_value=5.0,
        help_text="Avaliação mínima (1.0 a 5.0)"
    )
    tags = serializers.CharField(
        required=False, 
        help_text="Tags separadas por vírgula"
    )
    order_by = serializers.ChoiceField(
        choices=[
            'meeting_date', '-meeting_date',
            'created_at', '-created_at',
            'title', '-title',
            'view_count', '-view_count'
        ],
        required=False,
        default='-meeting_date',
        help_text="Campo para ordenação"
    )
    page = serializers.IntegerField(
        required=False, 
        min_value=1, 
        default=1,
        help_text="Número da página"
    )
    page_size = serializers.IntegerField(
        required=False, 
        min_value=1, 
        max_value=100, 
        default=20,
        help_text="Itens por página (máximo 100)"
    )
    
    def validate(self, attrs):
        """Validações cruzadas"""
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError(
                "Data inicial não pode ser maior que data final."
            )
        
        return attrs


class BulkActionSerializer(serializers.Serializer):
    """Serializer para ações em lote"""
    meeting_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="Lista de IDs das reuniões"
    )
    action = serializers.ChoiceField(
        choices=[
            'publish', 'unpublish', 'cancel', 'delete'
        ],
        help_text="Ação a ser executada"
    )
    reason = serializers.CharField(
        max_length=500,
        required=False,
        help_text="Motivo da ação (opcional)"
    )
    
    def validate_meeting_ids(self, value):
        """Validar se todas as reuniões existem"""
        if len(value) > 50:
            raise serializers.ValidationError(
                "Máximo de 50 reuniões por operação em lote."
            )
        
        existing_count = Meeting.objects.filter(id__in=value).count()
        if existing_count != len(value):
            raise serializers.ValidationError(
                "Algumas reuniões não foram encontradas."
            )
        
        return value


class MeetingTemplateSerializer(serializers.Serializer):
    """Serializer para templates de reunião"""
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=300, required=False)
    template_data = serializers.JSONField(
        help_text="Dados do template (campos da reunião)"
    )
    is_public = serializers.BooleanField(default=False)
    category = serializers.IntegerField(required=False)
    
    def validate_template_data(self, value):
        """Validar estrutura do template"""
        required_fields = ['title', 'duration_minutes', 'meeting_format']
        
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(
                    f"Campo obrigatório '{field}' não encontrado no template."
                )
        
        return value