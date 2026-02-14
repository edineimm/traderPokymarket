import ccxt
import pandas as pd
import numpy as np
from colorama import Fore, Style, init

init(autoreset=True)


class BacktestPolymarketV4:
    def __init__(self, symbol='BTC/USDT', limit=1440):
        self.exchange = ccxt.binance()
        self.symbol = symbol
        self.limit = limit
        self.df_m1 = None
        self.trend_h1 = "NEUTRO"  # Vamos definir a tendência macro
        self.trades = []

    def buscar_dados(self):
        print(f"{Fore.CYAN}📥 Baixando dados M1 (Tático) e H1 (Estratégico)...")

        # 1. Dados de 1 Minuto (O Campo de Batalha)
        ohlcv_m1 = self.exchange.fetch_ohlcv(
            self.symbol, timeframe='1m', limit=self.limit)
        self.df_m1 = pd.DataFrame(
            ohlcv_m1, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        self.df_m1['timestamp'] = pd.to_datetime(
            self.df_m1['timestamp'], unit='ms')

        # 2. Dados de 1 Hora (A Maré) - Pegamos os últimos 48h para garantir
        ohlcv_h1 = self.exchange.fetch_ohlcv(
            self.symbol, timeframe='1h', limit=48)
        df_h1 = pd.DataFrame(ohlcv_h1, columns=[
                             'timestamp', 'open', 'high', 'low', 'close', 'volume'])

        # Define a tendência MACRO baseada na última vela fechada de H1
        # Se Preço > EMA20 no H1 = Tendência de Alta
        ema_h1 = df_h1['close'].ewm(span=20, adjust=False).mean().iloc[-1]
        price_h1 = df_h1['close'].iloc[-1]

        if price_h1 > ema_h1:
            self.trend_h1 = "ALTA"
        else:
            self.trend_h1 = "BAIXA"

        print(f"{Fore.MAGENTA}🌊 Tendência Macro (H1) Identificada: {self.trend_h1}")
        print(f"{Fore.GREEN}✔ Dados carregados!\n")

    def calcular_indicadores(self):
        # Cálculos no M1 (igual ao V3)
        df = self.df_m1

        # EMA
        df['ema_fast'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=21, adjust=False).mean()

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        avg_gain = gain.ewm(com=13, adjust=False).mean()
        avg_loss = loss.ewm(com=13, adjust=False).mean()
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # ADX (Filtro V3)
        df['h-l'] = df['high'] - df['low']
        df['h-yc'] = abs(df['high'] - df['close'].shift(1))
        df['l-yc'] = abs(df['low'] - df['close'].shift(1))
        df['tr'] = df[['h-l', 'h-yc', 'l-yc']].max(axis=1)
        df['up'] = df['high'] - df['high'].shift(1)
        df['down'] = df['low'].shift(1) - df['low']
        df['+dm'] = np.where((df['up'] > df['down']) &
                             (df['up'] > 0), df['up'], 0)
        df['-dm'] = np.where((df['down'] > df['up']) &
                             (df['down'] > 0), df['down'], 0)
        window = 14
        df['tr_s'] = df['tr'].ewm(alpha=1/window, adjust=False).mean()
        df['+dm_s'] = df['+dm'].ewm(alpha=1/window, adjust=False).mean()
        df['-dm_s'] = df['-dm'].ewm(alpha=1/window, adjust=False).mean()
        df['+di'] = 100 * (df['+dm_s'] / df['tr_s'])
        df['-di'] = 100 * (df['-dm_s'] / df['tr_s'])
        df['dx'] = 100 * abs(df['+di'] - df['-di']) / (df['+di'] + df['-di'])
        df['adx'] = df['dx'].ewm(alpha=1/window, adjust=False).mean()

        df.dropna(inplace=True)

    def executar_simulacao(self):
        print(
            f"{Fore.YELLOW}⚙️  Rodando simulação V4 (Filtro ADX + Filtro H1 Macro)...\n")

        for i in range(len(self.df_m1) - 16):
            candle = self.df_m1.iloc[i]
            candle_futuro = self.df_m1.iloc[i + 15]

            sinal = None

            # --- FILTRO 1: ADX (Força) ---
            if candle['adx'] > 25:

                # --- FILTRO 2: EMA Cruzada (Gatilho) ---
                ema_up = candle['ema_fast'] > candle['ema_slow']
                ema_down = candle['ema_fast'] < candle['ema_slow']

                # --- FILTRO 3: A REGRA DA MARÉ (H1) ---
                # Só compra se Macro for ALTA. Só vende se Macro for BAIXA.

                # Lógica de CALL
                if ema_up and (candle['rsi'] < 70):
                    if self.trend_h1 == "ALTA":  # CONFLUÊNCIA!
                        if candle['close'] > candle['open']:
                            sinal = "CALL (UP)"

                # Lógica de PUT
                elif ema_down and (candle['rsi'] > 30):
                    if self.trend_h1 == "BAIXA":  # CONFLUÊNCIA!
                        if candle['close'] < candle['open']:
                            sinal = "PUT (DOWN)"

            if sinal:
                # Checa resultado
                if sinal == "CALL (UP)":
                    ganhou = candle_futuro['close'] > candle['close']
                else:
                    ganhou = candle_futuro['close'] < candle['close']

                resultado = "WIN" if ganhou else "LOSS"

                # Diagnóstico V4
                diagnostico = "Setup Perfeito (M1 + H1)"
                if not ganhou:
                    # Se perdemos mesmo a favor da tendência macro, o que houve?
                    diff = candle_futuro['close'] - candle['close']
                    if abs(diff) < (candle['close'] * 0.0002):
                        diagnostico = "Lateralização Súbita"
                    else:
                        diagnostico = "Volatilidade/Ruído de Notícia (H1 falhou)"

                self.trades.append(
                    {'Resultado': resultado, 'Diagnostico': diagnostico})

    def gerar_relatorio(self):
        total = len(self.trades)
        if total == 0:
            print(
                f"Nenhum trade alinhado com a tendência macro ({self.trend_h1}).")
            return

        wins = len([t for t in self.trades if t['Resultado'] == 'WIN'])
        taxa = (wins / total) * 100

        print(f"{Fore.WHITE}{'='*40}")
        print(f"{Fore.CYAN}RESUMO V4 (Sniper Mode - M1 + H1)")
        print(f"{Fore.WHITE}{'='*40}")
        print(f"Total Trades: {total}")
        print(
            f"Taxa de Acerto: {Fore.GREEN if taxa > 60 else Fore.YELLOW if taxa > 55 else Fore.RED}{taxa:.2f}%{Style.RESET_ALL}")

        print(f"\n{Fore.YELLOW}🔍 ANÁLISE FINAL DE ERROS:")
        erros = [t for t in self.trades if t['Resultado'] == 'LOSS']
        causas = {}
        for erro in erros:
            causas[erro['Diagnostico']] = causas.get(
                erro['Diagnostico'], 0) + 1
        for c, q in causas.items():
            print(f"- {c}: {q}x")


# Execução
bot = BacktestPolymarketV4()
bot.buscar_dados()
bot.calcular_indicadores()
bot.executar_simulacao()
bot.gerar_relatorio()
