# meetings/signals.py - SINAIS PARA EVENTOS IMPORTANTES

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Meeting, MeetingParticipation, Rating, Comment, MeetingCooperation
from .utils import MeetingUtils
import logging

logger = logging.getLogger('meetings.signals')


@receiver(pre_save, sender=Meeting)
def meeting_pre_save(sender, instance, **kwargs):
    """Validações e ações antes de salvar reunião"""
    
    # Se é uma atualização
    if instance.pk:
        try:
            old_instance = Meeting.objects.get(pk=instance.pk)
            
            # Log de mudanças importantes
            if old_instance.status != instance.status:
                logger.info(
                    f"Status da reunião {instance.id} mudou de "
                    f"{old_instance.status} para {instance.status}"
                )
            
            # Impedir mudança de data/hora se reunião já começou
            if old_instance.is_in_progress or old_instance.is_finished:
                if (instance.meeting_date != old_instance.meeting_date or 
                    instance.meeting_time != old_instance.meeting_time):
                    raise ValidationError(
                        "Não é possível alterar data/hora de reunião em andamento ou finalizada."
                    )
            
            # Notificar participantes sobre mudanças importantes
            significant_changes = []
            
            if old_instance.meeting_date != instance.meeting_date:
                significant_changes.append('data')
            if old_instance.meeting_time != instance.meeting_time:
                significant_changes.append('horário')
            if old_instance.meeting_url != instance.meeting_url:
                significant_changes.append('link')
            
            # Se houver mudanças significativas, notificar participantes
            if significant_changes and instance.status == 'published':
                # Esta lógica será executada no post_save
                instance._notify_changes = significant_changes
                
        except Meeting.DoesNotExist:
            pass
    
    # Validações para reuniões novas ou atualizadas
    if instance.meeting_date and instance.meeting_time:
        is_valid, message = MeetingUtils.is_valid_meeting_time(
            instance.meeting_date, 
            instance.meeting_time
        )
        
        if not is_valid:
            raise ValidationError(f"Data/hora inválida: {message}")


@receiver(post_save, sender=Meeting)
def meeting_post_save(sender, instance, created, **kwargs):
    """Ações após salvar reunião"""
    
    if created:
        logger.info(f"Nova reunião criada: {instance.title} por {instance.creator}")
        
        # Criar notificação para o criador
        from .models import Notification
        try:
            Notification.objects.create(
                user=instance.creator,
                type='meeting_created',
                title='Reunião Criada',
                message=f'Sua reunião "{instance.title}" foi criada com sucesso.',
                meeting=instance
            )
        except Exception as e:
            logger.error(f"Erro ao criar notificação: {e}")
        
        # Se for publicada imediatamente, enviar notificação
        if instance.status == 'published':
            # Aqui você pode adicionar lógica para notificar seguidores
            logger.info(f"Reunião {instance.title} publicada imediatamente")
    
    else:
        logger.info(f"Reunião atualizada: {instance.title}")
        
        # Verificar se há mudanças a serem notificadas
        if hasattr(instance, '_notify_changes'):
            changes = instance._notify_changes
            logger.info(f"Notificando mudanças na reunião {instance.id}: {changes}")
            
            # Buscar participantes aprovados
            participants = []
            for participation in instance.meetingparticipation_set.filter(status='approved'):
                participants.append(participation.participant)
            
            if participants:
                # Enviar notificação sobre mudanças
                MeetingUtils.send_meeting_notification(
                    instance, 'updated', participants
                )
            
            # Remover a flag
            delattr(instance, '_notify_changes')
    
    # Atualizar published_at quando status muda para published
    if instance.status == 'published' and not instance.published_at:
        Meeting.objects.filter(pk=instance.pk).update(
            published_at=timezone.now()
        )


@receiver(post_save, sender=MeetingParticipation)
def participation_post_save(sender, instance, created, **kwargs):
    """Ações após criar/atualizar participação"""
    
    if created:
        logger.info(
            f"Nova participação: {instance.participant} -> {instance.meeting}"
        )
        
        # Se foi aprovada automaticamente, enviar notificação
        if instance.status == 'approved':
            MeetingUtils.send_meeting_notification(
                instance.meeting, 'participation_approved', [instance.participant]
            )
        
        # Notificar criador da reunião sobre nova solicitação
        elif instance.status == 'pending':
            from .models import Notification
            try:
                Notification.objects.create(
                    user=instance.meeting.creator,
                    type='participation_request',
                    title='Nova Solicitação de Participação',
                    message=f'{instance.participant.get_full_name()} quer participar de "{instance.meeting.title}"',
                    meeting=instance.meeting
                )
            except Exception as e:
                logger.error(f"Erro ao criar notificação: {e}")
    
    else:
        logger.info(
            f"Participação atualizada: {instance.participant} -> {instance.meeting} "
            f"Status: {instance.status}"
        )
        
        # Se status mudou para approved, notificar participante
        if instance.status == 'approved':
            MeetingUtils.send_meeting_notification(
                instance.meeting, 'participation_approved', [instance.participant]
            )
        
        # Se foi rejeitada, notificar também
        elif instance.status == 'rejected':
            MeetingUtils.send_meeting_notification(
                instance.meeting, 'participation_rejected', [instance.participant]
            )


