# Use Python 3.11 slim como base
FROM python:3.11-slim

# Informações do mantenedor
LABEL maintainer="seu@email.com"
LABEL description="Trading Bot PokyMarket"

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivo de requirements
# COPY requirimentes.txt requirements.txt ./

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código do bot
COPY live_bot_v1.py .
COPY script_v4.py .
COPY historico_trades.csv .

# Criar diretório para logs
RUN mkdir -p /app/logs

# Criar usuário não-root para segurança
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app
USER botuser

# Variáveis de ambiente (serão sobrescritas pelo .env)
ENV PYTHONUNBUFFERED=1

# Healthcheck para monitoramento
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import os; os.path.exists('/app/live_bot_v1.py')" || exit 1

# Comando para executar o bot
CMD ["python", "-u", "live_bot_v1.py"]
