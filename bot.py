import config
from pprint import pprint
from binance.spot import Spot
import time
import pandas as pd
import numpy as np
import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from mplfinance.original_flavor import candlestick_ohlc

class BotBinance:
    __api_key = config.api_key
    __api_secret = config.api_secret
    
    
    def __init__(self, symbol: str, interval: str, limit: int):
        self.symbol = symbol.upper()
        self.interval = interval
        self.limit = limit
        self._client = Spot(self.__api_key, self.__api_secret)
        
    def _request(self, endpoint: str, parameters: dict = None):
        try:
            response= getattr(self._client, endpoint)
            return response() if parameters is None else response(**parameters)
        except Exception as e:  # Manejar otros errores de forma diferente
            print(f'Error inesperado: {e}')
            raise e  # Propagar la excepción para que la maneje la función llamadora
    def symbol_price(self, pair: str = None):
        symbol = self.symbol if pair is None else pair
        return float(self._request("ticker_price", {"symbol": symbol.upper()}).get('price'))
    def addcandle(self, candles):
        data = self._request(endpoint="klines", parameters={
                             "symbol": self.symbol, "interval": self.interval, "limit": self.limit})
        v = data[0]
        candle = {'Open_time': int(v[0]), 'Open_price': float(v[1]), 'High_price': float(
            v[2]), 'Low_price': float(v[3]), 'Close_price': float(v[4]), "Volume": float(v[5])}
        candles.append(candle)
        candles.pop(0)
        #print(len(candles))
        return candles


    def candlestick(self):
        candles = self._request(endpoint="klines", parameters={
                                "symbol": self.symbol, "interval": self.interval, "limit": self.limit})
        return list(map(lambda v: {'Open_time': int(v[0]), 'Open_price': float(v[1]), 'High_price': float(v[2]), 'Low_price': float(v[3]), 'Close_price': float(v[4]), "Volume": float(v[5])}, candles))

    def create_dataframe(self, candles):
        df = pd.DataFrame({
            'Datetime': [datetime.datetime.fromtimestamp(candle['Open_time'] / 1000) for candle in candles],
            'Open': [candle['Open_price'] for candle in candles],
            'High': [candle['High_price'] for candle in candles],
            'Low': [candle['Low_price'] for candle in candles],
            'Close': [candle['Close_price'] for candle in candles],
            'Volume': [candle['Volume'] for candle in candles],
        })
        df.set_index('Datetime', inplace=True)
        return df
    
    def new_order(self, side: str,  type: str, quantity: float = 0, price: float = 0, stopPrice: float = 0, mode: int = 1):
        timestamp = int(time.time()*1000)
        params={}    
        if type =="MARKET":
            params = {
                "symbol": self.symbol,
                "type": type,
                "side": side, #sell or buy
                "quantity": f"{quantity:.{5}f}",
                "timestamp": timestamp 
            }
        elif type== "LIMIT":
            #print("limit")
            params = {
                "symbol": self.symbol,
                "side": side, #sell or buy
                "type": type,
                "quantity": f"{quantity:.{5}f}",
                "price": round(price,2),
                "timeInForce": "GTC",
                "timestamp": timestamp, 
            }
        elif type in ("STOP_LOSS_LIMIT", "TAKE_PROFIT_LIMIT"):    
            params = {
                "symbol": self.symbol,
                "side": side, #sell or buy
                "type": type,
                "quantity": f"{quantity:.{5}f}",
                "price": round(price,2),
                "stopPrice":round(stopPrice,2),
                "timeInForce": "GTC",
                "timestamp": timestamp, 
            }
            if mode==1:
                return  self._request(endpoint="new_order", parameters=params)
            else:
                return  self._request(endpoint="new_order_test", parameters=params)
    def get_open_orders(self):
        return  self._request(endpoint="get_open_orders", parameters={"symbol": self.symbol})    
    def cancel_orderId(self, orderId: int):
        return  self._request(endpoint="cancel_order", parameters={"symbol": self.symbol, "orderId": orderId})
    def get_orderId(self, orderId: int):
        return  self._request(endpoint="get_order", parameters={"symbol": self.symbol, "orderId": orderId})
    def cancel_open_orders(self):
          params ={
              "symbol": self.symbol
          }
          return  self._request(endpoint="cancel_open_orders", parameters=params)
          
    def distanceBand(self, price, band):
        return abs(price - band)
    def confirm_band(self, price_market, upperband, middleband, lowerband ):
        distanceUpper = self.distanceBand(price=price_market, band=upperband.iloc[-1])
        distanceLower = self.distanceBand(price=price_market, band=lowerband.iloc[-1])  
        distanceMiddle= self.distanceBand(price=price_market, band=middleband.iloc[-1])  
        if distanceLower < distanceMiddle:
            return "up"
        
        elif distanceUpper < distanceMiddle:
            return "down"
       
    def confirm_mfi(self, mfi: float = 0):
        if (mfi.iloc[-1] < 20):    
            return "up"
        elif(mfi.iloc[-1] > 80): 
            return "down"
        
    def confirm_divergences(self, data_values, close_prices):
        # Inicializar listas de divergencias
        bullish_divergences = []
        bearish_divergences = []

        # Detectar divergencias alcistas y bajistas
        for i in range(1, len(data_values)):
            # Detectar divergencia alcista
            if close_prices.iloc[i] < close_prices.iloc[i - 1] and data_values.iloc[i] > data_values.iloc[i - 1]:
                # Almacenar divergencia potencial
                potential_bullish_div = (i, data_values.iloc[i], close_prices.iloc[i])

                # Evaluar la divergencia potencial
                is_valid = True
                for j in range(i + 1, len(data_values)):
                    if not (close_prices.iloc[j] < close_prices.iloc[j - 1] and data_values.iloc[j] > data_values.iloc[j - 1]):
                        is_valid = False
                        break

                # Agregar divergencia válida
                if is_valid:
                    bullish_divergences.append(potential_bullish_div)

            # Detectar divergencia bajista
            if close_prices.iloc[i] > close_prices.iloc[i - 1] and data_values.iloc[i] < data_values.iloc[i - 1]:
                # Almacenar divergencia potencial
                potential_bearish_div = (i, data_values.iloc[i], close_prices.iloc[i])

                # Evaluar la divergencia potencial
                is_valid = True
                for j in range(i + 1, len(data_values)):
                    if not (close_prices.iloc[j] > close_prices.iloc[j - 1] and data_values.iloc[j] < data_values.iloc[j - 1]):
                        is_valid = False
                        break

                # Agregar divergencia válida
                if is_valid:
                    bearish_divergences.append(potential_bearish_div)

        return {
            "up_divergences": bullish_divergences,
            "down_divergences": bearish_divergences
        }

                
    
    def confirm_signal_macd(self, macd, signal, closes):
        divergences = self.confirm_divergences(data_values=macd, close_prices=closes)
        if len(divergences.get("up_divergences")) == 0 and len(divergences.get("down_divergences")) == 0:
            if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] < signal.iloc[-2]:
                return "up"  # Cruce alcista
            elif macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-2] > signal.iloc[-2]:
                return "down"  # Cruce bajista
        else:
            up_divergences = divergences.get("up_divergences")
            if up_divergences is not None and len(up_divergences) > 0:
                if len(up_divergences[-1]) > 0:
                    return "up_div"

            down_divergences = divergences.get("down_divergences")
            if down_divergences is not None and len(down_divergences) > 0:
                if len(down_divergences[-1]) > 0:
                    return "up_div"
            
    def confirm_signal_rsi(self, rsi, closes):
        divergences = self.confirm_divergences(data_values=rsi, close_prices=closes)
        if len(divergences.get("up_divergences")) == 0 and len(divergences.get("down_divergences")) == 0:
            if   rsi.iloc[-1] > 70:
                return "down" 
        
            if rsi.iloc[-1] < 30:
                return "up"           
        else:
            up_divergences = divergences.get("up_divergences")
            if up_divergences is not None and len(up_divergences) > 0:
                if len(up_divergences[-1]) > 0:
                    return "up_div"

            down_divergences = divergences.get("down_divergences")
            if down_divergences is not None and len(down_divergences) > 0:
                if len(down_divergences[-1]) > 0:
                    return "up_div"
    
    def SMA(self, closes, timeperiod:float = 20):
        sma = []
        for i in range(len(closes)):
            if i < timeperiod - 1:
                sma.append(None)  # No hay suficientes datos para calcular la SMA
            else:
                sma.append(sum(closes[i-timeperiod+1:i+1]) / timeperiod)
        return sma
    
    def confirm_double_crossover(self, sma_min, sma_medium, sma_max): 
        if self.confirm_single_crossover(sma_min, sma_medium) == self.confirm_single_crossover(sma_medium, sma_max):
            return self.confirm_single_crossover(sma_medium, sma_max)
    
    def confirm_single_crossover(self, sma_min, sma_max):
        if sma_min[-1] > sma_max[-1] and sma_min[-2] < sma_max[-2]:
            return "up"
        if sma_min[-1] < sma_max[-1] and sma_min[-2] > sma_max[-2]:
            return "down"
    
    def confirm_signal_sma(self, smaS, smaM, smaL):      
        if self.confirm_double_crossover(sma_min= smaS, sma_medium=smaM, sma_max= smaM):
            return self.confirm_double_crossover(sma_min= smaS, sma_medium=smaM, sma_max= smaM)
        else:
            if self.confirm_single_crossover(sma_min= smaS, sma_max= smaM):
                return self.confirm_single_crossover(sma_min= smaS, sma_max= smaM)
            elif self.confirm_single_crossover(sma_min = smaS, sma_max= smaL):
                return self.confirm_single_crossover(sma_min = smaS, sma_max= smaL)
            elif self.confirm_single_crossover(sma_min= smaM, sma_max= smaL):
                return self.confirm_single_crossover(sma_min= smaM, sma_max= smaL)

    
    def series(self, closes):
        return pd.Series(closes)
    
    def RSI(self, closes, timeperiod:float = 20):
        delta = closes.diff(1)
        # Separar las ganancias y pérdidas
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        # Calcular la media de ganancias y pérdidas
        avg_gain = gains.rolling(window=timeperiod, min_periods=1).mean()
        avg_loss = losses.rolling(window=timeperiod, min_periods=1).mean()
        # Calcular la fuerza relativa (RS)
        rs = avg_gain / avg_loss
        # Calcular el RSI
        return 100 - (100 / (1 + rs))

    def calculate_ema(self, series, timeperiod:float = 20):
        
        return series.ewm(span=timeperiod, adjust=False).mean()
    
    def MACD(self, closes, fastperiod:float = 12, slowperiod:float = 26, signalperiod:float = 9):
        # Calcular las EMAs rápidas y lentas
        ema_fast = self.calculate_ema(closes, fastperiod)
        ema_slow = self.calculate_ema(closes, slowperiod)
   
        # Calcular la línea MACD
        macd = ema_fast - ema_slow
    
        # Calcular la línea de señal
        macdsignal = self.calculate_ema(macd, signalperiod)
    
        # Calcular el histograma
        macdhist = macd - macdsignal
        
        return macd, macdsignal, macdhist
    
    def BBANDS(self, closes, timeperiod:float = 20, nbdevup: float = 2, nbdevdn: float = 2):
        rolling_mean = closes.rolling(window=timeperiod).mean()
        rolling_std = closes.rolling(window=timeperiod).std()
        middleband = rolling_mean
        upperband = rolling_mean + (rolling_std * nbdevup)
        lowerband = rolling_mean - (rolling_std * nbdevdn)
        return upperband, middleband, lowerband


    
    def show_list(self, column: str, data):
        return list(map(lambda v: v[column], data))

    def MFI(self, highs,  lows, closes, volume,  timeperiod:float = 14):
        typical_price = (highs + lows + closes) / 3
        raw_money_flow = typical_price * volume
        positive_flow = np.where(typical_price.diff() > 0, raw_money_flow, 0)
        negative_flow = np.where(typical_price.diff() < 0, raw_money_flow, 0)
        positive_mf = pd.Series(positive_flow).rolling(window=timeperiod, min_periods=1).sum()
        negative_mf = pd.Series(negative_flow).rolling(window=timeperiod, min_periods=1).sum()
        money_ratio = positive_mf / negative_mf
        mfi = 100 - (100 / (1 + money_ratio))
        return mfi

    def heikin_ashi(self, candles):
        
        ha_open = []
        ha_high = []
        ha_low = []
        ha_close = []

        if len(candles) <= 1:
            return ha_open, ha_high, ha_low, ha_close

        # Inicialización de la primera vela Heikin-Ashi
        ha_open.append(candles[0]['Open_price'])
        ha_close.append((candles[0]['Open_price'] + candles[0]['High_price'] + candles[0]['Low_price'] + candles[0]['Close_price']) / 4)
        ha_high.append(max(candles[0]['High_price'], ha_open[0], ha_close[0]))
        ha_low.append(min(candles[0]['Low_price'], ha_open[0], ha_close[0]))

        for i in range(1, len(candles)):
            open_price = (ha_open[-1] + ha_close[-1]) / 2
            close_price = (candles[i]['Open_price'] + candles[i]['High_price'] + candles[i]['Low_price'] + candles[i]['Close_price']) / 4
            high_price = max(candles[i]['High_price'], open_price, close_price)
            low_price = min(candles[i]['Low_price'], open_price, close_price)

            ha_open.append(open_price)
            ha_close.append(close_price)
            ha_high.append(high_price)
            ha_low.append(low_price)

        return ha_open, ha_high, ha_low, ha_close
    
    def identify_exit_signal(self, ha_open, ha_close, ha_high, ha_low, n=5): #Identifica una señal de salida en tendencia alcista.
         # Considera las últimas n velas para la señal de salida
        exit_signals = []
        for i in range(-n, 0):
            last_open = ha_open[i]
            last_close = ha_close[i]
            last_high = ha_high[i]
            last_low = ha_low[i]
            body_size = abs(last_close - last_open)
            shadow_size = last_high - last_low
            exit_signals.append(body_size < shadow_size / 2)
        return sum(exit_signals) > n / 2

    def analyze_trend_and_signals(self, candles):  #Analiza la tendencia actual, punto de entrada y punto de salida en base a la última vela Heikin-Ashi.
        ha_open, ha_high, ha_low, ha_close = self.heikin_ashi(candles)
        trend = self.identify_current_trend(ha_open, ha_close, ha_high, ha_low)
        entry_signal = self.identify_bullish_entry_signal(ha_open, ha_close) 
        exit_signal = self.identify_exit_signal(ha_open, ha_close, ha_high, ha_low) 
        return trend, entry_signal, exit_signal

    def identify_bullish_entry_signal(self, ha_open, ha_close, n=5):  #Identifica una señal de entrada en tendencia alcista.
        # Considera las últimas n velas para la señal de entrada
        entry_signals = []
        for i in range(-n, 0):
            last_open = ha_open[i]
            last_close = ha_close[i]
            entry_signals.append(last_close > last_open)
        return sum(entry_signals) > n / 2


    def identify_current_trend(self, ha_open, ha_close, ha_high, ha_low):
        # Utilizar un historial de tendencias recientes para suavizar las transiciones
        trends = []

        for i in range(len(ha_open)):
            body_size = abs(ha_close[i] - ha_open[i])
            shadow_size = ha_high[i] - ha_low[i]
            if ha_close[i] > ha_open[i]:
                trends.append('up')
            elif ha_close[i] < ha_open[i]:
                trends.append('down')
            else:
                if shadow_size > 2 * body_size:
                    trends.append('consolidation')
                else:
                    trends.append('neutral')

        # Determinar la tendencia actual basándose en el historial reciente
        if trends[-1] == 'up' and trends[-2] == 'up':
            return 'up'
        elif trends[-1] == 'down' and trends[-2] == 'down':
            return 'down'
        else:
            body_size = abs(ha_close[-1] - ha_open[-1])
            shadow_size = ha_high[-1] - ha_low[-1]
            if shadow_size > 2 * body_size:
                return 'consolidation'
            else:
                return 'neutral'
    def stop_price(self, side:str = "", price:float =0, perc_stop: float=0.035, perc_price: float= 0.0185):
        stopPriceSide= 0
        priceSide = 0
        if side =="BUY":
            stopPriceSide=  int(price + price * perc_stop /100)
            priceSide= int(stopPriceSide + stopPriceSide * perc_price  /100) 
            
        elif side=="SELL":    
            stopPriceSide=  int(price - price * perc_stop /100)
            priceSide= int(stopPriceSide - stopPriceSide * perc_price  /100) 
        return stopPriceSide, priceSide
    
    def user_asset(self, asset: str =""):
        return self._request(endpoint="user_asset", parameters={"asset": asset})    
    
    def my_trades(self, symbol):
        return self._request("my_trades", parameters={"symbol":symbol})
    
    def percPro(self, last_price, price):
        return (abs(last_price - price) / (last_price + price)) * 100

    def min_crypto_buy(self):
        #BTC_TRY 0.00001 ETH_TRY 0.0001 BTC_ARS 0.00003
        pair = self.symbol
        exchange_rates = {
                'BTCTRY': 0.00001,
                'ETHTRY': 0.0001,
                'BTCARS': 0.00003,
                'BTCUSDT': 0.00007,
                'BTCUSDC': 0.9899,
                'BTCFDUSD': 0.00007,
                'FDUSDUSDT': 0.9987,
                'FDUSDTRY': 1.0024,
                'ETHBTC':0.000109, #EQUIVALE A 7.48 DOLARES
                "BNBBTC": 0.012, #EQUIVALE A 7.48 DOLARES
            }

        return float(exchange_rates.get(pair, 0))
    
    def update_chart(self, candles, closes, upperband, lowerband, smaS, smaM, smaL, fig):
        # Crear el subgráfico de velas e indicadores
        ax1 = fig.add_subplot(1, 1, 1)
        ax1.set_ylabel('Price')
        ax1.set_xlabel('Time')
        df = self.create_dataframe(candles)
        df['Datetime'] = df.index.map(mdates.date2num)
        
        # Ajustar el ancho de las velas
        ohlc = df[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']].values
        candlestick_ohlc(ax=ax1, quotes=ohlc, width=0.0001, colorup='green', colordown='red') # Aumentar el ancho de las velas
        
        # Graficar los otros indicadores
        ax1.plot(df['Datetime'], closes, label='Closes prices', color='black', linewidth=0.8)
        ax1.plot(df['Datetime'], upperband, label='Upper Band', color='blue', linewidth=0.8)
        ax1.plot(df['Datetime'], lowerband, label='Lower Band', color='red', linewidth=0.8)
        ax1.plot(df['Datetime'], smaS, label='SMA Short', color='orange', linewidth=0.8)
        ax1.plot(df['Datetime'], smaM, label='SMA Medium', color='purple', linewidth=0.8)
        ax1.plot(df['Datetime'], smaL, label='SMA Long', color='green', linewidth=0.8)
        
        # Añadir la leyenda para los indicadores de precios
        ax1.legend(loc='upper left', fontsize='small')
        
        # Ajustar los límites del eje y para mejorar la visualización
        ax1.set_ylim(min(df['Low'])-min(df['Low'])*1.3/100, max(df['High'])+ max(df['High'])*1.3/100)
        
        # Ajustar el espaciado entre subgráficos
        fig.tight_layout(pad=0.8)
        return fig
    