@receiver(post_save, sender=MeetingCooperation)
def cooperation_post_save(sender, instance, created, **kwargs):
    """Ações após criar/atualizar cooperação"""
    
    if created:
        logger.info(
            f"Nova solicitação de cooperação: {instance.cooperator} -> {instance.meeting}"
        )
        
        # Notificar criador da reunião
        from .models import Notification
        try:
            Notification.objects.create(
                user=instance.meeting.creator,
                type='cooperation_request',
                title='Solicitação de Cooperação',
                message=f'{instance.cooperator.get_full_name()} quer cooperar em "{instance.meeting.title}"',
                meeting=instance.meeting
            )
        except Exception as e:
            logger.error(f"Erro ao criar notificação: {e}")
    
    else:
        logger.info(
            f"Cooperação atualizada: {instance.cooperator} -> {instance.meeting} "
            f"Status: {instance.status}"
        )
        
        # Notificar cooperador sobre mudança de status
        if instance.status == 'approved':
            try:
                Notification.objects.create(
                    user=instance.cooperator,
                    type='cooperation_approved',
                    title='Cooperação Aprovada',
                    message=f'Sua solicitação para cooperar em "{instance.meeting.title}" foi aprovada!',
                    meeting=instance.meeting
                )
            except Exception as e:
                logger.error(f"Erro ao criar notificação: {e}")


@receiver(post_save, sender=Rating)
def rating_post_save(sender, instance, created, **kwargs):
    """Ações após criar/atualizar avaliação"""
    
    if created:
        logger.info(
            f"Nova avaliação: {instance.user} avaliou {instance.meeting} "
            f"com {instance.rating} estrelas"
        )
        
        # Notificar criador da reunião sobre nova avaliação
        if instance.user != instance.meeting.creator:
            from .models import Notification
            try:
                user_name = "Usuário anônimo" if instance.is_anonymous else instance.user.get_full_name()
                Notification.objects.create(
                    user=instance.meeting.creator,
                    type='new_rating',
                    title='Nova Avaliação',
                    message=f'{user_name} avaliou sua reunião "{instance.meeting.title}" com {instance.rating} estrelas',
                    meeting=instance.meeting
                )
            except Exception as e:
                logger.error(f"Erro ao criar notificação: {e}")


@receiver(post_save, sender=Comment)
def comment_post_save(sender, instance, created, **kwargs):
    """Ações após criar/atualizar comentário"""
    
    if created:
        logger.info(
            f"Novo comentário: {instance.author} comentou em {instance.meeting}"
        )
        
        # Notificar criador da reunião sobre novo comentário
        if instance.author != instance.meeting.creator:
            from .models import Notification
            try:
                Notification.objects.create(
                    user=instance.meeting.creator,
                    type='new_comment',
                    title='Novo Comentário',
                    message=f'{instance.author.get_full_name()} comentou em "{instance.meeting.title}"',
                    meeting=instance.meeting
                )
            except Exception as e:
                logger.error(f"Erro ao criar notificação: {e}")
        
        # Se é uma resposta, notificar autor do comentário pai
        if instance.parent and instance.author != instance.parent.author:
            try:
                Notification.objects.create(
                    user=instance.parent.author,
                    type='comment_reply',
                    title='Resposta ao Comentário',
                    message=f'{instance.author.get_full_name()} respondeu seu comentário em "{instance.meeting.title}"',
                    meeting=instance.meeting
                )
            except Exception as e:
                logger.error(f"Erro ao criar notificação: {e}")


@receiver(post_delete, sender=Meeting)
def meeting_post_delete(sender, instance, **kwargs):
    """Ações após deletar reunião"""
    
    logger.info(f"Reunião deletada: {instance.title} por {instance.creator}")
    
    # Aqui você pode adicionar lógica para:
    # - Limpar arquivos relacionados
    # - Notificar participantes sobre cancelamento
    # - Fazer backup dos dados


@receiver(post_delete, sender=MeetingParticipation)
def participation_post_delete(sender, instance, **kwargs):
    """Ações após deletar participação"""
    
    logger.info(
        f"Participação removida: {instance.participant} saiu de {instance.meeting}"
    )


# Signal para atualizar status de reuniões automaticamente
from django.db.models.signals import post_migrate

@receiver(post_migrate)
def create_periodic_tasks(sender, **kwargs):
    """Criar tarefas periódicas após migração"""
    
    if sender.name == 'meetings':
        logger.info("Configurando tarefas periódicas para reuniões")
        
        # Aqui você pode configurar tarefas do Celery ou outros jobs
        # Por exemplo: agendar verificação de reuniões que precisam mudar status