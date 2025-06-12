from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import FileExtensionValidator

class User(AbstractUser):
    """
    Modelo de usuário customizado para o sistema Tertúlia Literária
    """
    USER_TYPES = [
        ('participante', 'Participante'),
        ('cooperador', 'Cooperador'),
        ('criador', 'Criador de Reunião'),
    ]
    
    email = models.EmailField(unique=True, verbose_name="Email")
    user_type = models.CharField(
        max_length=20, 
        choices=USER_TYPES, 
        default='participante',
        verbose_name="Tipo de Usuário"
    )
    profile_image = models.ImageField(
        upload_to='profiles/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        help_text="Imagem de perfil (JPG, JPEG, PNG)",
        verbose_name="Foto de Perfil"
    )
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name="Telefone"
    )
    bio = models.TextField(
        max_length=500, 
        blank=True, 
        null=True,
        verbose_name="Biografia"
    )
    is_email_verified = models.BooleanField(
        default=False,
        verbose_name="Email Verificado"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    # Para cooperadores
    max_cooperations = models.PositiveIntegerField(
        default=5,
        verbose_name="Máximo de Cooperações"
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Retorna nome completo do usuário"""
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def can_create_meetings(self):
        """Verifica se o usuário pode criar reuniões"""
        return self.user_type in ['criador', 'cooperador']
    
    def is_meeting_creator(self):
        """Verifica se é criador de reuniões"""
        return self.user_type == 'criador'
    
    def is_cooperator(self):
        """Verifica se é cooperador"""
        return self.user_type == 'cooperador'


class CooperatorRequest(models.Model):
    """
    Modelo para solicitações de cooperação
    """
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('approved', 'Aprovado'),
        ('rejected', 'Rejeitado'),
    ]
    
    cooperator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='cooperator_requests',
        verbose_name="Cooperador"
    )
    meeting_creator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_cooperator_requests',
        verbose_name="Criador da Reunião"
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name="Status"
    )
    message = models.TextField(
        max_length=500, 
        blank=True,
        verbose_name="Mensagem"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        verbose_name = "Solicitação de Cooperação"
        verbose_name_plural = "Solicitações de Cooperação"
        unique_together = ['cooperator', 'meeting_creator']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.cooperator.get_full_name()} -> {self.meeting_creator.get_full_name()}"