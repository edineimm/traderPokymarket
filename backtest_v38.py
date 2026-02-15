import ccxt
import pandas as pd
import numpy as np
from scipy.stats import norm
from colorama import Fore, Style, init

init(autoreset=True)

class SolanaADXSniperV38:
    def __init__(self):
        self.exchange = ccxt.binance()
        self.symbol = 'SOL/USDT'
        self.limit = 1440 
        self.trades = []
        self.df = None
        
    def baixar_dados(self):
        print(f"{Fore.CYAN}📥 Baixando dados SOL para V38 (Filtro ADX + Correção de Typo)...")
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe='1m', limit=self.limit)
        self.df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
        self.df['ts'] = pd.to_datetime(self.df['ts'], unit='ms')

    def calcular_indicadores(self): # Nome correto aqui
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

        # 5. ADX (Average Directional Index) - Medidor de Força
        plus_dm = df['h'].diff().clip(lower=0)
        minus_dm = df['l'].diff().clip(upper=0).abs()
        tr = df[['h', 'l', 'c']].diff().abs().max(axis=1)
        
        tr_smooth = tr.rolling(14).sum()
        plus_di = 100 * (plus_dm.rolling(14).sum() / tr_smooth)
        minus_di = 100 * (minus_dm.rolling(14).sum() / tr_smooth)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        df['adx'] = dx.rolling(14).mean()
        
        df.dropna(inplace=True)
        self.df = df.reset_index(drop=True)

    def executar_simulacao(self):
        print(f"{Fore.YELLOW}⚙️  Executando V38: Reversão + Pavio + ADX < 30...")
        
        i = 0
        while i < (len(self.df) - 16):
            row = self.df.iloc[i]
            future = self.df.iloc[i + 15]
            sinal = None
            
            # Filtros V36/V37
            vol_exaurido = row['v'] < row['vol_ma5']
            rejeicao_alta = row['upper_wick'] > (row['body'] * 0.7)
            rejeicao_baixa = row['lower_wick'] > (row['body'] * 0.7)
            
            # NOVO FILTRO V38: ADX (Tendência Fraca/Moderada)
            tendencia_calma = row['adx'] < 30

            # Lógica PUT (Venda no topo)
            if row['prob_tac'] > 0.60 and row['z_score'] > 1.5 and vol_exaurido and rejeicao_alta and tendencia_calma:
                sinal = "PUT"
            
            # Lógica CALL (Compra no fundo)
            elif row['prob_tac'] < 0.40 and row['z_score'] < -1.5 and vol_exaurido and rejeicao_baixa and tendencia_calma:
                sinal = "CALL"
            
            if sinal:
                ganhou = (future['c'] > row['c']) if sinal == "CALL" else (future['c'] < row['c'])
                diag = "Vitoria ADX" if ganhou else "Derrota ADX (Trend Surpresa)"
                
                self.trades.append({
                    'res': 'WIN' if ganhou else 'LOSS',
                    'motivo': diag
                })
                i += 15 
            else:
                i += 1

    def gerar_relatorio(self):
        total = len(self.trades)
        if total == 0:
            print(f"{Fore.RED}⚠️ Sem trades. O ADX barrou tudo ou as condições de pavio não bateram.")
            return

        wins = len([t for t in self.trades if t['res'] == 'WIN'])
        taxa = (wins / total) * 100
        
        print(f"\n{Fore.WHITE}{'='*40}")
        print(f"{Fore.MAGENTA}RELATÓRIO V38 - ADX SNIPER")
        print(f"{Fore.WHITE}{'='*40}")
        print(f"Total Trades: {total}")
        print(f"Taxa de Acerto: {Fore.GREEN if taxa > 65 else Fore.YELLOW}{taxa:.2f}%")
        
        W = taxa / 100
        kelly = (W - ((1 - W) / 0.85)) * 100
        print(f"💰 Kelly Criterion: {Fore.CYAN}{kelly:.2f}%")
        print(f"{Fore.WHITE}{'='*40}")

# Execução
bot = SolanaADXSniperV38()
bot.baixar_dados()
bot.calcular_indicadores() # Nome corrigido
bot.executar_simulacao()
bot.gerar_relatorio()