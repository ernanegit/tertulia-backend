from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate, login
from .models import User, CooperatorRequest
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    ChangePasswordSerializer, CooperatorRequestSerializer
)


class RegisterView(APIView):
    """Registro de novos usuários - SEM TOKEN"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'user': UserSerializer(user).data,
                'message': 'Usuário criado com sucesso!'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Login de usuários - SEM TOKEN"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    login(request, user)
                    return Response({
                        'user': UserSerializer(user).data,
                        'message': 'Login realizado com sucesso!'
                    })
                else:
                    return Response({
                        'error': 'Credenciais inválidas'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            except User.DoesNotExist:
                return Response({
                    'error': 'Usuário não encontrado'
                }, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Logout de usuários"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        return Response({'message': 'Logout realizado com sucesso!'})


class RefreshTokenView(APIView):
    """Renovar token"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        return Response({'message': 'Token ainda válido'})


class ProfileView(APIView):
    """Perfil do usuário logado"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """Alterar senha do usuário"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.validated_data['old_password']):
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({'message': 'Senha alterada com sucesso!'})
            return Response({'error': 'Senha atual incorreta'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CooperatorRequestView(APIView):
    """Solicitar ser cooperador"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        return Response({'message': 'Funcionalidade em desenvolvimento'})


class CooperatorRequestListView(APIView):
    """Listar solicitações de cooperação"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response({
            'received': [],
            'sent': []
        })


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet para usuários"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)