import ccxt
import pandas as pd
import numpy as np
import time
import json
import os
from datetime import datetime, timedelta
from colorama import Fore, Style, init

init(autoreset=True)

class LiveTraderBot:
    def __init__(self, symbol='BTC/USDT'):
        self.exchange = ccxt.binance()
        self.symbol = symbol
        self.active_trades = [] # Lista de trades em aberto
        self.file_log = "historico_trades.csv"
        
        # Cria o arquivo CSV se não existir
        if not os.path.exists(self.file_log):
            with open(self.file_log, 'w') as f:
                f.write("Data_Entrada,Tipo,Preco_Entrada,Preco_Saida,Resultado,Lucro_Simulado,Diagnostico\n")

    def obter_dados_mercado(self):
        """Busca dados frescos de M1 e H1"""
        try:
            # 1. H1 para Tendência Macro
            ohlcv_h1 = self.exchange.fetch_ohlcv(self.symbol, timeframe='1h', limit=50)
            df_h1 = pd.DataFrame(ohlcv_h1, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            ema_h1 = df_h1['c'].ewm(span=20, adjust=False).mean().iloc[-1]
            trend_h1 = "ALTA" if df_h1['c'].iloc[-1] > ema_h1 else "BAIXA"
            
            # 2. M1 para Gatilho Tático
            ohlcv_m1 = self.exchange.fetch_ohlcv(self.symbol, timeframe='1m', limit=100)
            df_m1 = pd.DataFrame(ohlcv_m1, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            
            return df_m1, trend_h1
        except Exception as e:
            print(f"{Fore.RED}Erro de conexão: {e}")
            return None, None

    def calcular_indicadores(self, df):
        # EMA
        df['ema_fast'] = df['c'].ewm(span=9, adjust=False).mean()
        df['ema_slow'] = df['c'].ewm(span=21, adjust=False).mean()
        
        # RSI
        delta = df['c'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # ADX
        df['h-l'] = df['h'] - df['l']
        df['h-yc'] = abs(df['h'] - df['c'].shift(1))
        df['l-yc'] = abs(df['l'] - df['c'].shift(1))
        df['tr'] = df[['h-l', 'h-yc', 'l-yc']].max(axis=1)
        df['up'] = df['h'] - df['h'].shift(1)
        df['down'] = df['l'].shift(1) - df['l']
        df['+dm'] = np.where((df['up'] > df['down']) & (df['up'] > 0), df['up'], 0)
        df['-dm'] = np.where((df['down'] > df['up']) & (df['down'] > 0), df['down'], 0)
        window = 14
        df['tr_s'] = df['tr'].ewm(alpha=1/window, adjust=False).mean()
        df['+dm_s'] = df['+dm'].ewm(alpha=1/window, adjust=False).mean()
        df['-dm_s'] = df['-dm'].ewm(alpha=1/window, adjust=False).mean()
        df['+di'] = 100 * (df['+dm_s'] / df['tr_s'])
        df['-di'] = 100 * (df['-dm_s'] / df['tr_s'])
        df['dx'] = 100 * abs(df['+di'] - df['-di']) / (df['+di'] + df['-di'])
        df['adx'] = df['dx'].ewm(alpha=1/window, adjust=False).mean()
        
        return df.iloc[-1] # Retorna apenas a última vela processada

    def verificar_saidas(self, preco_atual):
        """Verifica se algum trade aberto já venceu (passaram-se 15 mins)"""
        trades_finalizados = []
        agora = datetime.now()
        
        for trade in self.active_trades:
            hora_saida = trade['hora_entrada'] + timedelta(minutes=15)
            
            if agora >= hora_saida:
                # O Trade Venceu! Hora de auditar.
                resultado = "LOSS"
                lucro = -1.00 # Simula perda de $1
                diagnostico = "Volatilidade/Ruído"
                
                if trade['tipo'] == "CALL (UP)":
                    if preco_atual > trade['preco_entrada']:
                        resultado = "WIN"
                        lucro = 0.85 # Simula lucro de $0.85 (considerando taxas/spread)
                        diagnostico = "Sucesso na Tendência"
                
                elif trade['tipo'] == "PUT (DOWN)":
                    if preco_atual < trade['preco_entrada']:
                        resultado = "WIN"
                        lucro = 0.85
                        diagnostico = "Sucesso na Tendência"

                print(f"{Fore.MAGENTA}🏁 TRADE FINALIZADO: {trade['tipo']} | Res: {resultado} | PnL: ${lucro}")
                
                # Salva no CSV
                with open(self.file_log, 'a') as f:
                    data_str = trade['hora_entrada'].strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"{data_str},{trade['tipo']},{trade['preco_entrada']},{preco_atual},{resultado},{lucro},{diagnostico}\n")
                
                trades_finalizados.append(trade)

        # Remove trades finalizados da lista ativa
        for t in trades_finalizados:
            self.active_trades.remove(t)

    def executar_ciclo(self):
        print(f"{Fore.YELLOW}🚀 Bot Iniciado (Paper Trading Mode). Pressione Ctrl+C para parar.")
        print(f"Estratégia: Sniper V4 (ADX + H1 Trend)")
        print(f"Log: {self.file_log}\n")
        
        while True:
            try:
                df_m1, trend_h1 = self.obter_dados_mercado()
                
                if df_m1 is not None:
                    candle = self.calcular_indicadores(df_m1)
                    preco_atual = candle['c']
                    
                    # 1. Verifica saídas pendentes
                    self.verificar_saidas(preco_atual)
                    
                    # 2. Verifica novas entradas
                    sinal = None
                    
                    # Filtros V4
                    if candle['adx'] > 25:
                        ema_up = candle['ema_fast'] > candle['ema_slow']
                        ema_down = candle['ema_fast'] < candle['ema_slow']
                        
                        if ema_up and (candle['rsi'] < 70) and trend_h1 == "ALTA":
                            sinal = "CALL (UP)"
                        elif ema_down and (candle['rsi'] > 30) and trend_h1 == "BAIXA":
                            sinal = "PUT (DOWN)"
                    
                    # Execução Virtual
                    timestamp_atual = datetime.now()
                    
                    # Evita abrir trade duplicado no mesmo minuto
                    ultimo_trade_recente = False
                    if self.active_trades:
                        delta_last = timestamp_atual - self.active_trades[-1]['hora_entrada']
                        if delta_last.total_seconds() < 60:
                            ultimo_trade_recente = True

                    if sinal and not ultimo_trade_recente:
                        print(f"{Fore.GREEN}⚡ ENTRADA DETECTADA: {sinal}")
                        print(f"   Preço: {preco_atual} | ADX: {candle['adx']:.2f} | H1: {trend_h1}")
                        
                        novo_trade = {
                            'hora_entrada': timestamp_atual,
                            'tipo': sinal,
                            'preco_entrada': preco_atual
                        }
                        self.active_trades.append(novo_trade)
                    
                    # Status Heartbeat (para você saber que ele está vivo)
                    print(f"\r⏳ Monitorando... BTC: {preco_atual:.2f} | H1: {trend_h1} | ADX: {candle['adx']:.1f} | Trades Abertos: {len(self.active_trades)}", end="")
                
                # Aguarda 60 segundos antes do próximo ciclo
                time.sleep(60)
                
            except KeyboardInterrupt:
                print("\n🛑 Bot parado pelo usuário.")
                break
            except Exception as e:
                print(f"\n{Fore.RED}Erro no loop principal: {e}")
                time.sleep(10)

# Start
bot = LiveTraderBot()
bot.executar_ciclo()