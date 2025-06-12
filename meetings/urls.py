from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'meetings', views.MeetingViewSet, basename='meeting')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'comments', views.CommentViewSet, basename='comment')
router.register(r'ratings', views.RatingViewSet, basename='rating')

urlpatterns = [
    # Endpoints específicos de reuniões
    path('meetings/<int:meeting_id>/join/', views.JoinMeetingView.as_view(), name='join_meeting'),
    path('meetings/<int:meeting_id>/leave/', views.LeaveMeetingView.as_view(), name='leave_meeting'),
    path('meetings/<int:meeting_id>/approve-participant/', views.ApproveParticipantView.as_view(), name='approve_participant'),
    path('meetings/<int:meeting_id>/reject-participant/', views.RejectParticipantView.as_view(), name='reject_participant'),
    
    # Cooperação em reuniões
    path('meetings/<int:meeting_id>/request-cooperation/', views.RequestCooperationView.as_view(), name='request_cooperation'),
    path('meetings/<int:meeting_id>/approve-cooperation/', views.ApproveCooperationView.as_view(), name='approve_cooperation'),
    path('meetings/<int:meeting_id>/reject-cooperation/', views.RejectCooperationView.as_view(), name='reject_cooperation'),
    
    # Comentários e avaliações de reuniões específicas
    path('meetings/<int:meeting_id>/comments/', views.MeetingCommentsView.as_view(), name='meeting_comments'),
    path('meetings/<int:meeting_id>/ratings/', views.MeetingRatingsView.as_view(), name='meeting_ratings'),
    path('meetings/<int:meeting_id>/my-rating/', views.MyMeetingRatingView.as_view(), name='my_meeting_rating'),
    
    # Estatísticas e relatórios
    path('meetings/upcoming/', views.UpcomingMeetingsView.as_view(), name='upcoming_meetings'),
    path('meetings/my-meetings/', views.MyMeetingsView.as_view(), name='my_meetings'),
    path('meetings/search/', views.SearchMeetingsView.as_view(), name='search_meetings'),
    
    # ViewSets do router
    path('', include(router.urls)),
]