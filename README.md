# Tertúlia Literária - Backend

Sistema completo de gerenciamento de reuniões online focado em eventos literários com sistema avançado de cooperação entre usuários.

## 🚀 Funcionalidades

### ✅ **Completamente Implementadas e Testadas**
- **Autenticação completa** - Login, registro, perfil de usuário com session/token auth
- **Sistema de usuários** - Participantes, Cooperadores, Criadores com tipos diferenciados
- **Gerenciamento de reuniões** - CRUD completo com aprovação e status avançados
- **Categorias** - Organização por temas literários com cores e ícones
- **Participação** - Solicitação, aprovação e gerenciamento de participantes
- **🤝 Sistema de Cooperação** - **NOVO!** Sistema completo de cooperadores com permissões
- **Comentários** - Sistema de comentários nas reuniões com threading
- **Avaliações** - Sistema de rating com estrelas e aspectos detalhados
- **API REST completa** - 28+ endpoints documentados e testados
- **Admin Panel** - Interface administrativa avançada e customizada
- **Filtros e Busca** - Sistema de filtros avançados com django-filter
- **Notificações** - Sistema de notificações automáticas via signals

### 🔄 Em desenvolvimento
- Notificações em tempo real (WebSocket)
- Upload de imagens e arquivos
- Sistema de convites privados
- Relatórios e analytics avançados
- Integração com calendários externos

## 🛠️ Tecnologias

- **Backend**: Django 4.2.7 + Django REST Framework 3.14.0
- **Banco de dados**: SQLite (desenvolvimento) / PostgreSQL (produção)
- **Autenticação**: Session + Token Authentication
- **API**: REST com paginação, filtros e browsable interface
- **Admin**: Django Admin customizado com interfaces especializadas
- **Filtros**: django-filter para busca avançada
- **CORS**: django-cors-headers para frontend
- **Validações**: Validações customizadas e signals

## 📦 Instalação

### Pré-requisitos
- Python 3.9+
- pip
- Git

### Setup do projeto

```bash
# Clonar repositório
git clone https://github.com/ernanegit/tertulia-backend.git
cd tertulia-backend

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows PowerShell
.\venv\Scripts\Activate.ps1
# Windows CMD
venv\Scripts\activate
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

# Criar dados de teste (opcional)
python manage.py shell
# Execute os comandos de criação de categorias e usuários

# Iniciar servidor
python manage.py runserver
```

## 🔧 Configuração

### Variáveis de ambiente (.env)
```bash
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3

# Email (opcional)
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-app

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## 📚 API Endpoints

### 🔐 **Autenticação**
- `POST /api/auth/register/` - Registro de usuário
- `POST /api/auth/login/` - Login
- `POST /api/auth/logout/` - Logout
- `GET /api/auth/profile/` - Perfil do usuário
- `POST /api/auth/change-password/` - Alterar senha

### 📅 **Reuniões**
- `GET /api/meetings/` - Listar reuniões (com filtros)
- `POST /api/meetings/` - Criar reunião
- `GET /api/meetings/{id}/` - Detalhes da reunião
- `PUT /api/meetings/{id}/` - Atualizar reunião
- `DELETE /api/meetings/{id}/` - Deletar reunião
- `GET /api/meetings/upcoming/` - Próximas reuniões
- `GET /api/meetings/my-meetings/` - Minhas reuniões
- `GET /api/meetings/search/` - Busca avançada

### 👥 **Participação**
- `POST /api/meetings/{id}/join/` - Solicitar participação
- `POST /api/meetings/{id}/leave/` - Cancelar participação
- `GET /api/meetings/{id}/participants/` - Listar participantes
- `POST /api/meetings/{id}/manage-participant/` - Aprovar/rejeitar participante
- `GET /api/my-participations/` - Minhas participações

### 🤝 **Cooperação** *(Novo Sistema Testado!)*
- `GET /api/meetings/{id}/cooperators/` - Listar cooperadores
- `POST /api/meetings/{id}/request-cooperation/` - Solicitar cooperação
- `POST /api/meetings/{id}/manage-cooperation/` - Aprovar/rejeitar cooperação
- `PUT /api/meetings/{id}/cooperations/{coop_id}/permissions/` - Gerenciar permissões
- `GET /api/my-cooperations/` - Minhas cooperações
- `GET /api/cooperation-stats/` - Estatísticas de cooperação

### 🏷️ **Categorias**
- `GET /api/categories/` - Listar categorias
- `POST /api/categories/` - Criar categoria

### 💬 **Comentários e Avaliações**
- `GET /api/meetings/{id}/comments/` - Comentários da reunião
- `POST /api/comments/` - Adicionar comentário
- `GET /api/meetings/{id}/ratings/` - Avaliações da reunião
- `POST /api/ratings/` - Avaliar reunião
- `GET /api/meetings/{id}/my-rating/` - Minha avaliação

## 🗂️ Estrutura do Projeto

```
tertulia-backend/
├── accounts/              # App de usuários e autenticação
│   ├── models.py         # User customizado com tipos
│   ├── views.py          # Views de autenticação
│   ├── serializers.py    # Serializers de usuário
│   ├── admin.py          # Admin customizado
│   └── urls.py           # URLs de auth
├── meetings/             # App principal de reuniões
│   ├── models.py         # Modelos de reunião e cooperação
│   ├── views.py          # Views da API REST
│   ├── serializers.py    # Serializers da API
│   ├── admin.py          # Admin customizado
│   ├── filters.py        # Filtros avançados
│   ├── permissions.py    # Permissões customizadas
│   ├── signals.py        # Signals para notificações
│   ├── utils.py          # Utilitários e helpers
│   └── urls.py           # URLs da API
├── core/                 # App auxiliar
├── tertulia_backend/     # Configurações Django
│   ├── settings.py       # Configurações completas
│   └── urls.py           # URLs principais
├── requirements.txt      # Dependências
├── .env.example         # Exemplo de variáveis
├── .gitignore           # Arquivos ignorados
└── manage.py            # Script Django
```

## 💾 Modelos de Dados

### **User (Usuário)**
- Tipos: `participante`, `cooperador`, `criador`
- Campos: nome, email, bio, telefone, tipo, imagem
- Validações: email único, tipos específicos

### **Meeting (Reunião)**
- Status: `draft`, `pending_approval`, `published`, `finished`, etc.
- Campos: título, descrição, data, hora, formato, URL, agenda
- Relacionamentos: criador, participantes, cooperadores, categoria
- Validações: data futura, URL por formato, duração

### **Category (Categoria)**
- Organização temática das reuniões
- Campos: nome, descrição, cor, ícone, ordem
- Sistema de cores hexadecimais

### **MeetingParticipation (Participação)**
- Relacionamento many-to-many entre User e Meeting
- Status: `pending`, `approved`, `rejected`, `attended`
- Controle de presença e mensagens

### **MeetingCooperation (Cooperação)** *(Novo!)*
- Sistema de cooperadores com permissões granulares
- Permissões: `view`, `edit`, `moderate`, `manage_participants`
- Status: `pending`, `approved`, `rejected`, `expired`
- Sistema de expiração automática

### **Comment (Comentário)**
- Comentários nas reuniões com threading
- Suporte a respostas aninhadas
- Sistema de likes e moderação

### **Rating (Avaliação)**
- Avaliações de 1-5 estrelas
- Comentários opcionais e aspectos detalhados
- Avaliações anônimas opcionais

## 🔐 Sistema de Permissões

### **Participantes**
- Visualizar reuniões públicas
- Solicitar participação
- Comentar e avaliar (após participar)

### **Cooperadores**
- Criar reuniões (com aprovação)
- Solicitar cooperação em outras reuniões
- Permissões específicas quando aprovados

### **Criadores**
- Criar e publicar reuniões livremente
- Gerenciar participantes e cooperadores
- Moderar comentários e conteúdo

### **Admins**
- Acesso total ao sistema
- Gerenciamento via Django Admin
- Aprovação de reuniões e usuários

## 🧪 Testes

### **Endpoints Testados (Sistema de Cooperação)**
```bash
# Testados e funcionando 100%
✅ GET /api/my-cooperations/
✅ GET /api/cooperation-stats/
✅ GET /api/meetings/1/cooperators/
✅ GET /api/meetings/1/cooperators/?status=pending
✅ POST /api/meetings/1/request-cooperation/
✅ Sistema de autenticação integrado
✅ Filtros por status funcionando
✅ Validações de permissões
```

### **Como executar testes**
```bash
# Executar testes automatizados
python manage.py test

