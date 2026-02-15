import ccxt
import pandas as pd
import numpy as np
from colorama import Fore, Style, init

init(autoreset=True)

class BacktestPolymarketV11_StandardReversion:
    def __init__(self, symbol='BTC/USDT', limit=1440):
        self.exchange = ccxt.binance()
        self.symbol = symbol
        self.limit = limit
        self.df_m1 = None
        self.trades = []
        
    def buscar_dados(self):
        print(f"{Fore.CYAN}📥 Baixando dados V11 (Mean Reversion - StdDev 2.0)...")
        ohlcv_m1 = self.exchange.fetch_ohlcv(self.symbol, timeframe='1m', limit=self.limit)
        self.df_m1 = pd.DataFrame(ohlcv_m1, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        self.df_m1['timestamp'] = pd.to_datetime(self.df_m1['timestamp'], unit='ms')

    def calcular_indicadores(self):
        df = self.df_m1
        
        # 1. Bandas de Bollinger (Padrão: 20, 2.0)
        df['ma_20'] = df['close'].rolling(window=20).mean()
        df['std_20'] = df['close'].rolling(window=20).std()
        
        # Ajuste: 2.0 Desvios (Mais permissivo que a V10)
        df['bb_upper'] = df['ma_20'] + (df['std_20'] * 2.0)
        df['bb_lower'] = df['ma_20'] - (df['std_20'] * 2.0)

        # 2. ADX (Filtro de Lateralidade)
        df['tr'] = df[['high', 'low', 'close']].diff().abs().max(axis=1)
        df['dx'] = 100 * abs(df['high'].diff() - df['low'].diff()) / df['tr']
        df['adx'] = df['dx'].ewm(span=14).mean()
        
        df.dropna(inplace=True)
        self.df_m1 = df.reset_index(drop=True)

    def executar_simulacao(self):
        print(f"{Fore.YELLOW}⚙️  Rodando V11 (Aposta: Tocou na banda 2.0 e ADX baixo -> Vai voltar)...\n")
        
        i = 0
        while i < (len(self.df_m1) - 16):
            candle = self.df_m1.iloc[i]
            candle_futuro = self.df_m1.iloc[i + 15]
            
            sinal = None
            
            # FILTRO: Mercado Calmo (ADX < 30)
            # Se o ADX estiver alto, o toque na banda pode virar tendência (não queremos isso)
            if candle['adx'] < 30:
                
                # Preço FURANDO a Banda Superior? -> VENDE (PUT)
                if candle['close'] > candle['bb_upper']:
                    sinal = "PUT (DOWN)"

                # Preço FURANDO a Banda Inferior? -> COMPRA (CALL)
                elif candle['close'] < candle['bb_lower']:
                    sinal = "CALL (UP)"

            # EXECUÇÃO
            if sinal:
                ganhou = False
                diff = candle_futuro['close'] - candle['close']
                
                if sinal == "CALL (UP)": ganhou = diff > 0
                else: ganhou = diff < 0 # PUT
                
                resultado = "WIN" if ganhou else "LOSS"
                
                # Diagnóstico V11
                diag = ""
                if resultado == "WIN":
                    diag = "Mean Reversion: Respeitou a banda"
                else:
                    # Se perdeu, foi porque "surfou a banda"?
                    if abs(diff) > (candle['close'] * 0.001):
                        diag = "Band Riding: Rompeu a banda e foi embora (Tendência nasceu)"
                    else:
                        diag = "Deriva: Ficou sambando fora da banda"

                self.trades.append({
                    'Timestamp': candle['timestamp'],
                    'Tipo': sinal,
                    'Resultado': resultado,
                    'Diagnostico': diag
                })
                i += 15 # Cooldown de 15 min
            else:
                i += 1

    def gerar_relatorio(self):
        total = len(self.trades)
        if total == 0:
            print("Nenhum trade. O mercado está comprimido demais (dentro das bandas).")
            return

        wins = len([t for t in self.trades if t['Resultado'] == 'WIN'])
        taxa = (wins / total) * 100
        
        print(f"{Fore.WHITE}{'='*40}")
        print(f"{Fore.CYAN}RESUMO BACKTEST V11 (Mean Reversion Standard)")
        print(f"{Fore.WHITE}{'='*40}")
        print(f"Total Trades: {total}") 
        print(f"Taxa de Acerto: {Fore.GREEN if taxa > 55 else Fore.RED}{taxa:.2f}%{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}🔍 ANÁLISE DE MOTIVOS:")
        causas = {}
        for t in self.trades:
            d = t['Diagnostico']
            if d not in causas: causas[d] = 0
            causas[d] += 1
        for d, q in causas.items():
            print(f"- {d}: {q}x ({q/total*100:.1f}%)")

# Execução
bot = BacktestPolymarketV11_StandardReversion()
bot.buscar_dados()
bot.calcular_indicadores()
bot.executar_simulacao()
bot.gerar_relatorio()