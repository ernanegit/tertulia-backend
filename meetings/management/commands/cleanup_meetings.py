# meetings/management/commands/cleanup_meetings.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from meetings.models import Meeting, MeetingParticipation, Notification
from meetings.utils import MeetingUtils

class Command(BaseCommand):
    help = 'Limpar reuniões antigas e realizar manutenção do sistema'
    
# meetings/management/commands/cleanup_meetings.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from meetings.models import Meeting, MeetingParticipation, Notification
from meetings.utils import MeetingUtils

class Command(BaseCommand):
    help = 'Limpar reuniões antigas e realizar manutenção do sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executar sem fazer alterações (apenas mostrar o que seria feito)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Número de dias para considerar reuniões antigas (padrão: 30)',
        )
        parser.add_argument(
            '--delete-notifications',
            action='store_true',
            help='Deletar notificações antigas (mais de 90 dias)',
        )
    
    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        days_old = options['days']
        delete_notifications = options['delete_notifications']
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('MODO DRY-RUN: Nenhuma alteração será feita')
            )
        
        self.stdout.write('Iniciando limpeza do sistema...\n')
        
        # 1. Finalizar reuniões que já terminaram
        self.finalize_old_meetings()
        
        # 2. Cancelar rascunhos muito antigos
        self.cancel_old_drafts(days_old)
        
        # 3. Limpar participações rejeitadas antigas
        self.cleanup_old_participations(days_old)
        
        # 4. Deletar notificações antigas (se solicitado)
        if delete_notifications:
            self.cleanup_old_notifications()
        
        # 5. Estatísticas gerais
        self.show_statistics()
        
        self.stdout.write(
            self.style.SUCCESS('\nLimpeza concluída!')
        )
    
    def finalize_old_meetings(self):
        """Finalizar reuniões que já terminaram"""
        self.stdout.write('1. Finalizando reuniões antigas...')
        
        now = timezone.now()
        yesterday = now.date() - timedelta(days=1)
        
        # Buscar reuniões que deveriam estar finalizadas
        meetings_to_finalize = Meeting.objects.filter(
            status__in=['published', 'in_progress'],
            meeting_date__lt=yesterday
        )
        
        count = meetings_to_finalize.count()
        
        if count > 0:
            if not self.dry_run:
                meetings_to_finalize.update(status='finished')
            
            self.stdout.write(
                f'   - {count} reuniões marcadas como finalizadas'
            )
        else:
            self.stdout.write('   - Nenhuma reunião para finalizar')
    
    def cancel_old_drafts(self, days_old):
        """Cancelar rascunhos muito antigos"""
        self.stdout.write('2. Cancelando rascunhos antigos...')
        
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        old_drafts = Meeting.objects.filter(
            status='draft',
            created_at__lt=cutoff_date
        )
        
        count = old_drafts.count()
        
        if count > 0:
            if not self.dry_run:
                old_drafts.update(
                    status='cancelled',
                    rejection_reason=f'Cancelado automaticamente após {days_old} dias'
                )
            
            self.stdout.write(
                f'   - {count} rascunhos cancelados (mais de {days_old} dias)'
            )
        else:
            self.stdout.write(f'   - Nenhum rascunho antigo para cancelar')
    
    def cleanup_old_participations(self, days_old):
        """Limpar participações rejeitadas antigas"""
        self.stdout.write('3. Limpando participações antigas...')
        
        cutoff_date = timezone.now() - timedelta(days=days_old)
        
        # Participações rejeitadas antigas
        old_rejected = MeetingParticipation.objects.filter(
            status='rejected',
            updated_at__lt=cutoff_date
        )
        
        rejected_count = old_rejected.count()
        
        if rejected_count > 0:
            if not self.dry_run:
                old_rejected.delete()
            
            self.stdout.write(
                f'   - {rejected_count} participações rejeitadas removidas'
            )
        
        # Participações pendentes muito antigas (mais de 60 dias)
        very_old_pending = MeetingParticipation.objects.filter(
            status='pending',
            created_at__lt=timezone.now() - timedelta(days=60)
        )
        
        pending_count = very_old_pending.count()
        
        if pending_count > 0:
            if not self.dry_run:
                very_old_pending.update(
                    status='cancelled',
                    response_message='Cancelado automaticamente por inatividade'
                )
            
            self.stdout.write(
                f'   - {pending_count} participações pendentes canceladas'
            )
        
        if rejected_count == 0 and pending_count == 0:
            self.stdout.write('   - Nenhuma participação antiga para limpar')
    
    def cleanup_old_notifications(self):
        """Deletar notificações antigas"""
        self.stdout.write('4. Limpando notificações antigas...')
        
        # Notificações lidas com mais de 90 dias
        cutoff_date = timezone.now() - timedelta(days=90)
        
        old_notifications = Notification.objects.filter(
            is_read=True,
            created_at__lt=cutoff_date
        )
        
        count = old_notifications.count()
        
        if count > 0:
            if not self.dry_run:
                old_notifications.delete()
            
            self.stdout.write(
                f'   - {count} notificações antigas removidas'
            )
        else:
            self.stdout.write('   - Nenhuma notificação antiga para remover')
    
    def show_statistics(self):
        """Mostrar estatísticas do sistema"""
        self.stdout.write('5. Estatísticas do sistema:')
        
        # Reuniões por status
        statuses = Meeting.objects.values('status').annotate(
            count=models.Count('id')
        ).order_by('-count')
        
        self.stdout.write('   Reuniões por status:')
        for status_info in statuses:
            status_display = dict(Meeting.STATUS_CHOICES).get(
                status_info['status'], 
                status_info['status']
            )
            self.stdout.write(
                f'     - {status_display}: {status_info["count"]}'
            )
        
        # Reuniões por período
        now = timezone.now()
        
        # Últimos 30 dias
        last_month = Meeting.objects.filter(
            created_at__gte=now - timedelta(days=30)
        ).count()
        
        # Próximos 30 dias
        next_month = Meeting.objects.filter(
            status='published',
            meeting_date__gte=now.date(),
            meeting_date__lte=now.date() + timedelta(days=30)
        ).count()
        
        self.stdout.write(f'   Reuniões criadas nos últimos 30 dias: {last_month}')
        self.stdout.write(f'   Reuniões agendadas para os próximos 30 dias: {next_month}')
        
        # Participações
        total_participations = MeetingParticipation.objects.filter(
            status='approved'
        ).count()
        
        pending_participations = MeetingParticipation.objects.filter(
            status='pending'
        ).count()
        
        self.stdout.write(f'   Total de participações aprovadas: {total_participations}')
        self.stdout.write(f'   Participações pendentes: {pending_participations}')
        
        # Notificações não lidas
        unread_notifications = Notification.objects.filter(
            is_read=False
        ).count()
        
        self.stdout.write(f'   Notificações não lidas: {unread_notifications}')


