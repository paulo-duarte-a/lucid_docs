# LucidDocs 📚

Uma plataforma inteligente para processamento e consulta de documentos PDF com integração de modelos de linguagem.

# Documentação da API
https://apiluciddocs.pauloduarte.tec.br/docs

## Funcionalidades Principais ✨
- **Autenticação JWT** com registro de usuários
- Upload e processamento de documentos PDF
- Armazenamento vetorial com ChromaDB
- Consultas contextualizadas usando RAG (Retrieval-Augmented Generation)
- Integração com modelos Gemini da Google
- Armazenamento de metadados em MongoDB
- Sistema de logging unificado com track IDs

## Pré-requisitos 📦
- Python 3.11+
- Docker e Docker Compose
- Conta no Google AI Studio (para API Key do Gemini)

## Instalação 🛠️

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/lucid-docs.git
cd lucid-docs
```

2. Inicie os serviços com Docker Compose:
```bash
docker-compose up -d
```

## Configuração ⚙️

1. Crie um arquivo `.env` na raiz do projeto:
```ini
GEMINI_API_KEY="sua-chave-aqui"
MONGO_URI="mongodb://mongo:27017/lucid_docs"  # Usando nome do serviço do Docker
```

## Uso 🚀


## Arquivo Docker Compose 🐳
```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - ./src:/app/src
      - ./tests:/app/tests
      - ./.env:/app/.env
      - chroma_db:/app/chroma_db
    ports:
      - "8000:8000"
    env_file: ".env"
    environment:
      - PYTHONDONTWRITEBYTECODE=1
      - PYTHONUNBUFFERED=1
      - PYTHONPATH=/app/src
    command: uvicorn lucid_docs.main:create_app --host 0.0.0.0 --port 8000 --reload
    depends_on:
      - mongo

  mongo:
    image: mongo
    restart: always
    environment:
      MONGO_INITDB_DATABASE: lucid_docs
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
  chroma_db:

```

## Principais Endpoints 🌐

| Método | Endpoint          | Descrição                     |
|--------|-------------------|-------------------------------|
| POST   | /auth/token       | Obter token de acesso         |
| POST   | /auth/users/register | Registrar novo usuário     |
| POST   | /upload/pdf       | Upload de arquivo PDF         |
| POST   | /chat/            | Realizar consulta contextual  |
| GET    | /health           | Verificar status do serviço   |

## Estrutura do Projeto 📂
```
lucid_docs/
├── core/           # Configurações e utilitários centrais
├── models/         # Modelos de dados e schemas
├── routers/        # Endpoints da API
├── services/       # Lógica de negócios e integrações
├── utils/          # Utilitários auxiliares
├── dependencies.py # Injeção de dependências
└── main.py         # Ponto de entrada da aplicação
```

## Contribuição 🤝
1. Faça um fork do projeto
2. Crie sua branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m '[feat]: Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Licença 📄
