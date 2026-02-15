import ccxt
import pandas as pd
import numpy as np
import time
import os
from datetime import datetime, timedelta
from colorama import Fore, Style, init

init(autoreset=True)

class LiveTraderBotV5:
    def __init__(self, symbol='BTC/USDT'):
        self.exchange = ccxt.binance()
        self.symbol = symbol
        self.active_trades = [] 
        self.file_log = "historico_trades_v5.csv"
        
        # Cria arquivo se não existir
        if not os.path.exists(self.file_log):
            with open(self.file_log, 'w') as f:
                f.write("Data_Entrada,Tipo,Preco_Entrada,Preco_Saida,Resultado,Lucro_Simulado,Diagnostico\n")

    def obter_dados_mercado(self):
        try:
            # H1 (Tendência Macro)
            ohlcv_h1 = self.exchange.fetch_ohlcv(self.symbol, timeframe='1h', limit=50)
            df_h1 = pd.DataFrame(ohlcv_h1, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            ema_h1 = df_h1['c'].ewm(span=20, adjust=False).mean().iloc[-1]
            trend_h1 = "ALTA" if df_h1['c'].iloc[-1] > ema_h1 else "BAIXA"
            
            # M1 (Tático)
            ohlcv_m1 = self.exchange.fetch_ohlcv(self.symbol, timeframe='1m', limit=100)
            df_m1 = pd.DataFrame(ohlcv_m1, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            
            return df_m1, trend_h1
        except Exception as e:
            print(f"{Fore.RED}Erro API: {e}")
            return None, None

    def calcular_indicadores(self, df):
        # EMA
        df['ema_fast'] = df['c'].ewm(span=9, adjust=False).mean()
        df['ema_slow'] = df['c'].ewm(span=21, adjust=False).mean()
        
        # RSI
        delta = df['c'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        rs = gain.ewm(com=13, adjust=False).mean() / loss.ewm(com=13, adjust=False).mean()
        df['rsi'] = 100 - (100 / (1 + rs))

        # ADX Simples
        df['tr'] = df[['h', 'l', 'c']].diff().abs().max(axis=1) # Simplificação para performance
        df['dx'] = 100 * abs(df['h'].diff() - df['l'].diff()) / df['tr'] # DX Aproximado
        df['adx'] = df['dx'].ewm(span=14).mean() # ADX Suavizado
        
        return df.iloc[-1]

    def verificar_saidas(self, preco_atual):
        removidos = []
        agora = datetime.now()
        
        for trade in self.active_trades:
            # Checa se passou 15 min
            if agora >= trade['hora_saida_prevista']:
                resultado = "LOSS"
                lucro = -1.0
                
                if trade['tipo'] == "CALL (UP)":
                    if preco_atual > trade['preco_entrada']:
                        resultado = "WIN"
                        lucro = 0.85
                elif trade['tipo'] == "PUT (DOWN)":
                    if preco_atual < trade['preco_entrada']:
                        resultado = "WIN"
                        lucro = 0.85

                print(f"{Fore.MAGENTA}🏁 FINALIZADO: {trade['tipo']} | Res: {resultado} | PnL: {lucro}")
                
                with open(self.file_log, 'a') as f:
                    d_str = trade['hora_entrada'].strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"{d_str},{trade['tipo']},{trade['preco_entrada']},{preco_atual},{resultado},{lucro},Execucao_Unica\n")
                
                removidos.append(trade)
        
        for r in removidos:
            self.active_trades.remove(r)

    def executar_ciclo(self):
        print(f"{Fore.YELLOW}🛡️ Bot V5 Iniciado (Modo: Single Shot).")
        
        while True:
            try:
                df_m1, trend_h1 = self.obter_dados_mercado()
                
                if df_m1 is not None:
                    candle = self.calcular_indicadores(df_m1)
                    preco = candle['c']
                    
                    self.verificar_saidas(preco)
                    
                    # --- TRAVA DE SEGURANÇA V5 ---
                    # Se já existe 1 trade aberto, NÃO FAZ NADA.
                    if len(self.active_trades) > 0:
                        trade_atual = self.active_trades[0]
                        tempo_restante = (trade_atual['hora_saida_prevista'] - datetime.now()).seconds // 60
                        print(f"\r🔒 Trade em andamento ({tempo_restante}m rest). Aguardando conclusão...", end="")
                    
                    else:
                        # Só analisa entrada se estiver "Livre"
                        sinal = None
                        if candle['adx'] > 25:
                            ema_up = candle['ema_fast'] > candle['ema_slow']
                            ema_down = candle['ema_fast'] < candle['ema_slow']
                            
                            if ema_up and (candle['rsi'] < 70) and trend_h1 == "ALTA":
                                sinal = "CALL (UP)"
                            elif ema_down and (candle['rsi'] > 30) and trend_h1 == "BAIXA":
                                sinal = "PUT (DOWN)"
                        
                        if sinal:
                            print(f"\n{Fore.GREEN}⚡ NOVA ENTRADA: {sinal} @ {preco}")
                            self.active_trades.append({
                                'hora_entrada': datetime.now(),
                                'hora_saida_prevista': datetime.now() + timedelta(minutes=15),
                                'tipo': sinal,
                                'preco_entrada': preco
                            })
                        else:
                            print(f"\r⏳ Monitorando... BTC: {preco:.2f} | H1: {trend_h1} | ADX: {candle['adx']:.1f}", end="")
                
                time.sleep(30) # Check a cada 30s
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Erro: {e}")
                time.sleep(10)

bot = LiveTraderBotV5()
bot.executar_ciclo()