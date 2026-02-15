# Guia: Configurar Trading Bot com Docker no Linux

## 1. Pré-requisitos

### Instalar Docker no Linux (Ubuntu/Debian):
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Adicionar chave GPG do Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Adicionar repositório Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Verificar instalação
docker --version
docker compose version
```

### Adicionar usuário ao grupo docker (evitar usar sudo):
```bash
sudo usermod -aG docker $USER
newgrp docker
```

## 2. Preparar Projeto

### Clonar repositório:
```bash
cd ~
git clone https://github.com/edineimm/trader_pokymarket.git
cd trader_pokymarket
```

### Criar arquivos Docker necessários:

#### 1. Dockerfile (criar na raiz do projeto):
```dockerfile
FROM python:3.11-slim

LABEL maintainer="seu@email.com"
LABEL description="Trading Bot PokyMarket"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirimentes.txt requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY live_bot_v1.py .
COPY script_v4.py .
COPY historico_trades.csv .

RUN mkdir -p /app/logs

RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app
USER botuser

ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import os; os.path.exists('/app/live_bot_v1.py')" || exit 1

CMD ["python", "-u", "live_bot_v1.py"]
```

#### 2. docker-compose.yml (criar na raiz do projeto):
```yaml
version: '3.8'

services:
  trading-bot:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: trading-bot-pokymarket
    restart: unless-stopped
    
    environment:
      - TZ=America/Sao_Paulo
      - PYTHONUNBUFFERED=1
    
    env_file:
      - .env
    
    volumes:
      - ./historico_trades.csv:/app/historico_trades.csv
      - ./logs:/app/logs
    
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    
    networks:
      - bot-network

networks:
  bot-network:
    driver: bridge
```

#### 3. .dockerignore (otimizar build):
```
.git
.gitignore
*.md
__pycache__
*.pyc
.env
logs/
*.log
.vscode
.idea
```

#### 4. .env (configurar credenciais):
```bash
cp .env.example .env
nano .env
```

Conteúdo do .env:
```env
API_KEY=sua_api_key_aqui
API_SECRET=sua_api_secret_aqui
SYMBOL=BTCUSDT
TIMEFRAME=1h
CAPITAL=1000
MAX_RISK=0.02
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Criar diretório de logs:
```bash
mkdir -p logs
```

## 3. Build e Execução

### Validar se o Docker esta funcinoando
```bash
sudo systemctl start docker
```

### Caso não esteja
```bash
sudo docker compose build
sudo usermod -aG docker $USER
pip install --no-cache-dir -r requirements.txt
```

### Construir imagem Docker:
```bash
docker compose build
```

### Iniciar bot:
```bash
docker compose up -d
```

### Verificar status:
```bash
docker compose ps
```

## 4. Gerenciamento do Container

### Ver logs em tempo real:
```bash
docker compose logs -f
```

### Ver logs específicos:
```bash
docker compose logs -f trading-bot
docker compose logs --tail=100 trading-bot
```

### Parar bot:
```bash
docker compose down
```

### Reiniciar bot:
```bash
docker compose restart
```

### Parar e remover volumes:
```bash
docker compose down -v
```

### Entrar no container (debugging):
```bash
docker compose exec trading-bot bash
```

## 5. Atualizações

### Atualizar código e rebuildar:
```bash
cd ~/trader_pokymarket
git pull
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Rebuild forçado:
```bash
docker compose build --no-cache
docker compose up -d --force-recreate
```

## 6. Monitoramento

### Ver uso de recursos:
```bash
docker stats trading-bot-pokymarket
```

### Inspecionar container:
```bash
docker inspect trading-bot-pokymarket
```

### Healthcheck manual:
```bash
docker compose exec trading-bot python -c "print('Bot está rodando!')"
```

## 7. Backup Automatizado

### Script de backup:
```bash
nano ~/backup_docker.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=~/backups

mkdir -p $BACKUP_DIR

# Backup do histórico de trades
docker compose cp trading-bot:/app/historico_trades.csv $BACKUP_DIR/historico_trades_$DATE.csv

