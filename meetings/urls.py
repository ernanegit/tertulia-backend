# meetings/urls.py - URLS COMPLETAS COM PARTICIPANTES

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
    
    # Ações em lote para participantes
    path('meetings/<int:meeting_id>/participant-actions/', 
         views.ParticipantActionsView.as_view(), 
         name='participant_actions'),
    
    # Minhas participações
    path('my-participations/', 
         views.MyParticipationsView.as_view(), 
         name='my_participations'),
    
    # ===== ENDPOINTS DE COOPERAÇÃO =====
    
    path('meetings/<int:meeting_id>/request-cooperation/', 
         views.RequestCooperationView.as_view(), 
         name='request_cooperation'),
    
    path('meetings/<int:meeting_id>/approve-cooperation/', 
         views.ApproveCooperationView.as_view(), 
         name='approve_cooperation'),
    
    path('meetings/<int:meeting_id>/reject-cooperation/', 
         views.RejectCooperationView.as_view(), 
         name='reject_cooperation'),
    
    # ===== ENDPOINTS LEGACY (compatibilidade) =====
    
    path('meetings/<int:meeting_id>/approve-participant/', 
         views.ApproveParticipantView.as_view(), 
         name='approve_participant'),
    
    path('meetings/<int:meeting_id>/reject-participant/', 
         views.RejectParticipantView.as_view(), 
         name='reject_participant'),
    
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