# 📊 Trader PokyMarket - Crypto 15m Predictor

Este repositório contém o motor de trading automatizado para o mercado de **15-Minute Crypto Odds & Predictions**. O bot utiliza análise de dados em tempo real para executar ordens baseadas em probabilidades de curto prazo.

O núcleo da estratégia está implementado no arquivo principal: `script_v4.py`.

## 🎯 Objetivo do Projeto
O bot foi desenhado especificamente para:
* Monitorar variações de preço em janelas de 15 minutos.
* Calcular probabilidades (*odds*) para movimentos de criptoativos.
* Executar entradas e saídas automatizadas no PokyMarket.

## 🛠️ Stack Tecnológica
* **Engine:** Python 3.11 (Otimizado com imagem `slim`)
* **Infraestrutura:** Docker & Docker Compose para isolamento de ambiente.
* **Frequência:** Análise de candles e predições a cada 15 minutos.

## 🚀 Como Começar

### 1. Preparação
Certifique-se de que o Docker está rodando em sua máquina. Clone o repositório:
```bash
git clone [https://github.com/edineimm/trader_pokymarket.git](https://github.com/edineimm/trader_pokymarket.git)
cd trader_pokymarket
```

### 2. Docker
1. Criar ou Atualizar a Imagem
Sempre que você alterar o `script_v4.py` ou o `requirements.txt`, você precisa reconstruir a imagem:

```bash
docker compose build
```

### 3. Iniciar o Bot e Monitorar
Para subir o bot em segundo plano e começar a ver as predições de 15 minutos imediatamente:

```bash
# Inicia em segundo plano
docker compose up -d

# Monitora a execução (logs em tempo real)
docker compose logs -f --tail 100
```

### 4. Parar a Execução
Para desligar o bot com segurança:

```bash
docker compose down
```

### 5. Limpeza de Sistema (Manutenção)
O Docker acumula cache, imagens antigas e containers parados que ocupam muito espaço em disco. Use este comando para fazer uma "faxina":
Limpeza Geral: Remove containers parados, redes não utilizadas e imagens suspensas.

```bash
docker system prune
```
