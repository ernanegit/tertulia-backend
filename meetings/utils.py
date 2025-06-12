# meetings/urls.py - ARQUIVO CORRIGIDO FINAL

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'meetings', views.MeetingViewSet, basename='meeting')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'comments', views.CommentViewSet, basename='comment')
router.register(r'ratings', views.RatingViewSet, basename='rating')

urlpatterns = [
    # ===== ENDPOINTS DE REUNIÕES =====
    
    # Participação básica
    path('meetings/<int:meeting_id>/join/', 
         views.JoinMeetingView.as_view(), 
         name='join_meeting'),
    
    path('meetings/<int:meeting_id>/leave/', 
         views.LeaveMeetingView.as_view(), 
         name='leave_meeting'),
    
    # ===== ENDPOINTS DE PARTICIPANTES =====
    
    # Listar participantes
    path('meetings/<int:meeting_id>/participants/', 
         views.MeetingParticipantsView.as_view(), 
         name='meeting_participants'),
    
    # Gerenciar participantes individuais
    path('meetings/<int:meeting_id>/manage-participant/', 
         views.ManageParticipantView.as_view(), 
         name='manage_participant'),
    
    # Minhas participações
    path('my-participations/', 
         views.MyParticipationsView.as_view(), 
         name='my_participations'),
    
    # ===== ENDPOINTS DE COOPERADORES =====
    
    # Listar cooperadores
    path('meetings/<int:meeting_id>/cooperators/', 
         views.MeetingCooperatorsView.as_view(), 
         name='meeting_cooperators'),
    
    # Solicitar cooperação
    path('meetings/<int:meeting_id>/request-cooperation/', 
         views.RequestCooperationView.as_view(), 
         name='request_cooperation'),
    
    # Gerenciar cooperação
    path('meetings/<int:meeting_id>/manage-cooperation/', 
         views.ManageCooperationView.as_view(), 
         name='manage_cooperation'),
    
    # Minhas cooperações
    path('my-cooperations/', 
         views.MyCooperationsView.as_view(), 
         name='my_cooperations'),
    
    # ===== ENDPOINTS LEGACY (compatibilidade) =====
    
    path('meetings/<int:meeting_id>/approve-participant/', 
         views.ApproveParticipantView.as_view(), 
         name='approve_participant'),
    
    path('meetings/<int:meeting_id>/reject-participant/', 
         views.RejectParticipantView.as_view(), 
         name='reject_participant'),
    
    path('meetings/<int:meeting_id>/approve-cooperation/', 
         views.ApproveCooperationView.as_view(), 
         name='approve_cooperation'),
    
    path('meetings/<int:meeting_id>/reject-cooperation/', 
         views.RejectCooperationView.as_view(), 
         name='reject_cooperation'),
    
    # ===== ENDPOINTS DE COMENTÁRIOS E AVALIAÇÕES =====
    
    # Comentários de reuniões específicas
    path('meetings/<int:meeting_id>/comments/', 
         views.MeetingCommentsView.as_view(), 
         name='meeting_comments'),
    
    # Avaliações de reuniões específicas
    path('meetings/<int:meeting_id>/ratings/', 
         views.MeetingRatingsView.as_view(), 
         name='meeting_ratings'),
    
    # Minha avaliação de uma reunião específica
    path('meetings/<int:meeting_id>/my-rating/', 
         views.MyMeetingRatingView.as_view(), 
         name='my_meeting_rating'),
    
    # ===== ENDPOINTS DE LISTAGEM E BUSCA =====
    
    # Próximas reuniões
    path('meetings/upcoming/', 
         views.UpcomingMeetingsView.as_view(), 
         name='upcoming_meetings'),
    
    # Minhas reuniões
    path('meetings/my-meetings/', 
         views.MyMeetingsView.as_view(), 
         name='my_meetings'),
    
    # Busca avançada
    path('meetings/search/', 
         views.SearchMeetingsView.as_view(), 
         name='search_meetings'),
    
    # ===== ROTAS DO ROUTER (ViewSets) =====
    
    # Inclui todas as rotas dos ViewSets:
    # GET/POST /api/meetings/ - MeetingViewSet
    # GET/PUT/PATCH/DELETE /api/meetings/{id}/ - MeetingViewSet
    # GET/POST /api/categories/ - CategoryViewSet
    # GET/PUT/PATCH/DELETE /api/categories/{id}/ - CategoryViewSet
    # GET/POST /api/comments/ - CommentViewSet
    # GET/PUT/PATCH/DELETE /api/comments/{id}/ - CommentViewSet
    # GET/POST /api/ratings/ - RatingViewSet
    # GET/PUT/PATCH/DELETE /api/ratings/{id}/ - RatingViewSet
    path('', include(router.urls)),
]


