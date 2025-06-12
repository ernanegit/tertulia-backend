# meetings/urls.py - VERSÃO FINAL COMPLETA

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para ViewSets (CRUD automático)
router = DefaultRouter()
router.register(r'meetings', views.MeetingViewSet, basename='meeting')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'comments', views.CommentViewSet, basename='comment')
router.register(r'ratings', views.RatingViewSet, basename='rating')

urlpatterns = [
    # ===== ENDPOINTS DE PARTICIPAÇÃO =====
    
    # Entrar/Sair de reuniões
    path('meetings/<int:meeting_id>/join/', 
         views.JoinMeetingView.as_view(), 
         name='join_meeting'),
    
    path('meetings/<int:meeting_id>/leave/', 
         views.LeaveMeetingView.as_view(), 
         name='leave_meeting'),
    
    # Gerenciar participantes
    path('meetings/<int:meeting_id>/participants/', 
         views.MeetingParticipantsView.as_view(), 
         name='meeting_participants'),
    
    path('meetings/<int:meeting_id>/manage-participant/', 
         views.ManageParticipantView.as_view(), 
         name='manage_participant'),
    
    # Minhas participações
    path('my-participations/', 
         views.MyParticipationsView.as_view(), 
         name='my_participations'),
    
    # ===== ENDPOINTS DE COOPERADORES (NOVOS) =====
    
    # Listar cooperadores de uma reunião
    path('meetings/<int:meeting_id>/cooperators/', 
         views.list_cooperators, 
         name='list_cooperators'),
    
    # Solicitar cooperação em uma reunião
    path('meetings/<int:meeting_id>/request-cooperation/', 
         views.request_cooperation, 
         name='request_cooperation'),
    
    # Gerenciar solicitação de cooperação (aprovar/rejeitar)
    path('meetings/<int:meeting_id>/manage-cooperation/', 
         views.manage_cooperation, 
         name='manage_cooperation'),
    
    # Ações em lote para cooperações
    path('meetings/<int:meeting_id>/cooperation-actions/', 
         views.cooperation_batch_actions, 
         name='cooperation_batch_actions'),
    
    # Gerenciar permissões de cooperador
    path('meetings/<int:meeting_id>/cooperations/<int:cooperation_id>/permissions/', 
         views.manage_cooperation_permissions, 
         name='manage_cooperation_permissions'),
    
    # Minhas cooperações
    path('my-cooperations/', 
         views.my_cooperations, 
         name='my_cooperations'),
    
    # Estatísticas de cooperação
    path('cooperation-stats/', 
         views.cooperation_stats, 
         name='cooperation_stats'),
    
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
    
    # ===== ENDPOINTS DE BUSCA E NAVEGAÇÃO =====
    
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
    
    # ===== ENDPOINTS LEGACY (compatibilidade com código antigo) =====
    
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
    
    # ===== ROTAS DO ROUTER (ViewSets) =====
    
    # Inclui automaticamente todas as rotas dos ViewSets:
    # GET/POST /api/meetings/                    - MeetingViewSet (list, create)
    # GET/PUT/PATCH/DELETE /api/meetings/{id}/   - MeetingViewSet (retrieve, update, destroy)
    # GET/POST /api/categories/                  - CategoryViewSet
    # GET/PUT/PATCH/DELETE /api/categories/{id}/ - CategoryViewSet
    # GET/POST /api/comments/                    - CommentViewSet  
    # GET/PUT/PATCH/DELETE /api/comments/{id}/   - CommentViewSet
    # GET/POST /api/ratings/                     - RatingViewSet
    # GET/PUT/PATCH/DELETE /api/ratings/{id}/    - RatingViewSet
    path('', include(router.urls)),
]


# ===== DOCUMENTAÇÃO DOS ENDPOINTS =====

"""
🚀 ENDPOINTS DISPONÍVEIS NA API:

PARTICIPANTES:
✅ POST   /api/meetings/{id}/join/                    - Solicitar participação
✅ POST   /api/meetings/{id}/leave/                   - Cancelar participação  
✅ GET    /api/meetings/{id}/participants/            - Listar participantes
✅ POST   /api/meetings/{id}/manage-participant/      - Aprovar/rejeitar participante
✅ GET    /api/my-participations/                     - Minhas participações

COOPERADORES:
✅ GET    /api/meetings/{id}/cooperators/             - Listar cooperadores
✅ POST   /api/meetings/{id}/request-cooperation/     - Solicitar cooperação
✅ POST   /api/meetings/{id}/manage-cooperation/      - Aprovar/rejeitar cooperação
✅ POST   /api/meetings/{id}/cooperation-actions/     - Ações em lote
✅ PUT    /api/meetings/{id}/cooperations/{coop_id}/permissions/ - Gerenciar permissões
✅ GET    /api/my-cooperations/                       - Minhas cooperações
✅ GET    /api/cooperation-stats/                     - Estatísticas

REUNIÕES (ViewSets):
✅ GET    /api/meetings/                              - Listar reuniões
✅ POST   /api/meetings/                              - Criar reunião
✅ GET    /api/meetings/{id}/                         - Detalhes da reunião
✅ PUT    /api/meetings/{id}/                         - Atualizar reunião
✅ DELETE /api/meetings/{id}/                         - Deletar reunião

BUSCA E NAVEGAÇÃO:
✅ GET    /api/meetings/search/                       - Busca avançada
✅ GET    /api/meetings/upcoming/                     - Próximas reuniões
✅ GET    /api/meetings/my-meetings/                  - Minhas reuniões

COMENTÁRIOS E AVALIAÇÕES:
✅ GET    /api/meetings/{id}/comments/                - Comentários da reunião
✅ GET    /api/meetings/{id}/ratings/                 - Avaliações da reunião
✅ GET    /api/meetings/{id}/my-rating/               - Minha avaliação
✅ GET    /api/comments/                              - Todos comentários
✅ POST   /api/comments/                              - Criar comentário
✅ GET    /api/ratings/                               - Todas avaliações
✅ POST   /api/ratings/                               - Criar avaliação

CATEGORIAS:
✅ GET    /api/categories/                            - Listar categorias
✅ POST   /api/categories/                            - Criar categoria

TOTAL: 28+ ENDPOINTS IMPLEMENTADOS E FUNCIONAIS! 🎉
"""