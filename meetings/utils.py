# meetings/utils.py - VERSÃO CORRIGIDA

# SE o arquivo utils.py contém URLs em vez de utilidades, SUBSTITUA TODO O CONTEÚDO por:

from django.core.mail import send_mail, send_mass_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
import logging
import re
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger('meetings.utils')


class MeetingUtils:
    """Classe com utilidades para o sistema de reuniões"""
    
    @staticmethod
    def is_valid_meeting_time(meeting_date, meeting_time) -> Tuple[bool, str]:
        """
        Valida se a data/hora da reunião é válida
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            # Combinar data e hora
            meeting_datetime = datetime.combine(meeting_date, meeting_time)
            meeting_datetime = timezone.make_aware(meeting_datetime)
            
            now = timezone.now()
            
            # Verificar se não é no passado
            if meeting_datetime <= now:
                return False, "A reunião não pode ser agendada no passado"
            
            # Verificar se não é muito no futuro (1 ano)
            max_future = now + timedelta(days=365)
            if meeting_datetime > max_future:
                return False, "A reunião não pode ser agendada com mais de 1 ano de antecedência"
            
            # Verificar horário comercial ampliado (06:00 às 23:59)
            if meeting_time.hour < 6 or meeting_time.hour >= 24:
                return False, "Horário deve ser entre 06:00 e 23:59"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Erro ao validar horário da reunião: {e}")
            return False, "Erro interno ao validar horário"
    
    @staticmethod
    def send_meeting_notification(meeting, notification_type: str, recipients: List, **kwargs) -> bool:
        """
        Enviar notificações por email sobre reuniões
        
        Args:
            meeting: Instância do modelo Meeting
            notification_type: Tipo da notificação
            recipients: Lista de usuários para enviar
            **kwargs: Parâmetros adicionais
            
        Returns:
            bool: True se enviou com sucesso
        """
        try:
            if not recipients:
                return True
            
            # Templates de email por tipo
            email_templates = {
                'meeting_created': {
                    'subject': 'Nova reunião criada',
                    'message': 'Uma nova reunião foi criada: {title}'
                },
                'participation_approved': {
                    'subject': 'Participação aprovada',
                    'message': 'Sua participação na reunião "{title}" foi aprovada!'
                },
                'cooperation_approved': {
                    'subject': 'Cooperação aprovada',
                    'message': 'Sua solicitação de cooperação em "{title}" foi aprovada!'
                },
                'meeting_reminder': {
                    'subject': 'Lembrete: reunião em breve',
                    'message': 'A reunião "{title}" começará em breve!'
                }
            }
            
            if notification_type not in email_templates:
                logger.error(f"Tipo de notificação desconhecido: {notification_type}")
                return False
            
            template_info = email_templates[notification_type]
            
            # Preparar emails para envio em massa
            messages = []
            
            for recipient in recipients:
                if hasattr(recipient, 'email') and recipient.email:
                    try:
                        message = template_info['message'].format(
                            title=meeting.title,
                            user_name=recipient.get_full_name()
                        )
                        
                        messages.append((
                            f"[Tertúlia] {template_info['subject']}",
                            message,
                            settings.DEFAULT_FROM_EMAIL,
                            [recipient.email]
                        ))
                        
                    except Exception as e:
                        logger.error(f"Erro ao preparar email para {recipient.email}: {e}")
            
            # Enviar emails em massa
            if messages:
                try:
                    send_mass_mail(messages, fail_silently=True)
                    logger.info(f"Enviados {len(messages)} emails do tipo {notification_type}")
                except Exception as e:
                    logger.error(f"Erro ao enviar emails: {e}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar notificações: {e}")
            return False
    
    @staticmethod
    def get_user_meeting_role(user, meeting) -> str:
        """
        Determinar o papel do usuário na reunião
        
        Args:
            user: Usuário
            meeting: Reunião
            
        Returns:
            str: 'creator', 'cooperator', 'participant', 'guest'
        """
        try:
            if meeting.creator == user:
                return 'creator'
            
            # Verificar se é cooperador aprovado
            from .models import MeetingCooperation  # Import local para evitar circular
            if MeetingCooperation.objects.filter(
                meeting=meeting,
                cooperator=user,  # ← CORRIGIDO: era 'user'
                status='approved'
            ).exists():
                return 'cooperator'
            
            # Verificar se é participante aprovado
            from .models import MeetingParticipation
            if MeetingParticipation.objects.filter(
                meeting=meeting,
                participant=user,
                status='approved'
            ).exists():
                return 'participant'
            
            return 'guest'
            
        except Exception as e:
            logger.error(f"Erro ao determinar papel do usuário: {e}")
            return 'guest'
    
    @staticmethod
    def can_user_perform_action(user, meeting, action: str) -> Tuple[bool, str]:
        """
        Verificar se usuário pode realizar uma ação na reunião
        
        Args:
            user: Usuário
            meeting: Reunião
            action: Ação ('view', 'edit', 'moderate', 'manage_participants', 'delete')
            
        Returns:
            Tuple[bool, str]: (can_perform, reason)
        """
        try:
            if not user or not user.is_authenticated:
                return False, "Usuário não autenticado"
            
            # Admin pode tudo
            if user.is_staff:
                return True, "Administrador"
            
            user_role = MeetingUtils.get_user_meeting_role(user, meeting)
            
            # Criador pode tudo
            if user_role == 'creator':
                return True, "Criador da reunião"
            
            # Verificar permissões do cooperador
            if user_role == 'cooperator':
                from .models import MeetingCooperation
                try:
                    cooperation = MeetingCooperation.objects.get(
                        meeting=meeting,
                        cooperator=user,  # ← CORRIGIDO
                        status='approved'
                    )
                    
                    # Verificar se tem a permissão específica
                    if action in cooperation.permissions:
                        return True, f"Cooperador com permissão '{action}'"
                    else:
                        return False, f"Cooperador sem permissão '{action}'"
                        
                except MeetingCooperation.DoesNotExist:
                    return False, "Cooperação não encontrada"
            
            # Ações permitidas para participantes
            if user_role == 'participant':
                allowed_actions = ['view']
                if action in allowed_actions:
                    return True, f"Participante pode '{action}'"
                else:
                    return False, f"Participante não pode '{action}'"
            
            # Ações para guests
            if action == 'view' and meeting.status == 'published':
                return True, "Reunião pública"
            
            return False, f"Sem permissão para '{action}'"
            
        except Exception as e:
            logger.error(f"Erro ao verificar permissões: {e}")
            return False, "Erro interno"


# Funções auxiliares
def format_duration(minutes: int) -> str:
    """Formatar duração em minutos para string legível"""
    if minutes < 60:
        return f"{minutes}min"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes == 0:
        return f"{hours}h"
    else:
        return f"{hours}h {remaining_minutes}min"