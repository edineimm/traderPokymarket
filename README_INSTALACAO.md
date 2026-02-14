# Trading Bot PokyMarket - Guia de Instalação

Este repositório contém guias completos para executar o bot de trading em diferentes ambientes.

## 📁 Arquivos Incluídos

1. **guia_ec2.md** - Guia completo para configurar o bot em uma instância EC2 da AWS
2. **guia_docker.md** - Guia completo para executar o bot com Docker
3. **Dockerfile** - Arquivo Docker pronto para uso
4. **docker-compose.yml** - Orquestração do container
5. **.env.example** - Template de variáveis de ambiente
6. **install.sh** - Script de instalação automatizada

## 🚀 Instalação Rápida

### Opção 1: Script Automático (Recomendado)

```bash
# Baixar e executar o script de instalação
wget https://raw.githubusercontent.com/edineimm/trader_pokymarket/master/install.sh
chmod +x install.sh
./install.sh
```

O script oferece três opções:
1. **EC2 com systemd** - Para produção em servidor
2. **Docker** - Portável e isolado
3. **Desenvolvimento local** - Para testes

### Opção 2: EC2 Manual

```bash
# 1. Conectar na EC2
ssh -i "sua-chave.pem" ubuntu@seu-ip-ec2

# 2. Atualizar sistema e instalar dependências
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git -y

# 3. Clonar repositório
git clone https://github.com/edineimm/trader_pokymarket.git
cd trader_pokymarket

# 4. Criar ambiente virtual e instalar dependências
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Configurar variáveis de ambiente
cp .env.example .env
nano .env  # Adicionar suas API keys

# 6. Criar serviço systemd
sudo cp configs/trading-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot

# 7. Verificar status
sudo systemctl status trading-bot
```

### Opção 3: Docker

```bash
# 1. Instalar Docker (se necessário)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 2. Clonar repositório
git clone https://github.com/edineimm/trader_pokymarket.git
cd trader_pokymarket

# 3. Configurar variáveis de ambiente
cp .env.example .env
nano .env  # Adicionar suas API keys

# 4. Build e executar
docker compose build
docker compose up -d

# 5. Ver logs
docker compose logs -f
```

## 📖 Guias Detalhados

- **[guia_ec2.md](guia_ec2.md)** - Instruções completas para EC2
  - Configuração do servidor
  - Systemd service
  - Monitoramento e logs
  - Backup automático
  - Troubleshooting

- **[guia_docker.md](guia_docker.md)** - Instruções completas para Docker
  - Instalação do Docker
  - Build de imagens
  - Docker Compose
  - Volumes e persistência
  - Monitoramento
  - CI/CD

## ⚙️ Configuração

### Variáveis de Ambiente (.env)

```env
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
```

### Estrutura de Arquivos

```
trader_pokymarket/
├── live_bot_v1.py           # Bot principal
├── script_v4.py             # Script auxiliar
├── requirements.txt         # Dependências Python
├── historico_trades.csv     # Histórico de operações
├── Dockerfile               # Configuração Docker
├── docker-compose.yml       # Orquestração Docker
├── .env                     # Variáveis de ambiente (não versionar!)
├── .env.example             # Template de .env
└── logs/                    # Diretório de logs
```

## 🔧 Comandos Úteis

### EC2 com systemd

```bash
# Iniciar bot
sudo systemctl start trading-bot

# Parar bot
sudo systemctl stop trading-bot

# Reiniciar bot
sudo systemctl restart trading-bot

# Ver status
sudo systemctl status trading-bot

# Ver logs
sudo journalctl -u trading-bot -f

# Atualizar código
cd ~/trader_pokymarket
git pull
sudo systemctl restart trading-bot
```

### Docker

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
```

## 📊 Monitoramento

### Logs do Bot

```bash
# EC2
tail -f ~/trader_pokymarket/logs/bot.log

# Docker
docker compose logs -f trading-bot
```

### Uso de Recursos

```bash
# EC2
htop
free -h

# Docker
docker stats trading-bot-pokymarket
```

## 🔐 Segurança

1. **NUNCA** commite o arquivo `.env` no Git
2. Configure permissões adequadas: `chmod 600 .env`
3. Use API keys com permissões mínimas necessárias
4. Configure firewall: `sudo ufw allow 22/tcp && sudo ufw enable`
5. Mantenha o sistema atualizado: `sudo apt update && sudo apt upgrade`

## 🐛 Troubleshooting

### Bot não inicia

```bash
# EC2
sudo journalctl -u trading-bot -n 50

# Docker
docker compose logs --tail=50
```

### Problemas de permissão

```bash
# EC2
ls -la ~/trader_pokymarket/live_bot_v1.py
chmod +x ~/trader_pokymarket/live_bot_v1.py

# Docker
sudo chown -R $USER:$USER logs/
```

### Conexão com API falha

```bash
# Testar conectividade
python3 -c "import ccxt; exchange = ccxt.binance(); print(exchange.fetch_ticker('BTC/USDT'))"
```

## 📦 Backup

### Backup Manual

```bash
# Copiar histórico de trades
cp ~/trader_pokymarket/historico_trades.csv ~/backups/

# Backup completo
tar -czf bot-backup-$(date +%Y%m%d).tar.gz ~/trader_pokymarket
```

### Backup Automático (Cron)

```bash
# Editar crontab
crontab -e

# Adicionar linha para backup diário às 00:00
0 0 * * * cp ~/trader_pokymarket/historico_trades.csv ~/backups/historico_$(date +\%Y\%m\%d).csv
```

## 📝 Requisitos do Sistema

### Mínimo
- CPU: 1 vCPU
- RAM: 512 MB
- Disco: 10 GB
- SO: Ubuntu 20.04+ / Debian 11+

### Recomendado
- CPU: 2 vCPU
- RAM: 1 GB
- Disco: 20 GB
- SO: Ubuntu 22.04 LTS

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique os guias detalhados (guia_ec2.md e guia_docker.md)
2. Consulte a seção de Troubleshooting
3. Abra uma issue no GitHub

## 📄 Licença

[Adicione sua licença aqui]

## ⚠️ Disclaimer

Este bot é fornecido "como está", sem garantias. Trading de criptomoedas envolve riscos significativos. Use por sua conta e risco.
