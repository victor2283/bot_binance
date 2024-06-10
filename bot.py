import config
from pprint import pprint
from binance.spot import Spot
import talib as ta
import time
import pandas as pd
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

        
        # Identificar divergencias alcistas y bajistas
        previous_max = data_values.iloc[0]  # Inicializar máximo anterior con primer valor
        previous_min = data_values.iloc[0]  # Inicializar mínimo anterior con primer valor


        for i in range(len(data_values)): # Recorrer desde 0 hasta len(data_values) - 1
            # Detectar divergencia alcista: El precio del activo está haciendo mínimos más bajos, mientras que el RSI está haciendo mínimos más altos.
            if data_values.iloc[i] < previous_max and close_prices.iloc[i] > close_prices.iloc[i - 1]:
                bullish_divergences.append((i, data_values.iloc[i], previous_max, close_prices.iloc[i], close_prices.iloc[i - 1]))
                previous_max = data_values.iloc[i]  # Actualizar máximo anterior
            
            # Detectar divergencia bajista, El precio del activo está haciendo máximos más altos, mientras que el RSI está haciendo máximos más bajos.
            if data_values.iloc[i] > previous_min and close_prices.iloc[i] < close_prices.iloc[i - 1]:
                bearish_divergences.append((i, data_values.iloc[i], previous_min, close_prices.iloc[i], close_prices.iloc[i - 1]))
                previous_min = data_values.iloc[i]  # Actualizar mínimo anterior
        return {
                "up_divergences": bullish_divergences,
                "down_divergences": bearish_divergences
        }
                
               
    def confirm_signal_rsi(self, rsi, closes):
        
        divergences = self.confirm_divergences(data_values=rsi, close_prices=closes)
        
        
        if len(divergences.get("up_divergences")) == len(divergences.get("down_divergences"))==0:
            if   rsi.iloc[-1] > 70:
                return "down" 
        
            if rsi.iloc[-1] < 30:
                return "up"           
        else:
            #print("Divergencias alcistas:")
            for divergence in divergences.get("up_divergences"):
                print(f"Índice: {divergence[0]}, idicador: {divergence[1]}, {divergence[2]}, Precio: {divergence[3]}, {divergence[4]}")
            
            if  len(divergences.get("up_divergences")[-1]) > 0: 
                return "up_divergence"

            #print("\nDivergencias bajistas:")
            for divergence in divergences.get("down_divergences"):
                print(f"Índice: {divergence[0]}, indicador: {divergence[1]}, {divergence[2]}, Precio: {divergence[3]}, {divergence[4]}")
            
            if  len(divergences.get("down_divergences")[-1]) > 0: 
                return "down_divergence"
    
    def confirm_signal_macd(self, macd, signal, closes):
        
        divergences = self.confirm_divergences(data_values=macd, close_prices=closes)
        
        
        if len(divergences.get("up_divergences")) == len(divergences.get("down_divergences"))==0:
            if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] < signal.iloc[-2]:
                return "up"  # Cruce alcista
            elif macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-2] > signal.iloc[-2]:
                return "down"  # Cruce bajista
        else:
            #print("Divergencias alcistas:")
            for divergence in divergences.get("up_divergences"):
                print(f"Índice: {divergence[0]}, idicador: {divergence[1]}, {divergence[2]}, Precio: {divergence[3]}, {divergence[4]}")
            if  len(divergences.get("up_divergences")[-1]) > 0: 
                return "up_divergence"

            #print("\nDivergencias bajistas:")
            for divergence in divergences.get("down_divergences"):
                print(f"Índice: {divergence[0]}, indicador: {divergence[1]}, {divergence[2]}, Precio: {divergence[3]}, {divergence[4]}")
            if  len(divergences.get("down_divergences")[-1]) > 0: 
                return "down_divergence"
            
    def confirm_double_crossover(self, sma_min, sma_medium, sma_max): 
        if self.confirm_single_crossover(sma_min, sma_medium) == self.confirm_single_crossover(sma_medium, sma_max):
            return self.confirm_single_crossover(sma_medium, sma_max)
       
    
    def confirm_single_crossover(self, sma_min, sma_max):

        if sma_min.iloc[-1] > sma_max.iloc[-1] and sma_min.iloc[-2] < sma_max.iloc[-2]:
            return "up"
        if sma_min.iloc[-1] < sma_max.iloc[-1] and sma_min.iloc[-2] > sma_max.iloc[-2]:
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

    def confirm_signal_dema(self, dema, closes, price_market):
        if price_market == closes.iloc[-1]:
            if dema.iloc[-1] > closes.iloc[-1] and dema.iloc[-2] < closes.iloc[-2]:
                return "up"
            if dema.iloc[-1] > closes.iloc[-1] and dema.iloc[-2] < closes.iloc[-2]:
                return "down"    
    
    def confirm_signal_all(self, data):
        up_count = 0
        down_count = 0
        for signal in data:
            if signal == "up" or signal == "up_divergence":
                up_count += 1
            elif signal == "down" or signal == "down_divergence":
                down_count += 1
            
        if up_count > down_count:
            return "up"
        elif up_count < down_count:        
            return "down"
        
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
    
    
    def series(self, closes):
        return pd.Series(closes)
    def SMA(self, closes_serie, timeperiod:float = 20):
        return ta.SMA(closes_serie, timeperiod=timeperiod)
    
    def RSI(self, closes_serie, timeperiod:float = 20):
        return ta.RSI(closes_serie, timeperiod=timeperiod)
    
    def MACD(self, closes_serie, fastperiod:float = 90, slowperiod:float = 15, signalperiod:float = 20):
        return ta.MACD(closes_serie, fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
    
    def MFI(self, highs_serie,  lows_serie, closes_serie, volume_serie,  timeperiod:float = 20):
        return ta.MFI(highs_serie, lows_serie, closes_serie, volume_serie ,  timeperiod=timeperiod)
    
    def DEMA(self, closes_serie, timeperiod:float = 20):
        return ta.DEMA(closes_serie, timeperiod=timeperiod)
    
    def BBANDS(self, closes_serie, timeperiod:float = 20, nbdevup: int = 2, nbdevdn:int = 2, matype:int =0):
        return ta.BBANDS(closes_serie, timeperiod=timeperiod, nbdevup=nbdevup, nbdevdn=nbdevdn, matype=matype)
    def show_list(self, column: str, data):
        return list(map(lambda v: v[column], data))

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



    
    
    
