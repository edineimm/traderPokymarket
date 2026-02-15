import ccxt
import pandas as pd
import numpy as np
from scipy.stats import norm
from colorama import Fore, Style, init

init(autoreset=True)

class EthHullTideV20:
    def __init__(self):
        self.exchange = ccxt.binance()
        self.symbol = 'ETH/USDT'
        self.limit = 1440 
        self.trades = []
        self.df = None
        
    def baixar_dados(self):
        print(f"{Fore.CYAN}📥 Baixando dados ETH para V20 (Alinhamento Tático 30m + Estratégico 60m)...")
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe='1m', limit=self.limit)
        self.df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
        self.df['ts'] = pd.to_datetime(self.df['ts'], unit='ms')

    def calcular_z_score(self, df, window, forecast_horizon=15):
        log_ret = np.log(df['c'] / df['c'].shift(1))
        mu = log_ret.rolling(window=window).mean()
        sigma = log_ret.rolling(window=window).std()
        
        # Z-Score de Hull
        z_score = (mu * forecast_horizon) / (sigma * np.sqrt(forecast_horizon))
        return z_score

    def calcular_metricas(self):
        df = self.df
        
        # Calculamos Apenas Tático (30m) e Estratégico (60m)
        # Ignoramos o ruído de 10m
        df['z_tactical']  = self.calcular_z_score(df, window=30)
        df['z_strategic'] = self.calcular_z_score(df, window=60)
        
        # Probabilidades
        df['prob_tac'] = norm.cdf(df['z_tactical'])
        df['prob_str'] = norm.cdf(df['z_strategic'])
        
        df.dropna(inplace=True)
        self.df = df.reset_index(drop=True)

    def executar_simulacao(self):
        print(f"{Fore.YELLOW}⚙️  Rodando V20 (Tático agressivo, mas respeitando a Maré 60m)...")
        
        i = 0
        while i < (len(self.df) - 16):
            row = self.df.iloc[i]
            candle_future = self.df.iloc[i + 15]
            
            sinal = None
            
            # LÓGICA DE ALINHAMENTO
            
            # CALL:
            # 1. Tático (30m) vê oportunidade clara (> 60%)
            # 2. Estratégico (60m) NÃO está contra (> 50%)
            if (row['prob_tac'] > 0.60) and (row['prob_str'] > 0.50):
                sinal = "CALL"
            
            # PUT:
            # 1. Tático (30m) vê queda clara (< 40%)
            # 2. Estratégico (60m) NÃO está contra (< 50%)
            elif (row['prob_tac'] < 0.40) and (row['prob_str'] < 0.50):
                sinal = "PUT"
            
            # EXECUÇÃO
            if sinal:
                ganhou = False
                diff = candle_future['c'] - row['c']
                
                if sinal == "CALL": ganhou = diff > 0
                else: ganhou = diff < 0
                
                resultado = "WIN" if ganhou else "LOSS"
                
                # Diagnóstico V20
                diag = ""
                if resultado == "WIN":
                    diag = "Full Alignment: 30m e 60m concordaram"
                else:
                    # Se perdeu com tudo alinhado, foi um evento de cauda (Cisne Negro)?
                    if (sinal == "CALL" and diff < -row['c']*0.002) or (sinal == "PUT" and diff > row['c']*0.002):
                        diag = "Evento de Cauda: Reversão violenta contra tendência macro"
                    else:
                        diag = "Ruído de Mercado: Drift natural falhou (Normal)"

                self.trades.append({
                    'Timestamp': row['ts'],
                    'Tipo': sinal,
                    'Prob_Tac': f"{row['prob_tac']:.2f}",
                    'Prob_Str': f"{row['prob_str']:.2f}",
                    'Resultado': resultado,
                    'Diagnostico': diag
                })
                
                i += 15 # Cooldown
            else:
                i += 1

    def gerar_relatorio(self):
        total = len(self.trades)
        if total == 0:
            print("Nenhum trade: Tático e Estratégico nunca se alinharam.")
            return

        wins = len([t for t in self.trades if t['Resultado'] == 'WIN'])
        taxa = (wins / total) * 100
        
        print(f"{Fore.WHITE}{'='*40}")
        print(f"{Fore.CYAN}RESUMO V20 (ETH HULL TIDE ALIGNMENT)")
        print(f"{Fore.WHITE}{'='*40}")
        print(f"Total Trades: {total}") 
        print(f"Taxa de Acerto: {Fore.GREEN if taxa > 60 else Fore.YELLOW if taxa > 55 else Fore.RED}{taxa:.2f}%{Style.RESET_ALL}")
        
        # Cálculo de Kelly (Gestão de Risco Profissional)
        # K% = W - (1-W)/R (Assumindo R=0.85 profit vs 1.0 loss no Polymarket)
        # Se taxa > 55%, Kelly será positivo
        R = 0.85 # Payoff ratio (Lucro / Risco)
        W = taxa / 100
        kelly = W - ((1 - W) / R)
        
        if kelly > 0:
            print(f"\n💰 Kelly Criterion: {Fore.GREEN}Apostar {kelly*100:.1f}% da banca por trade{Style.RESET_ALL}")
        else:
            print(f"\n💰 Kelly Criterion: {Fore.RED}NÃO OPERAR (Expectativa Negativa){Style.RESET_ALL}")

        print(f"\n{Fore.YELLOW}🔍 ANÁLISE DE MOTIVOS:")
        causas = {}
        for t in self.trades:
            d = t['Diagnostico']
            if d not in causas: causas[d] = 0
            causas[d] += 1
        for d, q in causas.items():
            print(f"- {d}: {q}x ({q/total*100:.1f}%)")

# Execução
bot = EthHullTideV20()
bot.baixar_dados()
bot.calcular_metricas()
bot.executar_simulacao()
bot.gerar_relatorio()