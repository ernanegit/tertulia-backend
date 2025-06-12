from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    # Autenticação JWT
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('refresh/', views.RefreshTokenView.as_view(), name='token_refresh'),
    
    # Perfil do usuário
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # Cooperação
    path('cooperator-request/', views.CooperatorRequestView.as_view(), name='cooperator_request'),
    path('cooperator-requests/', views.CooperatorRequestListView.as_view(), name='cooperator_requests'),
    
    # ViewSets do router
    path('', include(router.urls)),
]