# Testar via browsable API
python manage.py runserver
# Acesse: http://127.0.0.1:8000/api/

# Criar dados de teste
python manage.py shell
```

## 🌐 Interface de Testes

### **Django REST Framework Browsable API**
- Interface visual automática: `http://127.0.0.1:8000/api/`
- Formulários para testar POST/PUT
- Autenticação integrada
- Documentação automática

### **Django Admin**
- Interface administrativa: `http://127.0.0.1:8000/admin/`
- Gerenciamento completo de dados
- Filtros e buscas avançadas
- Estatísticas e relatórios

## 📈 Status do Desenvolvimento

- [x] ✅ Configuração inicial do projeto
- [x] ✅ Modelos de dados completos e testados
- [x] ✅ Sistema de autenticação funcional
- [x] ✅ API REST completa (28+ endpoints)
- [x] ✅ Sistema de cooperação implementado e testado
- [x] ✅ Admin panel customizado
- [x] ✅ Sistema de permissões avançado
- [x] ✅ Filtros e busca implementados
- [x] ✅ Validações e signals funcionando
- [ ] 🔄 Testes automatizados (unittest/pytest)
- [ ] 🔄 Documentação da API (Swagger/OpenAPI)
- [ ] 🔄 Sistema de notificações em tempo real
- [ ] 🔄 Upload de arquivos e imagens
- [ ] 🔄 Deploy em produção (Docker/AWS)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

### **Padrões de Commit**
- `✅ feat:` - Nova funcionalidade
- `🐛 fix:` - Correção de bug
- `📚 docs:` - Documentação
- `🧪 test:` - Testes
- `🔧 refactor:` - Refatoração

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👥 Autores

- **Ernane** - Desenvolvedor Principal - [@ernanegit](https://github.com/ernanegit)

## 📞 Contato

- **GitHub**: [@ernanegit](https://github.com/ernanegit)
- **Repository**: [tertulia-backend](https://github.com/ernanegit/tertulia-backend)
- **Issues**: [Reportar Problemas](https://github.com/ernanegit/tertulia-backend/issues)

## 🚀 Links Úteis

- **API Root**: `http://127.0.0.1:8000/api/`
- **Django Admin**: `http://127.0.0.1:8000/admin/`
- **Documentação Django**: [docs.djangoproject.com](https://docs.djangoproject.com/)
- **Django REST Framework**: [django-rest-framework.org](https://www.django-rest-framework.org/)

---

**Tertúlia Literária** - Conectando pessoas através da literatura 📚

*Sistema robusto de reuniões online com foco em eventos literários, cooperação entre usuários e gestão completa de participações.*