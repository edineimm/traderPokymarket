#!/bin/bash

# Script de Instalação Rápida - Trading Bot PokyMarket
# Suporta EC2 e configuração Docker

set -e

echo "=========================================="
echo "Trading Bot PokyMarket - Instalação Rápida"
echo "=========================================="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para imprimir mensagens
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERRO]${NC} $1"
}

# Detectar sistema operacional
print_info "Detectando sistema operacional..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    print_info "Sistema detectado: $OS"
else
    print_error "Não foi possível detectar o sistema operacional"
    exit 1
fi

# Verificar se está rodando em EC2
print_info "Verificando ambiente..."
if curl -s -m 2 http://169.254.169.254/latest/meta-data/ > /dev/null 2>&1; then
    print_info "Ambiente EC2 detectado"
    IS_EC2=true
else
    print_info "Ambiente local detectado"
    IS_EC2=false
fi

# Menu de opções
echo ""
echo "Escolha o tipo de instalação:"
echo "1) EC2 com systemd (recomendado para produção)"
echo "2) Docker (portável e isolado)"
echo "3) Desenvolvimento local (venv)"
read -p "Opção [1-3]: " INSTALL_TYPE

case $INSTALL_TYPE in
    1)
        print_info "Instalando em modo EC2 com systemd..."
        
        # Atualizar sistema
        print_info "Atualizando sistema..."
        sudo apt update && sudo apt upgrade -y
        
        # Instalar dependências
        print_info "Instalando dependências..."
        sudo apt install -y python3 python3-pip python3-venv git
        
        # Clonar repositório
        print_info "Clonando repositório..."
        cd ~
        if [ -d "trader_pokymarket" ]; then
            print_warning "Diretório já existe. Atualizando..."
            cd trader_pokymarket
            git pull
        else
            git clone https://github.com/edineimm/trader_pokymarket.git
            cd trader_pokymarket
        fi
        
        # Criar ambiente virtual
        print_info "Criando ambiente virtual..."
        python3 -m venv venv
        source venv/bin/activate
        
        # Corrigir nome do arquivo requirements
        if [ -f requirimentes.txt ]; then
            mv requirimentes.txt requirements.txt
        fi
        
        # Instalar dependências Python
        print_info "Instalando dependências Python..."
        pip install -r requirements.txt
        
        # Criar arquivo .env
        if [ ! -f .env ]; then
            print_info "Criando arquivo .env..."
            cat > .env << EOF
# API Keys da Exchange
API_KEY=sua_api_key_aqui
API_SECRET=sua_api_secret_aqui

# Configurações do Bot
SYMBOL=BTCUSDT
TIMEFRAME=1h
CAPITAL=1000
MAX_RISK=0.02
ENVIRONMENT=production
LOG_LEVEL=INFO
EOF
            print_warning "Configure suas credenciais em: ~/trader_pokymarket/.env"
        fi
        
        # Criar diretório de logs
        mkdir -p logs
        
        # Criar serviço systemd
        print_info "Criando serviço systemd..."
        sudo tee /etc/systemd/system/trading-bot.service > /dev/null << EOF
[Unit]
Description=Trading Bot PokyMarket
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/trader_pokymarket
Environment="PATH=$HOME/trader_pokymarket/venv/bin"
ExecStart=$HOME/trader_pokymarket/venv/bin/python3 $HOME/trader_pokymarket/live_bot_v1.py
Restart=always
RestartSec=10
StandardOutput=append:$HOME/trader_pokymarket/logs/bot.log
StandardError=append:$HOME/trader_pokymarket/logs/bot_error.log

