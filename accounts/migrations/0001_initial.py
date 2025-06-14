# Generated by Django 4.2.7 on 2025-06-12 04:03

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email')),
                ('user_type', models.CharField(choices=[('participante', 'Participante'), ('cooperador', 'Cooperador'), ('criador', 'Criador de Reunião')], default='participante', max_length=20, verbose_name='Tipo de Usuário')),
                ('profile_image', models.ImageField(blank=True, help_text='Imagem de perfil (JPG, JPEG, PNG)', null=True, upload_to='profiles/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])], verbose_name='Foto de Perfil')),
                ('phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='Telefone')),
                ('bio', models.TextField(blank=True, max_length=500, null=True, verbose_name='Biografia')),
                ('is_email_verified', models.BooleanField(default=False, verbose_name='Email Verificado')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('max_cooperations', models.PositiveIntegerField(default=5, verbose_name='Máximo de Cooperações')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Usuário',
                'verbose_name_plural': 'Usuários',
                'ordering': ['-created_at'],
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='CooperatorRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pendente'), ('approved', 'Aprovado'), ('rejected', 'Rejeitado')], default='pending', max_length=10, verbose_name='Status')),
                ('message', models.TextField(blank=True, max_length=500, verbose_name='Mensagem')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('cooperator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cooperator_requests', to=settings.AUTH_USER_MODEL, verbose_name='Cooperador')),
                ('meeting_creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_cooperator_requests', to=settings.AUTH_USER_MODEL, verbose_name='Criador da Reunião')),
            ],
            options={
                'verbose_name': 'Solicitação de Cooperação',
                'verbose_name_plural': 'Solicitações de Cooperação',
                'ordering': ['-created_at'],
                'unique_together': {('cooperator', 'meeting_creator')},
            },
        ),
    ]