# ===== DOCUMENTAÇÃO DOS ENDPOINTS =====

"""
🚀 ENDPOINTS FUNCIONAIS DA API TERTÚLIA LITERÁRIA

===== REUNIÕES BÁSICAS =====
GET    /api/meetings/                          # Listar reuniões
POST   /api/meetings/                          # Criar reunião
GET    /api/meetings/{id}/                     # Detalhes da reunião
PUT    /api/meetings/{id}/                     # Atualizar reunião
DELETE /api/meetings/{id}/                     # Deletar reunião

===== PARTICIPAÇÃO EM REUNIÕES =====
POST   /api/meetings/{id}/join/                # Solicitar participação
POST   /api/meetings/{id}/leave/               # Cancelar participação

===== GERENCIAR PARTICIPANTES =====
GET    /api/meetings/{id}/participants/        # Listar participantes
    ?status=approved|pending|rejected|all     # Filtrar por status
POST   /api/meetings/{id}/manage-participant/  # Aprovar/rejeitar participante
    Body: {"participant_id": 2, "action": "approve|reject", "response_message": "..."}

===== MINHAS PARTICIPAÇÕES =====
GET    /api/my-participations/                 # Minhas participações
    ?status=approved|pending|rejected          # Filtrar por status
    ?period=upcoming|past|today                # Filtrar por período

===== COOPERADORES =====
GET    /api/meetings/{id}/cooperators/         # Listar cooperadores
    ?status=approved|pending|rejected|all     # Filtrar por status
POST   /api/meetings/{id}/request-cooperation/ # Solicitar cooperação
    Body: {"permissions": ["view", "edit"], "message": "..."}
POST   /api/meetings/{id}/manage-cooperation/  # Aprovar/rejeitar cooperação
    Body: {"cooperation_id": 3, "action": "approve|reject", "response_message": "..."}

===== MINHAS COOPERAÇÕES =====
GET    /api/my-cooperations/                   # Minhas cooperações
    ?status=approved|pending|rejected          # Filtrar por status
    ?period=active|expired|upcoming            # Filtrar por período

===== CATEGORIAS =====
GET    /api/categories/                        # Listar categorias
POST   /api/categories/                        # Criar categoria
GET    /api/categories/{id}/                   # Detalhes da categoria

===== COMENTÁRIOS =====
GET    /api/meetings/{id}/comments/            # Comentários de uma reunião
GET    /api/comments/                          # Todos os comentários
POST   /api/comments/                          # Criar comentário

===== AVALIAÇÕES =====
GET    /api/meetings/{id}/ratings/             # Avaliações de uma reunião
GET    /api/meetings/{id}/my-rating/           # Minha avaliação
GET    /api/ratings/                           # Todas as avaliações
POST   /api/ratings/                           # Criar avaliação

===== BUSCA E FILTROS =====
GET    /api/meetings/upcoming/                 # Próximas reuniões
GET    /api/meetings/my-meetings/              # Minhas reuniões
GET    /api/meetings/search/                   # Busca avançada
    ?q=termo&category=1&format=zoom&upcoming=true

===== EXEMPLOS DE USO =====

1. Criar reunião:
POST /api/meetings/
{
    "title": "Análise de Machado de Assis",
    "responsible": "João Silva",
    "description": "Discussão sobre Dom Casmurro",
    "category": 1,
    "meeting_date": "2025-07-15",
    "meeting_time": "19:30:00",
    "duration_minutes": 90,
    "meeting_format": "zoom",
    "meeting_url": "https://zoom.us/j/123456789"
}

2. Participar de reunião:
POST /api/meetings/1/join/
{
    "message": "Gostaria de participar desta discussão"
}

3. Solicitar cooperação:
POST /api/meetings/1/request-cooperation/
{
    "permissions": ["view", "edit", "moderate"],
    "message": "Posso ajudar a moderar esta reunião"
}

4. Aprovar participante:
POST /api/meetings/1/manage-participant/
{
    "participant_id": 2,
    "action": "approve",
    "response_message": "Bem-vindo à discussão!"
}
"""