# Backup dos logs
docker compose cp trading-bot:/app/logs $BACKUP_DIR/logs_$DATE/

# Limpar backups antigos (> 30 dias)
find $BACKUP_DIR -name "historico_trades_*.csv" -mtime +30 -delete
find $BACKUP_DIR -type d -name "logs_*" -mtime +30 -exec rm -rf {} +

echo "Backup concluído: $DATE"
```

```bash
chmod +x ~/backup_docker.sh

# Agendar backup diário
crontab -e
# Adicionar:
0 0 * * * /home/ubuntu/backup_docker.sh >> /home/ubuntu/backup.log 2>&1
```

## 8. Docker em Produção - Configuração Avançada

### docker-compose.prod.yml (com múltiplas replicas):
```yaml
version: '3.8'

services:
  trading-bot:
    build:
      context: .
      dockerfile: Dockerfile
    deploy:
      replicas: 1
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '1'
          memory: 512M
    env_file:
      - .env.production
    volumes:
      - trades-data:/app/data
      - logs:/app/logs
    networks:
      - bot-network

volumes:
  trades-data:
  logs:

networks:
  bot-network:
    driver: bridge
```

### Executar com arquivo de produção:
```bash
docker compose -f docker-compose.prod.yml up -d
```

## 9. Monitoramento com Watchtower (Auto-Update)

### Adicionar ao docker-compose.yml:
```yaml
services:
  # ... serviço trading-bot ...

  watchtower:
    image: containrrr/watchtower
    container_name: watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - WATCHTOWER_POLL_INTERVAL=3600
      - WATCHTOWER_CLEANUP=true
    restart: unless-stopped
```

## 10. Logs e Debugging

### Ver todos os logs:
```bash
docker compose logs
```

### Filtrar logs por tempo:
```bash
docker compose logs --since 30m
docker compose logs --since 2024-01-01T00:00:00
```

### Seguir logs de erro:
```bash
docker compose logs -f | grep -i error
```

### Salvar logs em arquivo:
```bash
docker compose logs > bot_logs_$(date +%Y%m%d).log
```

## 11. Troubleshooting

### Container não inicia:
```bash
# Ver logs de erro
docker compose logs

# Verificar configuração
docker compose config

# Tentar iniciar em modo interativo
docker compose run --rm trading-bot bash
```

### Problemas de permissão:
```bash
# Ajustar permissões dos volumes
sudo chown -R $USER:$USER logs/
sudo chown $USER:$USER historico_trades.csv
```

### Limpar sistema Docker:
```bash
# Remover containers parados
docker container prune

# Remover imagens não utilizadas
docker image prune -a

# Limpar tudo (cuidado!)
docker system prune -a --volumes
```

### Rebuildar do zero:
```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

## 12. Segurança

### Proteger .env:
```bash
chmod 600 .env
echo ".env" >> .gitignore
```

### Escanear vulnerabilidades:
```bash
docker scout quickview
docker scout cves
```

### Usar secrets (Docker Swarm):
```bash
echo "sua_api_key" | docker secret create api_key -
```

## 13. Performance

### Limitar recursos do container:
```bash
docker compose run --cpus=0.5 --memory=256m trading-bot
```

### Verificar uso de memória:
```bash
docker stats --no-stream
```

## Comandos Rápidos de Referência

```bash
# Iniciar
docker compose up -d

# Parar
docker compose down

# Reiniciar
docker compose restart

# Ver logs
docker compose logs -f

# Status
docker compose ps

# Rebuild
docker compose build --no-cache && docker compose up -d

# Entrar no container
docker compose exec trading-bot bash

# Ver recursos
docker stats

# Backup
docker compose cp trading-bot:/app/historico_trades.csv ./backup/
```

## 14. CI/CD com GitHub Actions (Opcional)

### .github/workflows/docker-build.yml:
```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [ main, master ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker compose build
    
    - name: Test
      run: docker compose run --rm trading-bot python -c "print('Test OK')"
```