# meetings/management/commands/send_meeting_reminders.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from meetings.models import Meeting, MeetingParticipation
from meetings.utils import MeetingUtils

class Command(BaseCommand):
    help = 'Enviar lembretes de reuniões agendadas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=2,
            help='Horas antes da reunião para enviar lembrete (padrão: 2)',
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Modo teste - não enviar emails reais',
        )
    
    def handle(self, *args, **options):
        hours_before = options['hours']
        test_mode = options['test']
        
        if test_mode:
            self.stdout.write(
                self.style.WARNING('MODO TESTE: Emails não serão enviados')
            )
        
        self.stdout.write(
            f'Enviando lembretes para reuniões em {hours_before} horas...'
        )
        
        # Calcular horário alvo
        now = timezone.now()
        target_start = now + timedelta(hours=hours_before - 0.5)  # 30 min antes
        target_end = now + timedelta(hours=hours_before + 0.5)    # 30 min depois
        
        # Buscar reuniões no período alvo
        meetings = Meeting.objects.filter(
            status='published',
            meeting_date=target_start.date()
        )
        
        # Filtrar por horário
        target_meetings = []
        for meeting in meetings:
            meeting_datetime = datetime.combine(
                meeting.meeting_date, 
                meeting.meeting_time
            )
            meeting_datetime = timezone.make_aware(meeting_datetime)
            
            if target_start <= meeting_datetime <= target_end:
                target_meetings.append(meeting)
        
        if not target_meetings:
            self.stdout.write('Nenhuma reunião encontrada para o período especificado')
            return
        
        total_emails = 0
        
        for meeting in target_meetings:
            self.stdout.write(f'\nProcessando: {meeting.title}')
            
            # Buscar participantes aprovados
            participants = []
            participations = MeetingParticipation.objects.filter(
                meeting=meeting,
                status='approved'
            ).select_related('participant')
            
            for participation in participations:
                participants.append(participation.participant)
            
            # Adicionar criador se não estiver na lista
            if meeting.creator not in participants:
                participants.append(meeting.creator)
            
            if participants:
                self.stdout.write(f'  Enviando para {len(participants)} participantes')
                
                if not test_mode:
                    success = MeetingUtils.send_meeting_notification(
                        meeting, 'reminder', participants
                    )
                    
                    if success:
                        total_emails += len(participants)
                        self.stdout.write('  ✓ Emails enviados')
                    else:
                        self.stdout.write('  ✗ Erro ao enviar emails')
                else:
                    total_emails += len(participants)
                    self.stdout.write('  ✓ Simulado')
            else:
                self.stdout.write('  Nenhum participante encontrado')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nConcluído! {total_emails} lembretes enviados para {len(target_meetings)} reuniões'
            )
        )


