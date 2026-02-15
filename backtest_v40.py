import ccxt
import pandas as pd
import numpy as np
from scipy.stats import norm
from colorama import Fore, Style, init

init(autoreset=True)

class SolanaBandwidthV40:
    def __init__(self):
        self.exchange = ccxt.binance()
        self.symbol = 'SOL/USDT'
        self.limit = 1440 
        self.trades = []
        self.df = None
        
    def baixar_dados(self):
        print(f"{Fore.CYAN}📥 Baixando dados SOL para V40 (Bollinger Bandwidth + Z-Score 2.0)...")
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe='1m', limit=self.limit)
        self.df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
        self.df['ts'] = pd.to_datetime(self.df['ts'], unit='ms')

    def calcular_indicadores(self):
        df = self.df
        log_ret = np.log(df['c'] / df['c'].shift(1))
        T = 15
        
        # 1. HULL PROBABILITY (Inversa)
        df['sig30'] = log_ret.rolling(30).std()
        df['mu30'] = log_ret.rolling(30).mean()
        df['prob_tac'] = norm.cdf((df['mu30'] * T) / (df['sig30'] * np.sqrt(T)))
        
        # 2. BOLLINGER BANDS & Z-SCORE (Mola)
        df['ma20'] = df['c'].rolling(20).mean()
        df['std20'] = df['c'].rolling(20).std()
        df['upper'] = df['ma20'] + (2 * df['std20'])
        df['lower'] = df['ma20'] - (2 * df['std20'])
        df['z_score'] = (df['c'] - df['ma20']) / df['std20']
        
        # 3. BANDWIDTH (Largura das Bandas)
        df['bandwidth'] = (df['upper'] - df['lower']) / df['ma20']
        df['bw_ma20'] = df['bandwidth'].rolling(20).mean()
        
        # 4. MÉTRICAS DE PAVIO & VOLUME
        df['body'] = abs(df['c'] - df['o'])
        df['upper_wick'] = df['h'] - df[['o', 'c']].max(axis=1)
        df['lower_wick'] = df[['o', 'c']].min(axis=1) - df['l']
        df['vol_ma5'] = df['v'].rolling(5).mean()

        # 5. ADX (Trend Strength)
        plus_dm = df['h'].diff().clip(lower=0)
        minus_dm = df['l'].diff().clip(upper=0).abs()
        tr = df[['h', 'l', 'c']].diff().abs().max(axis=1)
        tr_smooth = tr.rolling(14).sum()
        plus_di = 100 * (plus_dm.rolling(14).sum() / tr_smooth)
        minus_di = 100 * (minus_dm.rolling(14).sum() / tr_smooth)
        df['adx'] = (100 * abs(plus_di - minus_di) / (plus_di + minus_di)).rolling(14).mean()
        
        df.dropna(inplace=True)
        self.df = df.reset_index(drop=True)

    def executar_simulacao(self):
        print(f"{Fore.YELLOW}⚙️  Executando V40: Z-Score 2.0 + Bandwidth Expansion...")
        
        i = 0
        while i < (len(self.df) - 16):
            row = self.df.iloc[i]
            future = self.df.iloc[i + 15]
            sinal = None
            
            # FILTROS DE PRECISÃO
            # Agora exigimos Z-Score 2.0 (Extremo)
            # E exigimos que as bandas estejam mais abertas que a média (Sem Squeeze)
            vol_exaurido = row['v'] < row['vol_ma5']
            tendencia_calma = row['adx'] < 30
            bandas_abertas = row['bandwidth'] > row['bw_ma20']
            
            # Lógica PUT
            if row['z_score'] > 2.0 and row['prob_tac'] > 0.60 and bandas_abertas and vol_exaurido and tendencia_calma:
                if row['upper_wick'] > (row['body'] * 0.6):
                    sinal = "PUT"
            
            # Lógica CALL
            elif row['z_score'] < -2.0 and row['prob_tac'] < 0.40 and bandas_abertas and vol_exaurido and tendencia_calma:
                if row['lower_wick'] > (row['body'] * 0.6):
                    sinal = "CALL"
            
            if sinal:
                ganhou = (future['c'] > row['c']) if sinal == "CALL" else (future['c'] < row['c'])
                self.trades.append({'res': 'WIN' if ganhou else 'LOSS'})
                i += 15 
            else:
                i += 1

    def gerar_relatorio(self):
        total = len(self.trades)
        if total == 0:
            print(f"{Fore.RED}⚠️ Critérios muito rígidos. 0 trades.")
            return

        wins = len([t for t in self.trades if t['res'] == 'WIN'])
        taxa = (wins / total) * 100
        
        print(f"\n{Fore.WHITE}{'='*40}")
        print(f"{Fore.MAGENTA}RELATÓRIO V40 - BANDWIDTH SENTINEL")
        print(f"{Fore.WHITE}{'='*40}")
        print(f"Total Trades: {total}")
        print(f"Taxa de Acerto: {Fore.GREEN if taxa > 65 else Fore.YELLOW}{taxa:.2f}%")
        
        W = taxa / 100
        kelly = (W - ((1 - W) / 0.85)) * 100
        print(f"💰 Kelly Criterion: {Fore.CYAN}{kelly:.2f}%")
        print(f"{Fore.WHITE}{'='*40}")

# Execução
bot = SolanaBandwidthV40()
bot.baixar_dados()
bot.calcular_indicadores()
bot.executar_simulacao()
bot.gerar_relatorio()