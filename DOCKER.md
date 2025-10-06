# Docker Setup para Projeto Next.js

## Arquivos criados:
- `Dockerfile` - Para produção
- `Dockerfile.dev` - Para desenvolvimento
- `docker-compose.yml` - Orquestração dos serviços
- `.dockerignore` - Otimização do build

## Como usar:

### 1. Build e execução em produção:
```bash
# Build da imagem
docker build -t tarefas-next .

# Executar container
docker run -p 3000:3000 tarefas-next
```

### 2. Usando docker-compose (produção):
```bash
# Build e execução
make start-build

# Ou diretamente
docker compose up -d --build
```

### 3. Desenvolvimento:
```bash
# Build e execução do ambiente de desenvolvimento
make dev-build

# Ou diretamente
docker compose --profile dev up -d --build

# Acessar shell do container de desenvolvimento
make dev-shell
```

### 4. Comandos úteis (Makefile):
```bash
# Produção
make start-build    # Build e execução
make start          # Apenas execução
make stop           # Parar e limpar
make restart        # Reiniciar
make logs           # Ver logs

# Desenvolvimento
make dev-build      # Build e execução do dev
make dev-start      # Apenas execução do dev
make dev-shell      # Acessar shell do container

# Limpeza
make clean          # Limpar tudo (volumes e imagens)
```

## Configurações importantes:

- **Porta**: A aplicação roda na porta 3000
- **Modo standalone**: Configurado no `next.config.ts` para otimizar o build
- **Multi-stage build**: Otimiza o tamanho da imagem final
- **Usuário não-root**: Segurança aprimorada
- **Hot reload**: Disponível no modo de desenvolvimento

## Estrutura dos serviços:

- `tarefas-app`: Serviço de produção (porta 3000)
- `tarefas-dev`: Serviço de desenvolvimento (porta 3001) - apenas quando usar profile dev

## Resolução do problema "no service selected":

O erro ocorria porque o docker-compose.yml só tinha serviços com profiles. Agora temos:
- Serviço de produção (`tarefas-app`) sem profile (executa por padrão)
- Serviço de desenvolvimento (`tarefas-dev`) com profile `dev`
