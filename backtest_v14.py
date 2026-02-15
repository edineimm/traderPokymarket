import ccxt
import pandas as pd
import numpy as np
from colorama import Fore, Style, init

init(autoreset=True)

class MarketScannerV14:
    def __init__(self):
        self.exchange = ccxt.binance()
        self.symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
        self.limit = 1000 # Últimos 1000 minutos
        
    def obter_dados(self, symbol):
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe='1m', limit=self.limit)
            df = pd.DataFrame(ohlcv, columns=['ts', 'o', 'h', 'l', 'c', 'v'])
            return df
        except:
            return None

    def analisar_ativo(self, symbol, df):
        # 1. Calcular ADX (Força da Tendência)
        df['tr'] = df[['h', 'l', 'c']].diff().abs().max(axis=1)
        df['dx'] = 100 * abs(df['h'].diff() - df['l'].diff()) / df['tr']
        df['adx'] = df['dx'].ewm(span=14).mean()
        
        # 2. Calcular Bandwidth (Largura das Bandas - Mede Volatilidade)
        df['ma'] = df['c'].rolling(20).mean()
        df['std'] = df['c'].rolling(20).std()
        df['upper'] = df['ma'] + (2 * df['std'])
        df['lower'] = df['ma'] - (2 * df['std'])
        df['bandwidth'] = ((df['upper'] - df['lower']) / df['ma']) * 100
        
        # 3. Calcular Estocástico (Para ver se está saturado)
        lowest_low = df['l'].rolling(14).min()
        highest_high = df['h'].rolling(14).max()
        df['k'] = 100 * ((df['c'] - lowest_low) / (highest_high - lowest_low))
        
        # Pega o último candle completo
        ultimo = df.iloc[-2] 
        
        return {
            'Symbol': symbol,
            'Preco': ultimo['c'],
            'ADX': ultimo['adx'],
            'Volatilidade_BB': ultimo['bandwidth'],
            'Stoch_K': ultimo['k']
        }

    def executar_scan(self):
        print(f"{Fore.YELLOW}📡 Iniciando Scanner Multi-Ativos (V14)...\n")
        print(f"{'ATIVO':<10} | {'ADX':<10} | {'VOLATIL(%)':<12} | {'REGIME DE MERCADO'}")
        print("-" * 60)
        
        melhor_ativo = None
        maior_volatilidade = -1
        
        for symbol in self.symbols:
            df = self.obter_dados(symbol)
            if df is not None:
                dados = self.analisar_ativo(symbol, df)
                
                # Classifica o Regime
                regime = ""
                cor = Fore.WHITE
                
                if dados['ADX'] > 25:
                    regime = "TENDÊNCIA (Vivo)"
                    cor = Fore.GREEN
                elif dados['Volatilidade_BB'] < 0.15: # Banda muito estreita
                    regime = "COMA (Morto)"
                    cor = Fore.RED
                else:
                    regime = "LATERAL (Ping-Pong)"
                    cor = Fore.CYAN
                
                print(f"{cor}{dados['Symbol']:<10} | {dados['ADX']:.2f}       | {dados['Volatilidade_BB']:.4f}%      | {regime}")
                
                # Lógica de Seleção: Queremos o ativo com maior ADX ou Volatilidade
                score = dados['ADX'] + (dados['Volatilidade_BB'] * 100)
                if score > maior_volatilidade:
                    maior_volatilidade = score
                    melhor_ativo = dados['Symbol']

        print("-" * 60)
        print(f"\n{Fore.MAGENTA}🏆 Melhor Oportunidade Agora: {melhor_ativo}")
        print(f"Recomendação: Rodar Backtest específico para este ativo.")

# Execução
scanner = MarketScannerV14()
scanner.executar_scan()