from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, CooperatorRequest


class UserSerializer(serializers.ModelSerializer):
    """Serializer para modelo User"""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'full_name', 'user_type', 'phone', 'bio', 
            'is_email_verified', 'max_cooperations', 'created_at'
        ]
        read_only_fields = ['id', 'is_email_verified', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer para registro de usuários"""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'user_type'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("As senhas não coincidem.")
        return attrs
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email já está em uso.")
        return value
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nome de usuário já está em uso.")
        return value
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer para login"""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para mudança de senha"""
    
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("As novas senhas não coincidem.")
        return attrs


class CooperatorRequestSerializer(serializers.ModelSerializer):
    """Serializer para solicitações de cooperação"""
    
    cooperator_name = serializers.CharField(source='cooperator.get_full_name', read_only=True)
    meeting_creator_name = serializers.CharField(source='meeting_creator.get_full_name', read_only=True)
    
    class Meta:
        model = CooperatorRequest
        fields = [
            'id', 'cooperator', 'cooperator_name', 'meeting_creator', 
            'meeting_creator_name', 'status', 'message', 'created_at'
        ]
        read_only_fields = ['id', 'cooperator', 'created_at']