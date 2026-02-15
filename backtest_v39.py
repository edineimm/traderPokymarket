import ccxt
import pandas as pd
import numpy as np
from scipy.stats import norm
from colorama import Fore, Style, init

init(autoreset=True)

class SolanaRSISniperV39:
    def __init__(self):
        self.exchange = ccxt.binance()
        self.symbol = 'SOL/USDT'
        self.limit = 1440 
        self.trades = []
        self.df = None
        
    def baixar_dados(self):
        print(f"{Fore.CYAN}📥 Baixando dados SOL para V39 (RSI + ADX + Pavio)...")
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe='1m', limit=self.limit)
        self.df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
        self.df['ts'] = pd.to_datetime(self.df['ts'], unit='ms')

    def calcular_indicadores(self):
        df = self.df
        log_ret = np.log(df['c'] / df['c'].shift(1))
        T = 15
        
        # 1. MOTOR HULL (Referência Inversa)
        df['sig30'] = log_ret.rolling(30).std()
        df['mu30'] = log_ret.rolling(30).mean()
        df['prob_tac'] = norm.cdf((df['mu30'] * T) / (df['sig30'] * np.sqrt(T)))
        
        # 2. Z-SCORE (Mola)
        df['ma20'] = df['c'].rolling(20).mean()
        df['std20'] = df['c'].rolling(20).std()
        df['z_score'] = (df['c'] - df['ma20']) / df['std20']
        
        # 3. VOLUME (Exaustão)
        df['vol_ma5'] = df['v'].rolling(5).mean()
        
        # 4. MÉTRICAS DE PAVIO
        df['body'] = abs(df['c'] - df['o'])
        df['upper_wick'] = df['h'] - df[['o', 'c']].max(axis=1)
        df['lower_wick'] = df[['o', 'c']].min(axis=1) - df['l']

        # 5. ADX (Trend Strength)
        plus_dm = df['h'].diff().clip(lower=0)
        minus_dm = df['l'].diff().clip(upper=0).abs()
        tr = df[['h', 'l', 'c']].diff().abs().max(axis=1)
        tr_smooth = tr.rolling(14).sum()
        plus_di = 100 * (plus_dm.rolling(14).sum() / tr_smooth)
        minus_di = 100 * (minus_dm.rolling(14).sum() / tr_smooth)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        df['adx'] = dx.rolling(14).mean()

        # 6. RSI (Relative Strength Index) - Período 7 (Rápido)
        delta = df['c'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=7).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=7).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        df.dropna(inplace=True)
        self.df = df.reset_index(drop=True)

    def executar_simulacao(self):
        print(f"{Fore.YELLOW}⚙️  Executando V39: Reversão + RSI Extremes + ADX < 30...")
        
        i = 0
        while i < (len(self.df) - 16):
            row = self.df.iloc[i]
            future = self.df.iloc[i + 15]
            sinal = None
            
            # Filtros de Precisão
            vol_exaurido = row['v'] < row['vol_ma5']
            rejeicao_alta = row['upper_wick'] > (row['body'] * 0.6) # Levemente relaxado
            rejeicao_baixa = row['lower_wick'] > (row['body'] * 0.6)
            tendencia_calma = row['adx'] < 30
            
            # NOVO FILTRO V39: RSI Extremes
            sobrecomprado = row['rsi'] > 70
            sobrevendido = row['rsi'] < 30

            # Lógica PUT
            if row['prob_tac'] > 0.60 and row['z_score'] > 1.5 and vol_exaurido and rejeicao_alta and tendencia_calma and sobrecomprado:
                sinal = "PUT"
            
            # Lógica CALL
            elif row['prob_tac'] < 0.40 and row['z_score'] < -1.5 and vol_exaurido and rejeicao_baixa and tendencia_calma and sobrevendido:
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
            print(f"{Fore.RED}⚠️ Filtros muito pesados. 0 trades.")
            return

        wins = len([t for t in self.trades if t['res'] == 'WIN'])
        taxa = (wins / total) * 100
        
        print(f"\n{Fore.WHITE}{'='*40}")
        print(f"{Fore.MAGENTA}RELATÓRIO V39 - RSI INTEGRATED SNIPER")
        print(f"{Fore.WHITE}{'='*40}")
        print(f"Total Trades: {total}")
        print(f"Taxa de Acerto: {Fore.GREEN if taxa >= 65 else Fore.YELLOW}{taxa:.2f}%")
        
        W = taxa / 100
        kelly = (W - ((1 - W) / 0.85)) * 100
        print(f"💰 Kelly Criterion: {Fore.CYAN}{kelly:.2f}%")
        print(f"{Fore.WHITE}{'='*40}")

# Execução
bot = SolanaRSISniperV39()
bot.baixar_dados()
bot.calcular_indicadores()
bot.executar_simulacao()
bot.gerar_relatorio()