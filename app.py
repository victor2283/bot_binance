from bot import BotBinance
from pprint import pprint
import math
import time
#import numpy as np
#import matplotlib.pyplot as plt
#import random

mode_Soft=1 # modo 0 como demo - modo 1 produccion con datos reales
asset_primary = "BTC"
asset_secundary="TRY"
#asset_secundary="ARS"
#asset_secundary="USDT"
symbol = asset_primary + asset_secundary
bot = BotBinance(symbol=symbol, interval="1m", limit=300)
price_min_sell = bot.min_crypto_buy() #BTC_TRY 0.00001 ETH_TRY 0.0001 BTC_ARS 0.00003
candles = bot.candlestick()
ear = 0
perc_binance = 0.16666
price_market = 0
last_price_market = 0
sPd = 9
mPd = sPd * 2
lPd = mPd * 3
price_buy = 0
nbdevup= 2
nbdevdn=2
orderId=0
stop_loss_pct = 0.035
take_profit_pct = 0.035
perc_max= 0.51
perc_min = 0.34
last_order_tradeId =0
sTrade =0
last_trend=""
while True:
    price_market = bot.symbol_price(symbol)
    alert_trading = ""
    last_alert_trading=""
    alert_trading_rsi = ""
    alert_trading_sma = ""    
    alert_trading_macd = ""
    alert_trading_band=""
    alert_trading_mfi=""
    alert_trading_dema=""
    highs = bot.show_list(column='High_price', data=candles)
    lows = bot.show_list(column='Low_price', data=candles)
    closes= bot.show_list(column='Close_price', data=candles)
    volume = bot.show_list(column='Volume', data=candles)
    closes_serie =  bot.series(closes)
    highs_serie = bot.series(highs)
    lows_serie = bot.series(lows)
    volume_serie = bot.series(volume)
    
    
    
    smaShort = bot.SMA(closes_serie=closes_serie, timeperiod=sPd)
    smaMedium = bot.SMA(closes_serie=closes_serie, timeperiod=mPd)
    smaLong = bot.SMA(closes_serie=closes_serie, timeperiod=lPd)
    rsi = bot.RSI(closes_serie=closes_serie, timeperiod=sPd) 
    macd, macdsignal, macdhist = bot.MACD(closes_serie=closes_serie, fastperiod=sPd*2, slowperiod=sPd*3, signalperiod=sPd)
    mfi = bot.MFI(highs_serie= highs_serie, lows_serie= lows_serie, closes_serie= closes_serie, volume_serie= volume_serie ,  timeperiod=mPd)
    dema = bot.DEMA(closes_serie, timeperiod=mPd)
    upperband, middleband, lowerband = bot.BBANDS(closes_serie, timeperiod=lPd, nbdevup=nbdevup, nbdevdn=nbdevdn, matype=0)
    if bot.confirm_mfi(mfi=mfi):
        alert_trading_mfi = bot.confirm_mfi(mfi=mfi)
    if bot.confirm_signal_rsi(rsi=rsi, closes=closes_serie):
        alert_trading_rsi = bot.confirm_signal_rsi(rsi=rsi, closes= closes_serie)
    if bot.confirm_band(price_market, upperband, middleband, lowerband):
        alert_trading_band= bot.confirm_band(price_market, upperband, middleband, lowerband)    
    
    price_min_buy = price_market * price_min_sell    
    if len(bot.user_asset(asset=asset_primary)) >0:
        quantity=  float(bot.user_asset(asset_primary)[0]["free"])
    else:
        quantity=0
    if len(bot.user_asset(asset=asset_secundary))>0:
        fiat= float(bot.user_asset(asset_secundary)[0]["free"])
    else:
        fiat=0
    ear = quantity * price_market + fiat
    order_trade=[]
    if len(bot.my_trades(symbol))>0:
        order_trade = bot.my_trades(symbol)[-1]
    open_order  = bot.get_open_orders()
    if len(open_order)> 0:
        orderId = int(open_order[len(open_order)-1]['orderId'])
        if open_order[len(open_order)-1]["side"]=="BUY":
            price_buy = float(open_order[len(open_order)-1]["price"])
    else:
        orderId=0
    if float(quantity) >  float(price_min_sell) and float(fiat/ price_market) < float(quantity) and order_trade['isBuyer'] == True:
        perc_binance = (float(order_trade['commission']) / float(order_trade['qty'])) * 100
        price_buy = float(order_trade["price"])
        if order_trade['orderId'] != last_order_tradeId:
            sTrade = sTrade + 1
            last_order_tradeId= order_trade['orderId']
    elif  order_trade['isBuyer'] == False: 
        price_buy = 0
        if order_trade['orderId'] != last_order_tradeId:
            sTrade = sTrade + 1
            last_order_tradeId= order_trade['orderId']
    
    msg = f"ear:{float(ear):.{3}f} = {asset_secundary}: {float(fiat):.{2}f} + {asset_primary}: {float(quantity):.{8}f}"
    trend, entry_signal, exit_signal = bot.analyze_trend_and_signals(candles=candles)
    alert_trading=trend
    #price sell***
    stopPriceSell=  int(price_market - price_market * 0.035 /100)
    priceSell= int(stopPriceSell - stopPriceSell * 0.0185 /100)
    #****
    #priceBuy *****
    stopPriceBuy=  int(price_market + price_market * 0.040 /100)
    priceBuy= int(stopPriceBuy + stopPriceBuy * 0.018  /100) 
    #****
    if orderId !=0:
        cancel_order= bot.get_orderId(orderId= orderId)
        aux_price = float(cancel_order['price'])
        aux_side = cancel_order['side']
        print(f" Trade: [{sTrade}] | alert:[{alert_trading}] band:[{alert_trading_band}] mfi:[{alert_trading_mfi}] rsi:[{alert_trading_rsi}] | Price: {round(price_market,2)} | {msg} | buy price: {round(aux_price,2)}")    
        if (last_trend=="consolidation" or last_trend=="neutral")   and ((trend == "up" and aux_side == "SELL" and priceSell > aux_price) or (trend== "down" and aux_side == "BUY" and priceBuy < aux_price)):
            if bot.get_orderId(orderId= orderId)['status']  == "NEW": 
                rs= bot.cancel_orderId(orderId= orderId)
                if rs["status"]=="CANCELED":
                    print(f"orden {rs['type']} ID: {rs['orderId']} {rs['status']}")
    else:
        if price_buy > 0 and (quantity > price_min_sell and fiat < price_min_buy):
            perc_stop_loss= round(float(bot.percPro(last_price=price_buy, price=priceSell)),2)
            print(f" Trade: [{sTrade}] | alert:[{alert_trading}] band:[{alert_trading_band}] mfi:[{alert_trading_mfi}] rsi:[{alert_trading_rsi}] | Price: {round(price_market,2)} | {msg} | buy price: {price_buy} perc:{perc_stop_loss}")
            if price_market > upperband.iloc[-1] and  perc_stop_loss > perc_binance  and  priceSell > price_buy: #sell
                result = bot.new_order(side="SELL",type="STOP_LOSS_LIMIT", quantity= float(math.floor(quantity/price_min_sell)* price_min_sell), stopPrice= stopPriceSell, price=priceSell, mode=mode_Soft)                                
                if len(result)>0:
                    rs =bot.get_orderId(orderId= result["orderId"])
                    print(f"order type: {rs['type']} | ID: {rs['orderId']} | status: {rs['status']} | price:{round(float(rs['price']),2)}")
        elif price_buy == 0 and (quantity < price_min_sell and fiat >= price_min_buy): 
            perc_stop_loss= round(float(bot.percPro(last_price=price_buy, price=priceBuy)),2)
            print(f" Trade: [{sTrade}] | alert:[{alert_trading}] band:[{alert_trading_band}] mfi:[{alert_trading_mfi}] rsi:[{alert_trading_rsi}] | Price: {round(price_market,2)} | {msg} |  buy price: {price_buy} ")
            if price_market < lowerband.iloc[-1] and alert_trading_mfi==alert_trading_rsi== "up": 
                print(f" buscando precio de compra... al precio: {last_price_market} | alert: {alert_trading_band}")
                buy_quantity =float(math.floor(fiat / price_market/price_min_sell)* price_min_sell) # calculo market buy
                if price_market <  last_price_market:
                    result = bot.new_order(side="BUY",type="STOP_LOSS_LIMIT",quantity= buy_quantity, stopPrice= stopPriceBuy,price=priceBuy, mode=mode_Soft)
                    if len(result)>0:
                        rs =bot.get_orderId(orderId= result["orderId"])
                        print(f"order type: {rs['type']} | ID: {rs['orderId']} | status: {rs['status']} | price:{round(float(rs['price']),2)}")
                        
                        
    time.sleep(3)
    candles = bot.addcandle(candles)
    last_alert_trading= alert_trading
    # si no hay orden activa
    last_price_market = price_market
    last_trend= trend
