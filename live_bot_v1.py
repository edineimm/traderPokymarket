import ccxt
import pandas as pd
import numpy as np
from scipy.stats import norm
import time
import os
from datetime import datetime, timedelta
from colorama import Fore, Style, init

init(autoreset=True)

class EthSentinelV21:
    def __init__(self):
        self.exchange = ccxt.binance()
        self.symbol = 'ETH/USDT'
        self.file_log = "historico_trades.csv"
        self.active_trade = None # Controla se estamos posicionados
        
        # Cria CSV se não existir
        if not os.path.exists(self.file_log):
            with open(self.file_log, 'w') as f:
                f.write("Data,Tipo,Preco_Entrada,Prob_Tatico,Prob_Estrategico,Status\n")

    def obter_probabilidades_reais(self):
        try:
            # Precisamos de pelo menos 60 candles para o cálculo estratégico
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe='1m', limit=100)
            df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            
            # Cálculo de Hull (Log Returns)
            log_ret = np.log(df['c'] / df['c'].shift(1))
            
            # Horizonte Tático (30m)
            mu_30 = log_ret.rolling(window=30).mean().iloc[-1]
            sigma_30 = log_ret.rolling(window=30).std().iloc[-1]
            z_30 = (mu_30 * 15) / (sigma_30 * np.sqrt(15))
            prob_30 = norm.cdf(z_30)
            
            # Horizonte Estratégico (60m)
            mu_60 = log_ret.rolling(window=60).mean().iloc[-1]
            sigma_60 = log_ret.rolling(window=60).std().iloc[-1]
            z_60 = (mu_60 * 15) / (sigma_60 * np.sqrt(15))
            prob_60 = norm.cdf(z_60)
            
            preco_atual = df['c'].iloc[-1]
            
            return prob_30, prob_60, preco_atual
            
        except Exception as e:
            print(f"{Fore.RED}Erro na API/Cálculo: {e}")
            return None, None, None

    def gerenciar_trade_ativo(self, preco_atual):
        if self.active_trade:
            agora = datetime.now()
            tempo_restante = (self.active_trade['saida'] - agora).total_seconds()
            
            if tempo_restante <= 0:
                # Trade acabou
                resultado = "LOSS"
                lucro = -1.0
                
                if self.active_trade['tipo'] == "CALL":
                    if preco_atual > self.active_trade['preco']:
                        resultado = "WIN"
                        lucro = 0.85
                elif self.active_trade['tipo'] == "PUT":
                    if preco_atual < self.active_trade['preco']:
                        resultado = "WIN"
                        lucro = 0.85
                
                print(f"\n{Fore.MAGENTA}🏁 TRADE FINALIZADO: {resultado} (PnL: {lucro})")
                
                # Salva no log
                with open(self.file_log, 'a') as f:
                    d = self.active_trade['entrada'].strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"{d},{self.active_trade['tipo']},{self.active_trade['preco']},{self.active_trade['p30']:.2f},{self.active_trade['p60']:.2f},{resultado}\n")
                
                self.active_trade = None # Libera para novo trade
            else:
                # Status de espera
                mins = int(tempo_restante // 60)
                secs = int(tempo_restante % 60)
                print(f"\r🔒 Trade em andamento ({self.active_trade['tipo']})... Faltam {mins:02d}:{secs:02d}", end="")

    def executar(self):
        print(f"{Fore.YELLOW}🚀 ETH SENTINEL V21 INICIADO")
        print(f"Estratégia: Hull Tide Alignment (30m + 60m)")
        print(f"Alvo: Prob Tática > 60% e Estratégica > 50%")
        print("-" * 50)
        
        while True:
            try:
                # 1. Pega dados frescos
                p30, p60, preco = self.obter_probabilidades_reais()
                
                if p30 is not None:
                    # 2. Gerencia trade aberto (se houver)
                    if self.active_trade:
                        self.gerenciar_trade_ativo(preco)
                    
                    # 3. Procura nova entrada (se estiver livre)
                    else:
                        sinal = None
                        
                        # --- CÉREBRO V20 ---
                        # CALL: Tático Forte (>60%) + Estratégico Favorável (>50%)
                        if (p30 > 0.60) and (p60 > 0.50):
                            sinal = "CALL"
                            cor = Fore.GREEN
                        
                        # PUT: Tático Fraco (<40%) + Estratégico Favorável (<50%)
                        elif (p30 < 0.40) and (p60 < 0.50):
                            sinal = "PUT"
                            cor = Fore.RED
                        
                        # Dashboard em Tempo Real
                        print(f"\rETH: {preco:.2f} | Tático(30m): {p30:.1%}" + 
                              f" | Estratégico(60m): {p60:.1%} | Sinal: {sinal if sinal else 'NEUTRO'}", end="")
                        
                        # Disparo
                        if sinal:
                            print(f"\n{cor}⚡ SINAL CONFIRMADO: {sinal} @ {preco}")
                            print(f"   Motivo: Alinhamento Estatístico (30m={p30:.2f}, 60m={p60:.2f})")
                            
                            self.active_trade = {
                                'entrada': datetime.now(),
                                'saida': datetime.now() + timedelta(minutes=15),
                                'tipo': sinal,
                                'preco': preco,
                                'p30': p30,
                                'p60': p60
                            }
                
                # Aguarda 30s antes do próximo tick (reduz flood na API)
                time.sleep(30)
                
            except KeyboardInterrupt:
                print("\n🛑 Bot parado pelo usuário.")
                break
            except Exception as e:
                print(f"\nErro Crítico: {e}")
                time.sleep(10)

# Start
bot = EthSentinelV21()
bot.executar()