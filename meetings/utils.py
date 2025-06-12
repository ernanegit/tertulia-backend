# meetings/utils.py - UTILITÁRIOS PARA REUNIÕES

from datetime import datetime, timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count, Avg
import logging

logger = logging.getLogger('meetings.utils')


class MeetingUtils:
    """Utilitários para reuniões"""
    
    @staticmethod
    def is_valid_meeting_time(meeting_date, meeting_time):
        """Verifica se data/hora da reunião é válida"""
        try:
            meeting_datetime = datetime.combine(meeting_date, meeting_time)
            now = timezone.now().replace(tzinfo=None)
            
            # Deve ser no futuro
            if meeting_datetime <= now:
                return False, "Data/hora deve ser no futuro"
            
            # Não pode ser muito distante (6 meses)
            max_future = now + timedelta(days=180)
            if meeting_datetime > max_future:
                return False, "Data não pode ser superior a 6 meses"
            
            # Horário comercial (6h às 23h)
            if meeting_time.hour < 6 or meeting_time.hour > 23:
                return False, "Horário deve ser entre 06:00 e 23:00"
            
            # Antecedência mínima (2 horas)
            min_advance = now + timedelta(hours=2)
            if meeting_datetime < min_advance:
                return False, "Reunião deve ser agendada com pelo menos 2 horas de antecedência"
            
            return True, "OK"
            
        except Exception as e:
            logger.error(f"Erro ao validar horário da reunião: {e}")
            return False, "Erro na validação"
    
    @staticmethod
    def check_time_conflicts(user, meeting_date, meeting_time, duration_minutes, exclude_meeting_id=None):
        """Verifica conflitos de horário para um usuário"""
        from .models import Meeting
        
        try:
            # Calcular início e fim da nova reunião
            start_datetime = datetime.combine(meeting_date, meeting_time)
            end_datetime = start_datetime + timedelta(minutes=duration_minutes)
            
            # Buscar reuniões do usuário no mesmo dia
            user_meetings = Meeting.objects.filter(
                creator=user,
                meeting_date=meeting_date,
                status__in=['published', 'approved']
            )
            
            # Excluir reunião atual se for update
            if exclude_meeting_id:
                user_meetings = user_meetings.exclude(id=exclude_meeting_id)
            
            conflicts = []
            for meeting in user_meetings:
                existing_start = datetime.combine(meeting.meeting_date, meeting.meeting_time)
                existing_end = existing_start + timedelta(minutes=meeting.duration_minutes)
                
                # Verificar sobreposição
                if (start_datetime < existing_end and end_datetime > existing_start):
                    conflicts.append({
                        'meeting': meeting,
                        'start_time': existing_start.time(),
                        'end_time': existing_end.time()
                    })
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Erro ao verificar conflitos: {e}")
            return []
    
    @staticmethod
    def send_meeting_notification(meeting, notification_type, recipients):
        """Enviar notificação por email sobre reunião"""
        if not recipients:
            return False
        
        try:
            subject_map = {
                'created': f'Nova reunião: {meeting.title}',
                'approved': f'Reunião aprovada: {meeting.title}',
                'reminder': f'Lembrete: {meeting.title} em breve',
                'cancelled': f'Reunião cancelada: {meeting.title}',
                'updated': f'Reunião atualizada: {meeting.title}',
                'participation_approved': f'Participação aprovada: {meeting.title}',
                'participation_rejected': f'Participação rejeitada: {meeting.title}',
            }
            
            subject = subject_map.get(notification_type, f'Atualização: {meeting.title}')
            
            message_map = {
                'created': f"""
                Olá!
                
                Uma nova reunião foi criada:
                
                Título: {meeting.title}
                Responsável: {meeting.responsible}
                Data: {meeting.meeting_date.strftime('%d/%m/%Y')}
                Horário: {meeting.meeting_time.strftime('%H:%M')}
                Duração: {meeting.duration_formatted}
                
                Descrição: {meeting.description}
                
                Link: {meeting.meeting_url}
                
                Atenciosamente,
                Equipe Tertúlia Literária
                """,
                
                'reminder': f"""
                Olá!
                
                Lembrete: sua reunião acontece em breve!
                
                Título: {meeting.title}
                Data: {meeting.meeting_date.strftime('%d/%m/%Y')}
                Horário: {meeting.meeting_time.strftime('%H:%M')}
                
                Link para participar: {meeting.meeting_url}
                {f"Senha: {meeting.meeting_password}" if meeting.meeting_password else ""}
                
                Não se esqueça!
                
                Atenciosamente,
                Equipe Tertúlia Literária
                """,
                
                'cancelled': f"""
                Olá!
                
                Infelizmente, a reunião "{meeting.title}" foi cancelada.
                
                Data original: {meeting.meeting_date.strftime('%d/%m/%Y')} às {meeting.meeting_time.strftime('%H:%M')}
                
                Pedimos desculpas pelo inconveniente.
                
                Atenciosamente,
                Equipe Tertúlia Literária
                """
            }
            
            message = message_map.get(notification_type, f"""
            Olá!
            
            Esta é uma notificação sobre a reunião "{meeting.title}":
            
            Data: {meeting.meeting_date.strftime('%d/%m/%Y')}
            Horário: {meeting.meeting_time.strftime('%H:%M')}
            Responsável: {meeting.responsible}
            
            Link: {meeting.meeting_url}
            
            Atenciosamente,
            Equipe Tertúlia Literária
            """)
            
            # Enviar email
            recipient_emails = []
            for recipient in recipients:
                if hasattr(recipient, 'email'):
                    recipient_emails.append(recipient.email)
                else:
                    recipient_emails.append(str(recipient))
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_emails,
                fail_silently=True
            )
            
            logger.info(f"Email enviado: {notification_type} para {len(recipient_emails)} destinatários")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
            return False
    
    @staticmethod
    def get_meeting_stats(user=None):
        """Obter estatísticas de reuniões"""
        from .models import Meeting, MeetingParticipation
        
        try:
            # Filtrar por usuário se especificado
            queryset = Meeting.objects.all()
            if user:
                queryset = queryset.filter(creator=user)
            
            # Estatísticas básicas
            total = queryset.count()
            published = queryset.filter(status='published').count()
            
            upcoming = queryset.filter(
                status='published',
                meeting_date__gte=timezone.now().date()
            ).count()
            
            finished = queryset.filter(status='finished').count()
            
            # Média de participantes
            meetings_with_participants = queryset.annotate(
                participant_count=Count('meetingparticipation', 
                                      filter=Q(meetingparticipation__status='approved'))
            )
            
            avg_participants = meetings_with_participants.aggregate(
                avg=Avg('participant_count')
            )['avg'] or 0
            
            # Estatísticas por categoria (se usuário específico)
            categories_stats = {}
            if user:
                from django.db.models import Q
                categories = queryset.values('category__name').annotate(
                    count=Count('id')
                ).order_by('-count')
                
                for cat in categories:
                    categories_stats[cat['category__name']] = cat['count']
            
            return {
                'total_meetings': total,
                'published_meetings': published,
                'upcoming_meetings': upcoming,
                'finished_meetings': finished,
                'average_participants': round(avg_participants, 1),
                'categories_stats': categories_stats,
                'total_participants': MeetingParticipation.objects.filter(
                    meeting__in=queryset,
                    status='approved'
                ).count() if not user else 0
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
            return {
                'total_meetings': 0,
                'published_meetings': 0,
                'upcoming_meetings': 0,
                'finished_meetings': 0,
                'average_participants': 0,
                'categories_stats': {},
                'total_participants': 0
            }
    
    @staticmethod
    def format_duration(minutes):
        """Formatar duração em texto legível"""
        if not minutes:
            return "Não definido"
        
        hours = minutes // 60
        mins = minutes % 60
        
        if hours and mins:
            return f"{hours}h {mins}min"
        elif hours:
            return f"{hours}h"
        else:
            return f"{mins}min"
    
    @staticmethod
    def get_meeting_url_info(url):
        """Extrair informações da URL da reunião"""
        import re
        
        info = {
            'platform': 'unknown',
            'is_valid': False,
            'meeting_id': None
        }
        
        if not url:
            return info
        
        try:
            # Zoom
            zoom_patterns = [
                r'zoom\.us/j/(\d+)',
                r'zoom\.com/j/(\d+)',
                r'us\d+\.zoom\.us/j/(\d+)'
            ]
            
            for pattern in zoom_patterns:
                match = re.search(pattern, url)
                if match:
                    info.update({
                        'platform': 'zoom',
                        'is_valid': True,
                        'meeting_id': match.group(1)
                    })
                    return info
            
            # Google Meet
            if 'meet.google.com' in url:
                meet_match = re.search(r'meet\.google\.com/([a-z-]+)', url)
                info.update({
                    'platform': 'google_meet',
                    'is_valid': True,
                    'meeting_id': meet_match.group(1) if meet_match else None
                })
                return info
            
            # Microsoft Teams
            if 'teams.microsoft.com' in url or 'teams.live.com' in url:
                info.update({
                    'platform': 'teams',
                    'is_valid': True
                })
                return info
            
            # YouTube
            youtube_patterns = [
                r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
                r'youtu\.be/([a-zA-Z0-9_-]+)'
            ]
            
            for pattern in youtube_patterns:
                match = re.search(pattern, url)
                if match:
                    info.update({
                        'platform': 'youtube',
                        'is_valid': True,
                        'meeting_id': match.group(1)
                    })
                    return info
            
            # Jitsi
            if 'jitsi' in url.lower():
                info.update({
                    'platform': 'jitsi',
                    'is_valid': True
                })
                return info
            
            # Discord
            if 'discord' in url.lower():
                info.update({
                    'platform': 'discord',
                    'is_valid': True
                })
                return info
            
            # URL genérica válida
            if url.startswith(('http://', 'https://')):
                info['is_valid'] = True
            
        except Exception as e:
            logger.error(f"Erro ao analisar URL: {e}")
        
        return info
    
    @staticmethod
    def generate_meeting_summary(meeting):
        """Gerar resumo da reunião"""
        try:
            participants_count = meeting.get_participant_count()
            comments_count = meeting.comments.filter(is_active=True).count()
            average_rating = meeting.get_average_rating()
            
            summary = {
                'meeting_id': meeting.id,
                'title': meeting.title,
                'date': meeting.meeting_date,
                'duration': meeting.duration_formatted,
                'participants_count': participants_count,
                'comments_count': comments_count,
                'average_rating': average_rating,
                'status': meeting.status,
                'view_count': meeting.view_count,
                'creator': meeting.creator.get_full_name(),
                'category': meeting.category.name,
                'tags': meeting.get_tags_list()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {e}")
            return None


# Funções auxiliares independentes

def validate_meeting_url(url, meeting_format):
    """Validar URL baseada no formato da reunião"""
    import re
    
    if not url or not meeting_format:
        return False, "URL e formato são obrigatórios"
    
    url_patterns = {
        'zoom': [r'zoom\.us', r'zoom\.com'],
        'teams': [r'teams\.microsoft\.com', r'teams\.live\.com'],
        'meet': [r'meet\.google\.com'],
        'youtube': [r'youtube\.com', r'youtu\.be'],
        'jitsi': [r'jitsi', r'meet\.jit\.si'],
        'discord': [r'discord\.gg', r'discord\.com'],
    }
    
    if meeting_format in url_patterns:
        patterns = url_patterns[meeting_format]
        for pattern in patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True, "URL válida"
        
        return False, f"URL não corresponde ao formato {meeting_format}"
    
    # Para outros formatos, apenas verificar se é uma URL válida
    if url.startswith(('http://', 'https://')):
        return True, "URL válida"
    
    return False, "URL deve começar com http:// ou https://"


def clean_tags(tags_string):
    """Limpar e validar tags"""
    if not tags_string:
        return ""
    
    # Dividir por vírgula e limpar
    tags = [tag.strip().lower() for tag in tags_string.split(',') if tag.strip()]
    
    # Remover duplicatas mantendo ordem
    unique_tags = []
    for tag in tags:
        if tag not in unique_tags and len(tag) >= 2 and len(tag) <= 20:
            unique_tags.append(tag)
    
    # Limitar a 10 tags
    return ', '.join(unique_tags[:10])


def calculate_meeting_end_time(meeting_date, meeting_time, duration_minutes):
    """Calcular horário de término da reunião"""
    try:
        start_datetime = datetime.combine(meeting_date, meeting_time)
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        return end_datetime
    except:
        return None