from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator, URLValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
import re


class Category(models.Model):
    """Modelo para categorias de reuniões"""
    
    name = models.CharField(
        max_length=40, 
        unique=True,
        verbose_name="Nome da Categoria"
    )
    description = models.TextField(
        max_length=200, 
        blank=True,
        verbose_name="Descrição"
    )
    color = models.CharField(
        max_length=7, 
        default="#007bff",
        help_text="Código hexadecimal da cor (ex: #007bff)",
        verbose_name="Cor"
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Nome do ícone (ex: book, microphone)",
        verbose_name="Ícone"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordem de Exibição"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_active_meetings_count(self):
        """Retorna número de reuniões ativas"""
        return self.meetings.filter(status='published').count()


class Meeting(models.Model):
    """Modelo principal para reuniões"""
    
    MEETING_FORMATS = [
        ('youtube', 'YouTube Live'),
        ('zoom', 'Zoom Meeting'),
        ('teams', 'Microsoft Teams'),
        ('meet', 'Google Meet'),
        ('jitsi', 'Jitsi Meet'),
        ('discord', 'Discord'),
        ('other', 'Outro'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('pending_approval', 'Aguardando Aprovação'),
        ('approved', 'Aprovada'),
        ('published', 'Publicada'),
        ('in_progress', 'Em Andamento'),
        ('finished', 'Finalizada'),
        ('cancelled', 'Cancelada'),
        ('postponed', 'Adiada'),
    ]
    
    ACCESS_TYPE_CHOICES = [
        ('public', 'Público - Qualquer um pode solicitar participação'),
        ('private', 'Privado - Apenas por convite'),
        ('restricted', 'Restrito - Aprovação manual obrigatória'),
    ]
    
    # Campos básicos obrigatórios
    responsible = models.CharField(
        max_length=40,
        verbose_name="Responsável",
        help_text="Nome da pessoa responsável pela reunião"
    )
    title = models.CharField(
        max_length=60,
        verbose_name="Tema/Título",
        help_text="Título principal da reunião"
    )
    description = models.TextField(
        max_length=300,
        verbose_name="Descrição",
        help_text="Descrição detalhada do que será abordado"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='meetings',
        verbose_name="Categoria"
    )
    
    # Data, hora e duração
    meeting_date = models.DateField(
        verbose_name="Data da Reunião"
    )
    meeting_time = models.TimeField(
        verbose_name="Horário da Reunião"
    )
    duration_minutes = models.PositiveIntegerField(
        default=60,
        verbose_name="Duração (minutos)",
        help_text="Duração estimada em minutos"
    )
    timezone = models.CharField(
        max_length=50,
        default='America/Sao_Paulo',
        verbose_name="Fuso Horário"
    )
    
    # Formato e acesso
    meeting_format = models.CharField(
        max_length=20,
        choices=MEETING_FORMATS,
        verbose_name="Formato da Reunião"
    )
    meeting_url = models.URLField(
        validators=[URLValidator()],
        verbose_name="Link da Reunião",
        help_text="URL para acessar a reunião online"
    )
    backup_url = models.URLField(
        blank=True,
        verbose_name="Link Backup",
        help_text="URL alternativa caso a principal falhe"
    )
    meeting_password = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Senha da Reunião",
        help_text="Senha para acesso (se necessária)"
    )
    access_type = models.CharField(
        max_length=20,
        choices=ACCESS_TYPE_CHOICES,
        default='public',
        verbose_name="Tipo de Acesso"
    )
    
    # Relacionamentos
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_meetings',
        verbose_name="Criador"
    )
    cooperators = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='MeetingCooperation',
        through_fields=('meeting', 'cooperator'),
        related_name='cooperated_meetings',
        blank=True,
        verbose_name="Cooperadores"
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='MeetingParticipation',
        through_fields=('meeting', 'participant'),
        related_name='participated_meetings',
        blank=True,
        verbose_name="Participantes"
    )
    
    # Configurações de participação
    max_participants = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Máximo de Participantes",
        help_text="Deixe vazio para ilimitado"
    )
    requires_approval = models.BooleanField(
        default=True,
        verbose_name="Requer Aprovação",
        help_text="Participantes precisam de aprovação para entrar"
    )
    allow_comments = models.BooleanField(
        default=True,
        verbose_name="Permitir Comentários"
    )
    allow_ratings = models.BooleanField(
        default=True,
        verbose_name="Permitir Avaliações"
    )
    is_recurring = models.BooleanField(
        default=False,
        verbose_name="Reunião Recorrente"
    )
    
    # Conteúdo adicional
    agenda = models.TextField(
        blank=True,
        verbose_name="Agenda",
        help_text="Pauta detalhada da reunião"
    )
    prerequisites = models.TextField(
        blank=True,
        verbose_name="Pré-requisitos",
        help_text="O que os participantes devem saber/ter"
    )
    materials = models.TextField(
        blank=True,
        verbose_name="Materiais",
        help_text="Links para materiais de apoio"
    )
    tags = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Tags",
        help_text="Tags separadas por vírgula"
    )
    
    # Status e controle
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Status"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_meetings',
        verbose_name="Aprovado por"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Aprovado em"
    )
    rejection_reason = models.TextField(
        blank=True,
        verbose_name="Motivo da Rejeição"
    )
    
    # Métricas
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Visualizações"
    )
    join_attempts = models.PositiveIntegerField(
        default=0,
        verbose_name="Tentativas de Participação"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Publicado em")
    
    class Meta:
        verbose_name = "Reunião"
        verbose_name_plural = "Reuniões"
        ordering = ['-meeting_date', '-meeting_time']
        indexes = [
            models.Index(fields=['meeting_date', 'meeting_time']),
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['creator', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.meeting_date} {self.meeting_time}"
    
    def clean(self):
        """Validações customizadas"""
        super().clean()
        
        # Validar data não pode ser no passado
        if self.meeting_date and self.meeting_date < timezone.now().date():
            raise ValidationError({'meeting_date': 'A data da reunião não pode ser no passado.'})
        
        # Validar URL baseada no formato
        if self.meeting_url and self.meeting_format:
            self.validate_meeting_url()
        
        # Validar duração
        if self.duration_minutes and (self.duration_minutes < 15 or self.duration_minutes > 480):
            raise ValidationError({'duration_minutes': 'Duração deve ser entre 15 minutos e 8 horas.'})
    
    def save(self, *args, **kwargs):
        """Override do save para lógicas adicionais"""
        # Definir published_at quando status muda para published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        
        # Limpar published_at se não está mais publicado
        if self.status != 'published' and self.published_at:
            self.published_at = None
        
        super().save(*args, **kwargs)
    
    @property
    def meeting_datetime(self):
        """Combina data e hora da reunião"""
        from django.utils import timezone as tz
        dt = datetime.combine(self.meeting_date, self.meeting_time)
        # Garantir que sempre retorne um datetime com timezone
        if tz.is_naive(dt):
            dt = tz.make_aware(dt)
        return dt
    
    @property
    def end_datetime(self):
        """Data/hora de término da reunião"""
        return self.meeting_datetime + timedelta(minutes=self.duration_minutes)
    
    @property
    def is_upcoming(self):
        """Verifica se a reunião é futura"""
        from django.utils import timezone as tz
        now = tz.now()
        meeting_dt = tz.make_aware(self.meeting_datetime) if tz.is_naive(self.meeting_datetime) else self.meeting_datetime
        return meeting_dt > now
    
    @property
    def is_in_progress(self):
        """Verifica se a reunião está acontecendo agora"""
        from django.utils import timezone as tz
        now = tz.now()
        meeting_dt = tz.make_aware(self.meeting_datetime) if tz.is_naive(self.meeting_datetime) else self.meeting_datetime
        end_dt = tz.make_aware(self.end_datetime) if tz.is_naive(self.end_datetime) else self.end_datetime
        return meeting_dt <= now <= end_dt
    
    @property
    def is_finished(self):
        """Verifica se a reunião já terminou"""
        from django.utils import timezone as tz
        now = tz.now()
        end_dt = tz.make_aware(self.end_datetime) if tz.is_naive(self.end_datetime) else self.end_datetime
        return end_dt < now
    
    @property
    def time_until_start(self):
        """Tempo até o início da reunião"""
        if self.is_upcoming:
            from django.utils import timezone as tz
            now = tz.now()
            meeting_dt = tz.make_aware(self.meeting_datetime) if tz.is_naive(self.meeting_datetime) else self.meeting_datetime
            return meeting_dt - now
        return timedelta(0)
    
    @property
    def duration_formatted(self):
        """Duração formatada (ex: 1h 30min)"""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        if hours and minutes:
            return f"{hours}h {minutes}min"
        elif hours:
            return f"{hours}h"
        else:
            return f"{minutes}min"
    
    def can_join(self, user):
        """Verifica se o usuário pode participar da reunião"""
        if not user or not user.is_authenticated:
            return False
        
        # Criador sempre pode entrar
        if self.creator == user:
            return True
        
        # Verificar se é cooperador aprovado
        if self.cooperators.filter(
            id=user.id,
            meetingcooperation__status='approved'
        ).exists():
            return True
        
        # Verificar se é participante aprovado
        participation = self.meetingparticipation_set.filter(
            participant=user,
            status='approved'
        ).exists()
        
        return participation
    
    def can_edit(self, user):
        """Verifica se o usuário pode editar a reunião"""
        if not user or not user.is_authenticated:
            return False
        
        # Admin pode editar tudo
        if user.is_staff:
            return True
        
        # Criador pode editar suas reuniões
        if self.creator == user:
            return True
        
        # Cooperador aprovado pode editar (com limitações)
        return self.cooperators.filter(
            id=user.id,
            meetingcooperation__status='approved'
        ).exists()
    
    def get_participant_count(self):
        """Retorna número de participantes aprovados"""
        return self.meetingparticipation_set.filter(status='approved').count()
    
    def get_pending_requests_count(self):
        """Retorna número de solicitações pendentes"""
        return self.meetingparticipation_set.filter(status='pending').count()
    
    def get_cooperator_count(self):
        """Retorna número de cooperadores aprovados"""
        return self.meetingcooperation_set.filter(status='approved').count()
    
    def get_average_rating(self):
        """Retorna média das avaliações"""
        ratings = self.ratings.aggregate(avg=models.Avg('rating'))
        return round(ratings['avg'], 1) if ratings['avg'] else 0
    
    def get_tags_list(self):
        """Retorna lista de tags"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def validate_meeting_url(self):
        """Valida URL baseada no formato escolhido"""
        url_patterns = {
            'youtube': [r'(youtube\.com|youtu\.be)'],
            'zoom': [r'zoom\.us', r'zoom\.com'],
            'teams': [r'teams\.microsoft\.com', r'teams\.live\.com'],
            'meet': [r'meet\.google\.com'],
            'jitsi': [r'meet\.jit\.si', r'jitsi\.org'],
            'discord': [r'discord\.gg', r'discord\.com'],
        }
        
        if self.meeting_format in url_patterns:
            patterns = url_patterns[self.meeting_format]
            url_valid = any(re.search(pattern, self.meeting_url) for pattern in patterns)
            
            if not url_valid:
                raise ValidationError({
                    'meeting_url': f'URL inválida para {self.get_meeting_format_display()}. '
                                  f'Esperado: {", ".join(url_patterns[self.meeting_format])}'
                })
    
    def increment_view_count(self):
        """Incrementa contador de visualizações"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def increment_join_attempts(self):
        """Incrementa contador de tentativas de participação"""
        self.join_attempts += 1
        self.save(update_fields=['join_attempts'])


class MeetingCooperation(models.Model):
    """Modelo intermediário para cooperação em reuniões"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('approved', 'Aprovado'),
        ('rejected', 'Rejeitado'),
        ('expired', 'Expirado'),
        ('revoked', 'Revogado'),
    ]
    
    PERMISSION_CHOICES = [
        ('view', 'Visualizar'),
        ('edit', 'Editar'),
        ('moderate', 'Moderar'),
        ('manage_participants', 'Gerenciar Participantes'),
    ]
    
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        verbose_name="Reunião"
    )
    cooperator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Cooperador"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Status"
    )
    permissions = models.JSONField(
        default=list,
        help_text="Lista de permissões do cooperador",
        verbose_name="Permissões"
    )
    message = models.TextField(
        blank=True,
        verbose_name="Mensagem",
        help_text="Mensagem enviada na solicitação"
    )
    response_message = models.TextField(
        blank=True,
        verbose_name="Resposta",
        help_text="Resposta do criador da reunião"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Expira em"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_cooperations',
        verbose_name="Aprovado por"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Cooperação em Reunião"
        verbose_name_plural = "Cooperações em Reuniões"
        unique_together = ['meeting', 'cooperator']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.cooperator.get_full_name()} - {self.meeting.title} ({self.status})"
    
    def clean(self):
        """Validações customizadas"""
        super().clean()
        
        # Verificar limite de cooperações do usuário
        if self.cooperator and self.status == 'approved':
            max_cooperations = self.cooperator.max_cooperations
            current_cooperations = MeetingCooperation.objects.filter(
                cooperator=self.cooperator,
                status='approved'
            ).exclude(id=self.id).count()
            
            if current_cooperations >= max_cooperations:
                raise ValidationError(
                    f'Usuário já atingiu o limite de {max_cooperations} cooperações simultâneas.'
                )
        
        # Verificar limite de cooperadores na reunião (máximo 4)
        if self.meeting and self.status == 'approved':
            current_cooperators = MeetingCooperation.objects.filter(
                meeting=self.meeting,
                status='approved'
            ).exclude(id=self.id).count()
            
            if current_cooperators >= 4:
                raise ValidationError(
                    'Reunião já atingiu o limite máximo de 4 cooperadores.'
                )


class MeetingParticipation(models.Model):
    """Modelo intermediário para participação em reuniões"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('approved', 'Aprovado'),
        ('rejected', 'Rejeitado'),
        ('cancelled', 'Cancelado'),
        ('attended', 'Compareceu'),
        ('no_show', 'Não Compareceu'),
    ]
    
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        verbose_name="Reunião"
    )
    participant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Participante"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Status"
    )
    message = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="Mensagem",
        help_text="Mensagem enviada na solicitação"
    )
    response_message = models.TextField(
        blank=True,
        verbose_name="Resposta",
        help_text="Resposta sobre a aprovação/rejeição"
    )
    attended = models.BooleanField(
        default=False,
        verbose_name="Compareceu"
    )
    joined_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Entrou em"
    )
    left_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Saiu em"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_participations',
        verbose_name="Aprovado por"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Solicitado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Participação em Reunião"
        verbose_name_plural = "Participações em Reuniões"
        unique_together = ['meeting', 'participant']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.participant.get_full_name()} - {self.meeting.title} ({self.status})"
    
    def clean(self):
        """Validações customizadas"""
        super().clean()
        
        # Verificar limite de participantes na reunião
        if self.meeting and self.meeting.max_participants and self.status == 'approved':
            current_participants = MeetingParticipation.objects.filter(
                meeting=self.meeting,
                status='approved'
            ).exclude(id=self.id).count()
            
            if current_participants >= self.meeting.max_participants:
                raise ValidationError(
                    f'Reunião já atingiu o limite máximo de {self.meeting.max_participants} participantes.'
                )
    
    @property
    def duration_attended(self):
        """Duração que o participante ficou na reunião"""
        if self.joined_at and self.left_at:
            return self.left_at - self.joined_at
        return None


