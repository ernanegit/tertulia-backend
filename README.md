# Tertúlia Literária - Backend

Sistema de gerenciamento de reuniões online focado em eventos literários.

## 🚀 Funcionalidades

### ✅ Implementadas
- **Autenticação completa** - Login, registro, perfil de usuário
- **Sistema de usuários** - Participantes, Cooperadores, Criadores
- **Gerenciamento de reuniões** - CRUD completo com aprovação
- **Categorias** - Organização por temas literários
- **Participação** - Solicitação e aprovação de participantes
- **Cooperação** - Sistema de cooperadores com permissões
- **Comentários** - Sistema de comentários nas reuniões
- **Avaliações** - Sistema de rating com estrelas
- **API REST completa** - Endpoints documentados
- **Admin Panel** - Interface administrativa avançada

### 🔄 Em desenvolvimento
- Notificações em tempo real
- Upload de imagens
- Sistema de busca avançada
- Filtros complexos
- Estatísticas e relatórios

## 🛠️ Tecnologias

- **Backend**: Django 4.2.7 + Django REST Framework
- **Banco de dados**: SQLite (desenvolvimento) / PostgreSQL (produção)
- **Autenticação**: Token Authentication
- **API**: REST com paginação e filtros
- **Admin**: Django Admin customizado

## 📦 Instalação

### Pré-requisitos
- Python 3.9+
- pip

### Setup do projeto

```bash
# Clonar repositório
git clone https://github.com/ernanegit/tertulia-backend.git
cd tertulia-backend

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows
.\venv\Scripts\Activate.ps1
# Linux/Mac
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# Aplicar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
```

## 🔧 Configuração

### Variáveis de ambiente (.env)
```bash
SECRET_KEY=sua-chave-secreta
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
```

## 📚 API Endpoints

### Autenticação
- `POST /api/auth/register/` - Registro de usuário
- `POST /api/auth/login/` - Login
- `POST /api/auth/logout/` - Logout
- `GET /api/auth/profile/` - Perfil do usuário

### Reuniões
- `GET /api/meetings/` - Listar reuniões
- `POST /api/meetings/` - Criar reunião
- `GET /api/meetings/{id}/` - Detalhes da reunião
- `PUT /api/meetings/{id}/` - Atualizar reunião
- `DELETE /api/meetings/{id}/` - Deletar reunião

### Participação
- `POST /api/meetings/{id}/join/` - Solicitar participação
- `POST /api/meetings/{id}/leave/` - Cancelar participação
- `POST /api/meetings/{id}/approve-participant/` - Aprovar participante

### Categorias
- `GET /api/categories/` - Listar categorias
- `POST /api/categories/` - Criar categoria

### Comentários e Avaliações
- `GET /api/meetings/{id}/comments/` - Comentários da reunião
- `POST /api/meetings/{id}/comments/` - Adicionar comentário
- `GET /api/meetings/{id}/ratings/` - Avaliações da reunião
- `POST /api/meetings/{id}/rate/` - Avaliar reunião

## 🗂️ Estrutura do Projeto

```
tertulia-backend/
├── accounts/              # App de usuários
│   ├── models.py         # Modelo User customizado
│   ├── views.py          # Views de autenticação
│   ├── serializers.py    # Serializers de usuário
│   └── urls.py           # URLs de auth
├── meetings/             # App principal
│   ├── models.py         # Modelos de reunião
│   ├── views.py          # Views da API
│   ├── serializers.py    # Serializers da API
│   ├── admin.py          # Admin customizado
│   ├── filters.py        # Filtros para API
│   ├── permissions.py    # Permissões customizadas
│   └── urls.py           # URLs da API
├── core/                 # App auxiliar
├── tertulia_backend/     # Configurações
│   ├── settings.py       # Configurações Django
│   └── urls.py           # URLs principais
├── requirements.txt      # Dependências
├── .env.example         # Exemplo de variáveis
└── manage.py            # Script Django
```

## 💾 Modelos de Dados

### User (Usuário)
- Tipos: Participante, Cooperador, Criador
- Campos: nome, email, bio, telefone, etc.

### Meeting (Reunião)
- Status: Rascunho, Publicada, Finalizada, etc.
- Campos: título, descrição, data, hora, formato, URL
- Relacionamentos: criador, participantes, cooperadores

### Category (Categoria)
- Organização temática das reuniões
- Campos: nome, descrição, cor, ícone

### MeetingParticipation (Participação)
- Relacionamento many-to-many entre User e Meeting
- Status: Pendente, Aprovado, Rejeitado

### Comment (Comentário)
- Comentários nas reuniões
- Suporte a respostas (threading)

### Rating (Avaliação)
- Avaliações de 1-5 estrelas
- Comentários opcionais

## 🔐 Permissões

- **Participantes**: Visualizar e participar de reuniões
- **Cooperadores**: Criar reuniões (com aprovação)
- **Criadores**: Criar, gerenciar e aprovar reuniões
- **Admins**: Acesso total ao sistema

## 🧪 Testes

```bash
# Executar testes
python manage.py test

# Com coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 📈 Status do Desenvolvimento

- [x] Configuração inicial do projeto
- [x] Modelos de dados completos
- [x] Sistema de autenticação
- [x] API REST básica
- [x] Admin panel customizado
- [x] Sistema de permissões
- [ ] Testes automatizados
- [ ] Documentação da API (Swagger)
- [ ] Sistema de notificações
- [ ] Upload de arquivos
- [ ] Deploy em produção

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👥 Autores

- **Ernane** - Desenvolvedor Principal

## 📞 Contato

- GitHub: [@ernanegit](https://github.com/ernanegit)
- Email: [seu-email@exemplo.com]

---

**Tertúlia Literária** - Conectando pessoas através da literatura 📚