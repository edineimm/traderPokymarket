# Guia: Configurar Trading Bot na EC2

## 1. Preparar Instância EC2

### Criar e Conectar na EC2:
```bash
# Conectar via SSH
ssh -i "sua-chave.pem" ubuntu@seu-ip-ec2.compute.amazonaws.com
```

### Atualizar Sistema:
```bash
sudo apt update && sudo apt upgrade -y
```

### Instalar Python e Dependências:
```bash
sudo apt install python3 python3-pip python3-venv git -y
```

## 2. Clonar e Configurar Projeto

### Clonar Repositório:
```bash
cd ~
git clone https://github.com/edineimm/trader_pokymarket.git
cd trader_pokymarket
```

### Criar Ambiente Virtual:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Instalar Dependências:
```bash
# Corrigir nome do arquivo (se necessário)
if [ -f requirimentes.txt ]; then
    mv requirimentes.txt requirements.txt
fi

pip install -r requirements.txt
```

## 3. Configurar Variáveis de Ambiente

### Criar arquivo .env:
```bash
nano .env
```

### Adicionar suas credenciais:
```env
# API Keys da Exchange
API_KEY=sua_api_key_aqui
API_SECRET=sua_api_secret_aqui

# Configurações do Bot
SYMBOL=BTCUSDT
TIMEFRAME=1h
CAPITAL=1000
```

## 4. Testar Bot Manualmente

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar bot
python3 live_bot_v1.py
```

## 5. Configurar para Execução Contínua

### Opção A: Usando systemd (Recomendado)

#### Criar serviço:
```bash
sudo nano /etc/systemd/system/trading-bot.service
```

#### Conteúdo do arquivo:
```ini
[Unit]
Description=Trading Bot PokyMarket
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/trader_pokymarket
Environment="PATH=/home/ubuntu/trader_pokymarket/venv/bin"
ExecStart=/home/ubuntu/trader_pokymarket/venv/bin/python3 /home/ubuntu/trader_pokymarket/live_bot_v1.py
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/trader_pokymarket/logs/bot.log
StandardError=append:/home/ubuntu/trader_pokymarket/logs/bot_error.log

[Install]
WantedBy=multi-user.target
```

#### Criar diretório de logs:
```bash
mkdir -p ~/trader_pokymarket/logs
```

#### Habilitar e iniciar serviço:
```bash
sudo systemctl daemon-reload
sudo systemctl enable trading-bot.service
sudo systemctl start trading-bot.service
```

#### Comandos úteis:
```bash
# Ver status
sudo systemctl status trading-bot

# Ver logs em tempo real
sudo journalctl -u trading-bot -f

# Parar bot
sudo systemctl stop trading-bot

# Reiniciar bot
sudo systemctl restart trading-bot
```

### Opção B: Usando screen (Alternativa simples)

```bash
# Instalar screen
sudo apt install screen -y

# Criar sessão
screen -S trading-bot

# Executar bot
cd ~/trader_pokymarket
source venv/bin/activate
python3 live_bot_v1.py

# Desanexar: Ctrl+A depois D
# Reanexar: screen -r trading-bot
```

## 6. Monitoramento e Logs

### Ver logs do bot:
```bash
# Com systemd
tail -f ~/trader_pokymarket/logs/bot.log

# Com screen
screen -r trading-bot
```

### Configurar alertas por email (opcional):
```bash
sudo apt install mailutils -y
```

### Script de monitoramento:
```bash
nano ~/check_bot.sh
```

```bash
#!/bin/bash
if ! systemctl is-active --quiet trading-bot; then
    echo "Bot parado! Reiniciando..." | mail -s "Trading Bot Alert" seu@email.com
    sudo systemctl start trading-bot
fi
```

```bash
chmod +x ~/check_bot.sh

# Adicionar ao crontab (executar a cada 5 minutos)
crontab -e
# Adicionar linha:
*/5 * * * * /home/ubuntu/check_bot.sh
```

## 7. Segurança

### Configurar firewall:
```bash
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
```

### Proteger arquivo .env:
```bash
chmod 600 .env
```

### Backup automático:
```bash
nano ~/backup_trades.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp ~/trader_pokymarket/historico_trades.csv ~/backups/historico_trades_$DATE.csv
# Manter apenas últimos 30 dias
find ~/backups -name "historico_trades_*.csv" -mtime +30 -delete
```

```bash
mkdir -p ~/backups
chmod +x ~/backup_trades.sh

# Adicionar ao crontab (backup diário às 00:00)
crontab -e
# Adicionar linha:
0 0 * * * /home/ubuntu/backup_trades.sh
```

## 8. Atualização do Bot

```bash
cd ~/trader_pokymarket
sudo systemctl stop trading-bot
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl start trading-bot
```

## 9. Troubleshooting

### Bot não inicia:
```bash
# Verificar logs
sudo journalctl -u trading-bot -n 50

# Verificar permissões
ls -la ~/trader_pokymarket/live_bot_v1.py

# Testar manualmente
cd ~/trader_pokymarket
source venv/bin/activate
python3 live_bot_v1.py
```

### Problemas de memória:
```bash
# Verificar uso de recursos
htop
free -h

# Se necessário, adicionar swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Verificar conectividade com API:
```bash
# Testar conexão
python3 -c "import ccxt; print(ccxt.exchanges)"
```

## 10. Otimizações

### Reduzir custos EC2:
- Use instâncias t3.micro ou t4g.micro (elegível para free tier)
- Configure auto-stop quando mercado fechado (se aplicável)

### Melhorar performance:
```bash
# Instalar bibliotecas otimizadas
pip install numpy --upgrade --no-cache-dir
pip install pandas --upgrade --no-cache-dir
```

## Comandos Rápidos de Referência

```bash
# Status do bot
sudo systemctl status trading-bot

# Reiniciar bot
sudo systemctl restart trading-bot

# Ver logs em tempo real
sudo journalctl -u trading-bot -f

# Parar bot
sudo systemctl stop trading-bot

# Atualizar código
cd ~/trader_pokymarket && git pull && sudo systemctl restart trading-bot
```
