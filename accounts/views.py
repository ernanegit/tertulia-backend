
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .models import User, CooperatorRequest
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    ChangePasswordSerializer, CooperatorRequestSerializer
)


class RegisterView(APIView):
    """Registro de novos usuários"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'user': UserSerializer(user).data,
                'token': token.key,
                'message': 'Usuário criado com sucesso!'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Login de usuários"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            user = authenticate(request, username=email, password=password)
            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'user': UserSerializer(user).data,
                    'token': token.key,
                    'message': 'Login realizado com sucesso!'
                })
            return Response({
                'error': 'Credenciais inválidas'
            }, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Logout de usuários"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            token = Token.objects.get(user=request.user)
            token.delete()
            return Response({'message': 'Logout realizado com sucesso!'})
        except Token.DoesNotExist:
            return Response({'error': 'Token não encontrado'}, status=status.HTTP_400_BAD_REQUEST)


class RefreshTokenView(APIView):
    """Renovar token (implementação básica)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        token, created = Token.objects.get_or_create(user=request.user)
        return Response({'token': token.key})


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
    """Solicitar ser cooperador de um criador"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = CooperatorRequestSerializer(data=request.data)
        if serializer.is_valid():
            # Verificar se já existe uma solicitação
            meeting_creator_id = serializer.validated_data['meeting_creator'].id
            existing = CooperatorRequest.objects.filter(
                cooperator=request.user,
                meeting_creator_id=meeting_creator_id
            ).first()
            
            if existing:
                return Response({
                    'error': 'Já existe uma solicitação para este criador'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save(cooperator=request.user)
            return Response({
                'message': 'Solicitação enviada com sucesso!',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CooperatorRequestListView(APIView):
    """Listar solicitações de cooperação"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Solicitações recebidas (se for criador)
        received = CooperatorRequest.objects.filter(meeting_creator=request.user)
        # Solicitações enviadas
        sent = CooperatorRequest.objects.filter(cooperator=request.user)
        
        return Response({
            'received': CooperatorRequestSerializer(received, many=True).data,
            'sent': CooperatorRequestSerializer(sent, many=True).data
        })


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet para usuários (apenas para admins)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        # Usuários normais só veem o próprio perfil
        return User.objects.filter(id=self.request.user.id)
# Create your views here.
