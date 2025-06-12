# meetings/permissions.py - PERMISSÕES CUSTOMIZADAS

from rest_framework import permissions
from .models import MeetingCooperation, Meeting


class IsMeetingCreatorOrCooperator(permissions.BasePermission):
    """
    Permissão que permite apenas criadores da reunião ou cooperadores aprovados
    """
    
    def has_object_permission(self, request, view, obj):
        # Permitir leitura para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Verificar se o usuário está autenticado
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins podem tudo
        if request.user.is_staff:
            return True
        
        # Criador da reunião pode editar
        if obj.creator == request.user:
            return True
        
        # Cooperador aprovado pode editar
        try:
            cooperation = MeetingCooperation.objects.get(
                meeting=obj,
                cooperator=request.user,
                status='approved'
            )
            # Verificar se tem permissão de edição
            return 'edit' in cooperation.permissions or not cooperation.permissions
        except MeetingCooperation.DoesNotExist:
            return False


class CanManageParticipants(permissions.BasePermission):
    """
    Permissão para gerenciar participantes (aprovar/rejeitar)
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins podem tudo
        if request.user.is_staff:
            return True
        
        # Criador da reunião pode gerenciar
        if obj.creator == request.user:
            return True
        
        # Cooperador com permissão específica
        try:
            cooperation = MeetingCooperation.objects.get(
                meeting=obj,
                cooperator=request.user,
                status='approved'
            )
            return 'manage_participants' in cooperation.permissions
        except MeetingCooperation.DoesNotExist:
            return False


class CanModerateComments(permissions.BasePermission):
    """
    Permissão para moderar comentários
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Autor do comentário pode editar/deletar
        if hasattr(obj, 'author') and obj.author == request.user:
            return True
        
        # Admins podem moderar
        if request.user.is_staff:
            return True
        
        # Criador da reunião pode moderar comentários
        if hasattr(obj, 'meeting') and obj.meeting.creator == request.user:
            return True
        
        # Cooperador com permissão de moderação
        if hasattr(obj, 'meeting'):
            try:
                cooperation = MeetingCooperation.objects.get(
                    meeting=obj.meeting,
                    cooperator=request.user,
                    status='approved'
                )
                return 'moderate' in cooperation.permissions
            except MeetingCooperation.DoesNotExist:
                return False
        
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permissão que permite apenas ao dono do objeto editar
    """
    
    def has_object_permission(self, request, view, obj):
        # Permitir leitura para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Verificar se o usuário é o dono
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'author'):
            return obj.author == request.user
        elif hasattr(obj, 'participant'):
            return obj.participant == request.user
        elif hasattr(obj, 'cooperator'):
            return obj.cooperator == request.user
        
        return False


class IsCreatorOnly(permissions.BasePermission):
    """
    Permissão apenas para criadores de reunião
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
               request.user.user_type in ['criador', 'cooperador']


class CanCreateMeeting(permissions.BasePermission):
    """
    Permissão para criar reuniões
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Apenas criadores e cooperadores podem criar reuniões
        if request.user.user_type not in ['criador', 'cooperador']:
            return False
        
        # Verificar limite de reuniões ativas para cooperadores
        if request.user.user_type == 'cooperador':
            active_meetings = Meeting.objects.filter(
                creator=request.user,
                status__in=['published', 'approved', 'pending_approval']
            ).count()
            
            # Limite de 5 reuniões ativas por cooperador
            if active_meetings >= 5:
                return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class HasParticipatedInMeeting(permissions.BasePermission):
    """
    Permissão que verifica se o usuário participou da reunião
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Para avaliações - só pode avaliar quem participou
        meeting = obj if hasattr(obj, 'meetingparticipation_set') else obj.meeting
        
        # Criador pode avaliar sua própria reunião
        if meeting.creator == request.user:
            return True
        
        # Verificar se participou da reunião
        from .models import MeetingParticipation
        return MeetingParticipation.objects.filter(
            meeting=meeting,
            participant=request.user,
            status__in=['approved', 'attended']
        ).exists()


class CanJoinMeeting(permissions.BasePermission):
    """
    Permissão para participar de reuniões
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Verificar se a reunião permite participação
        if obj.status != 'published':
            return False
        
        # Verificar se a reunião já passou
        if obj.is_finished:
            return False
        
        # Verificar tipo de acesso
        if obj.access_type == 'private':
            # Apenas por convite - verificar se foi convidado
            return False  # Implementar lógica de convites
        
        # Verificar limite de participantes
        if obj.max_participants:
            current_participants = obj.get_participant_count()
            if current_participants >= obj.max_participants:
                return False
        
        return True


class CanRequestCooperation(permissions.BasePermission):
    """
    Permissão para solicitar cooperação
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Apenas cooperadores podem solicitar cooperação
        return request.user.user_type == 'cooperador'
    
    def has_object_permission(self, request, view, obj):
        if not self.has_permission(request, view):
            return False
        
        # Não pode solicitar cooperação em sua própria reunião
        if obj.creator == request.user:
            return False
        
        # Verificar se já não é cooperador
        try:
            cooperation = MeetingCooperation.objects.get(
                meeting=obj,
                cooperator=request.user
            )
            # Se já existe, não pode solicitar novamente
            return False
        except MeetingCooperation.DoesNotExist:
            return True


class CanApproveCooperation(permissions.BasePermission):
    """
    Permissão para aprovar cooperação
    """
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Apenas criador da reunião pode aprovar cooperação
        return obj.creator == request.user


class IsActiveUser(permissions.BasePermission):
    """
    Permissão que verifica se o usuário está ativo
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_active