class Comment(models.Model):
    """Modelo para comentários em reuniões"""
    
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Reunião"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Autor"
    )
    content = models.TextField(
        max_length=1000,
        verbose_name="Conteúdo"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name="Comentário Pai"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )
    is_pinned = models.BooleanField(
        default=False,
        verbose_name="Fixado"
    )
    likes_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Curtidas"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Comentário"
        verbose_name_plural = "Comentários"
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['meeting', '-created_at']),
            models.Index(fields=['author', '-created_at']),
        ]
    
    def __str__(self):
        content_preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f"{self.author.get_full_name()}: {content_preview}"
    
    def can_edit(self, user):
        """Verifica se o usuário pode editar o comentário"""
        return user == self.author or user.is_staff or self.meeting.can_edit(user)
    
    def get_replies_count(self):
        """Retorna número de respostas"""
        return self.replies.filter(is_active=True).count()


class Rating(models.Model):
    """Modelo para avaliações de reuniões"""
    
    RATING_CHOICES = [(i, f"{i} estrela{'s' if i > 1 else ''}") for i in range(1, 6)]
    
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name='ratings',
        verbose_name="Reunião"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Usuário"
    )
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        verbose_name="Avaliação"
    )
    review = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="Comentário"
    )
    aspects = models.JSONField(
        default=dict,
        help_text="Avaliações por aspecto (conteúdo, organização, etc.)",
        verbose_name="Aspectos"
    )
    is_anonymous = models.BooleanField(
        default=False,
        verbose_name="Avaliação Anônima"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Avaliação"
        verbose_name_plural = "Avaliações"
        unique_together = ['meeting', 'user']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['meeting', '-rating']),
        ]
    
    def __str__(self):
        user_display = "Anônimo" if self.is_anonymous else self.user.get_full_name()
        return f"{user_display} - {self.meeting.title} ({self.rating}★)"
    
    def clean(self):
        """Validações customizadas"""
        super().clean()
        
        # Só pode avaliar se participou da reunião
        if not MeetingParticipation.objects.filter(
            meeting=self.meeting,
            participant=self.user,
            status__in=['approved', 'attended']
        ).exists() and self.user != self.meeting.creator:
            raise ValidationError('Apenas participantes da reunião podem avaliá-la.')
        
        # Só pode avaliar após a reunião
        if self.meeting.is_upcoming:
            raise ValidationError('Não é possível avaliar reuniões que ainda não aconteceram.')


# Modelo para notificações (básico)
class Notification(models.Model):
    """Modelo para notificações do sistema"""
    
    TYPE_CHOICES = [
        ('meeting_approval', 'Reunião Aprovada'),
        ('meeting_rejection', 'Reunião Rejeitada'),
        ('participation_approved', 'Participação Aprovada'),
        ('participation_rejected', 'Participação Rejeitada'),
        ('cooperation_request', 'Solicitação de Cooperação'),
        ('cooperation_approved', 'Cooperação Aprovada'),
        ('meeting_reminder', 'Lembrete de Reunião'),
        ('new_comment', 'Novo Comentário'),
        ('meeting_cancelled', 'Reunião Cancelada'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Usuário"
    )
    type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        verbose_name="Tipo"
    )
    title = models.CharField(
        max_length=100,
        verbose_name="Título"
    )
    message = models.TextField(
        verbose_name="Mensagem"
    )
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Reunião"
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name="Lida"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    
    class Meta:
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"