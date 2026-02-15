import ccxt
import pandas as pd
import numpy as np
from scipy.stats import norm
from colorama import Fore, Style, init

init(autoreset=True)

class SolanaExhaustionV36:
    def __init__(self):
        self.exchange = ccxt.binance()
        self.symbol = 'SOL/USDT'
        self.limit = 1440 
        self.trades = []
        self.df = None
        
    def baixar_dados(self):
        print(f"{Fore.CYAN}📥 Baixando dados SOL para V36 (Filtro de Exaustão de Volume)...")
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe='1m', limit=self.limit)
        self.df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
        self.df['ts'] = pd.to_datetime(self.df['ts'], unit='ms')

    def calcular_indicadores(self):
        df = self.df
        log_ret = np.log(df['c'] / df['c'].shift(1))
        T = 15
        
        # 1. MOTOR HULL PROBABILITY
        df['sig30'] = log_ret.rolling(30).std()
        df['mu30'] = log_ret.rolling(30).mean()
        df['prob_tac'] = norm.cdf((df['mu30'] * T) / (df['sig30'] * np.sqrt(T)))
        
        # 2. Z-SCORE DE PREÇO (Mola)
        df['ma20'] = df['c'].rolling(20).mean()
        df['std20'] = df['c'].rolling(20).std()
        df['z_score'] = (df['c'] - df['ma20']) / df['std20']
        
        # 3. FILTRO DE VOLUME (Combustível)
        df['vol_ma5'] = df['v'].rolling(5).mean()
        
        df.dropna(inplace=True)
        self.df = df.reset_index(drop=True)

    def executar_simulacao(self):
        print(f"{Fore.YELLOW}⚙️  Executando V36: Operando Reversão APENAS com Volume em queda...")
        
        i = 0
        while i < (len(self.df) - 16):
            row = self.df.iloc[i]
            future = self.df.iloc[i + 15]
            sinal = None
            
            # --- CONDIÇÃO DE EXAUSTÃO V36 ---
            # Volume atual menor que a média curta (indicando que a força do movimento acabou)
            vol_exaurido = row['v'] < row['vol_ma5']
            
            # Se Hull indica ALTA, Z-Score CARO (> 1.5) e Volume CAINDO
            if row['prob_tac'] > 0.60 and row['z_score'] > 1.5 and vol_exaurido:
                sinal = "PUT"
            
            # Se Hull indica BAIXA, Z-Score BARATO (< -1.5) e Volume CAINDO
            elif row['prob_tac'] < 0.40 and row['z_score'] < -1.5 and vol_exaurido:
                sinal = "CALL"
            
            if sinal:
                ganhou = (future['c'] > row['c']) if sinal == "CALL" else (future['c'] < row['c'])
                self.trades.append({
                    'res': 'WIN' if ganhou else 'LOSS',
                    'motivo': 'Exaustão Confirmada' if ganhou else 'Falso Cansaço (Rompimento)'
                })
                i += 15 
            else:
                i += 1

    def gerar_relatorio(self):
        total = len(self.trades)
        if total == 0:
            print(f"{Fore.RED}⚠️ Sem trades. O volume não caiu nos picos de Z-Score.")
            return

        wins = len([t for t in self.trades if t['res'] == 'WIN'])
        taxa = (wins / total) * 100
        
        print(f"\n{Fore.WHITE}{'='*40}")
        print(f"{Fore.MAGENTA}RELATÓRIO V36 - SOLANA EXHAUSTION SNIPER")
        print(f"{Fore.WHITE}{'='*40}")
        print(f"Total Trades: {total}")
        print(f"Taxa de Acerto: {Fore.GREEN if taxa > 60 else Fore.YELLOW}{taxa:.2f}%")
        
        W = taxa / 100
        R = 0.85
        kelly = (W - ((1 - W) / R)) * 100
        
        if kelly > 0:
            print(f"💰 Kelly Criterion: {Fore.GREEN}{kelly:.2f}% (ALPHA DETECTADO)")
        else:
            print(f"💰 Kelly Criterion: {Fore.RED}{kelly:.2f}% (AGUARDAR MELHOR REGIME)")

        print(f"\n{Fore.YELLOW}🔍 ANÁLISE DE MOTIVOS:")
        analise = {}
        for t in self.trades:
            analise[t['motivo']] = analise.get(t['motivo'], 0) + 1
        for m, q in analise.items():
            print(f"- {m}: {q}x")
        print(f"{Fore.WHITE}{'='*40}")

# Execução
bot = SolanaExhaustionV36()
bot.baixar_dados()
bot.calcular_indicadores()
bot.executar_simulacao()
bot.gerar_relatorio()