# meetings/management/commands/update_meeting_status.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from meetings.models import Meeting
from django.db.models import Q

class Command(BaseCommand):
    help = 'Atualizar status das reuniões baseado na data/hora atual'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar mudanças sem aplicá-las',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO DRY-RUN: Mudanças não serão aplicadas')
            )
        
        now = timezone.now()
        today = now.date()
        current_time = now.time()
        
        # 1. Marcar reuniões como "em andamento"
        starting_meetings = Meeting.objects.filter(
            status='published',
            meeting_date=today,
            meeting_time__lte=current_time
        )
        
        # Filtrar apenas as que realmente estão em andamento
        in_progress_meetings = []
        for meeting in starting_meetings:
            if meeting.is_in_progress:
                in_progress_meetings.append(meeting)
        
        if in_progress_meetings:
            if not dry_run:
                Meeting.objects.filter(
                    id__in=[m.id for m in in_progress_meetings]
                ).update(status='in_progress')
            
            self.stdout.write(
                f'✓ {len(in_progress_meetings)} reuniões marcadas como "em andamento"'
            )
        
        # 2. Marcar reuniões como "finalizadas"
        finished_meetings = Meeting.objects.filter(
            status__in=['published', 'in_progress'],
            meeting_date__lt=today
        )
        
        # Incluir reuniões de hoje que já terminaram
        today_finished = []
        for meeting in Meeting.objects.filter(
            status__in=['published', 'in_progress'],
            meeting_date=today
        ):
            if meeting.is_finished:
                today_finished.append(meeting)
        
        total_finished = finished_meetings.count() + len(today_finished)
        
        if total_finished > 0:
            if not dry_run:
                # Reuniões de dias anteriores
                finished_meetings.update(status='finished')
                
                # Reuniões de hoje que terminaram
                if today_finished:
                    Meeting.objects.filter(
                        id__in=[m.id for m in today_finished]
                    ).update(status='finished')
            
            self.stdout.write(
                f'✓ {total_finished} reuniões marcadas como "finalizadas"'
            )
        
        # 3. Expirar reuniões pendentes muito antigas
        expired_pending = Meeting.objects.filter(
            status='pending_approval',
            created_at__lt=now - timedelta(days=7)  # 7 dias
        )
        
        expired_count = expired_pending.count()
        
        if expired_count > 0:
            if not dry_run:
                expired_pending.update(
                    status='cancelled',
                    rejection_reason='Expirado - sem aprovação em 7 dias'
                )
            
            self.stdout.write(
                f'✓ {expired_count} reuniões pendentes expiradas'
            )
        
        # 4. Mostrar estatísticas
        self.show_current_stats()
        
        self.stdout.write(
            self.style.SUCCESS('\nAtualização de status concluída!')
        )
    
    def show_current_stats(self):
        """Mostrar estatísticas atuais"""
        self.stdout.write('\n📊 Status atual das reuniões:')
        
        from django.db.models import Count
        
        stats = Meeting.objects.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for stat in stats:
            status_display = dict(Meeting.STATUS_CHOICES).get(
                stat['status'], 
                stat['status']
            )
            self.stdout.write(f'   {status_display}: {stat["count"]}')
        
        # Reuniões hoje
        today = timezone.now().date()
        today_meetings = Meeting.objects.filter(
            status__in=['published', 'in_progress'],
            meeting_date=today
        ).count()
        
        self.stdout.write(f'\n📅 Reuniões hoje: {today_meetings}')


# meetings/management/__init__.py
# (arquivo vazio)

# meetings/management/commands/__init__.py  
# (arquivo vazio)