[Install]
WantedBy=multi-user.target
EOF
        
        # Habilitar e iniciar serviço
        sudo systemctl daemon-reload
        sudo systemctl enable trading-bot.service
        
        print_info "Instalação concluída!"
        echo ""
        print_warning "PRÓXIMOS PASSOS:"
        echo "1. Configure suas credenciais: nano ~/trader_pokymarket/.env"
        echo "2. Inicie o bot: sudo systemctl start trading-bot"
        echo "3. Verifique status: sudo systemctl status trading-bot"
        echo "4. Ver logs: sudo journalctl -u trading-bot -f"
        ;;
        
    2)
        print_info "Instalando com Docker..."
        
        # Verificar se Docker está instalado
        if ! command -v docker &> /dev/null; then
            print_info "Docker não encontrado. Instalando..."
            
            # Instalar Docker
            sudo apt update
            sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            sudo apt update
            sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            
            # Adicionar usuário ao grupo docker
            sudo usermod -aG docker $USER
            print_warning "Você precisa fazer logout e login novamente para usar Docker sem sudo"
        fi
        
        # Clonar repositório
        print_info "Clonando repositório..."
        cd ~
        if [ -d "trader_pokymarket" ]; then
            print_warning "Diretório já existe. Atualizando..."
            cd trader_pokymarket
            git pull
        else
            git clone https://github.com/edineimm/trader_pokymarket.git
            cd trader_pokymarket
        fi
        
        # Criar Dockerfile
        print_info "Criando Dockerfile..."
        cat > Dockerfile << 'EOF'
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
EOF
        
        # Criar docker-compose.yml
        print_info "Criando docker-compose.yml..."
        cat > docker-compose.yml << 'EOF'
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
EOF
        
        # Criar .dockerignore
        cat > .dockerignore << 'EOF'
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
EOF
        
        # Criar arquivo .env
        if [ ! -f .env ]; then
            print_info "Criando arquivo .env..."
            cat > .env << EOF
API_KEY=sua_api_key_aqui
API_SECRET=sua_api_secret_aqui
SYMBOL=BTCUSDT
TIMEFRAME=1h
CAPITAL=1000
MAX_RISK=0.02
ENVIRONMENT=production
LOG_LEVEL=INFO
EOF
            print_warning "Configure suas credenciais em: ~/trader_pokymarket/.env"
        fi
        
        # Criar diretório de logs
        mkdir -p logs
        
        print_info "Instalação concluída!"
        echo ""
        print_warning "PRÓXIMOS PASSOS:"
        echo "1. Configure suas credenciais: nano ~/trader_pokymarket/.env"
        echo "2. Build da imagem: docker compose build"
        echo "3. Inicie o bot: docker compose up -d"
        echo "4. Ver logs: docker compose logs -f"
        echo "5. Status: docker compose ps"
        ;;
        
    3)
        print_info "Instalando em modo desenvolvimento..."
        
        # Instalar dependências
        print_info "Instalando dependências..."
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv git
        
        # Clonar repositório
        print_info "Clonando repositório..."
        cd ~
        if [ -d "trader_pokymarket" ]; then
            print_warning "Diretório já existe. Atualizando..."
            cd trader_pokymarket
            git pull
        else
            git clone https://github.com/edineimm/trader_pokymarket.git
            cd trader_pokymarket
        fi
        
        # Criar ambiente virtual
        print_info "Criando ambiente virtual..."
        python3 -m venv venv
        source venv/bin/activate
        
        # Corrigir nome do arquivo requirements
        if [ -f requirimentes.txt ]; then
            mv requirimentes.txt requirements.txt
        fi
        
        # Instalar dependências Python
        print_info "Instalando dependências Python..."
        pip install -r requirements.txt
        
        # Criar arquivo .env
        if [ ! -f .env ]; then
            print_info "Criando arquivo .env..."
            cat > .env << EOF
API_KEY=sua_api_key_aqui
API_SECRET=sua_api_secret_aqui
SYMBOL=BTCUSDT
TIMEFRAME=1h
CAPITAL=1000
MAX_RISK=0.02
ENVIRONMENT=development
LOG_LEVEL=DEBUG
EOF
            print_warning "Configure suas credenciais em: ~/trader_pokymarket/.env"
        fi
        
        # Criar diretório de logs
        mkdir -p logs
        
        print_info "Instalação concluída!"
        echo ""
        print_warning "PRÓXIMOS PASSOS:"
        echo "1. Configure suas credenciais: nano ~/trader_pokymarket/.env"
        echo "2. Ative o ambiente virtual: source ~/trader_pokymarket/venv/bin/activate"
        echo "3. Execute o bot: python live_bot_v1.py"
        ;;
        
    *)
        print_error "Opção inválida"
        exit 1
        ;;
esac

echo ""
print_info "=========================================="
print_info "Instalação finalizada!"
print_info "=========================================="
