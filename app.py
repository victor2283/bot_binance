from bot import BotBinance
from pprint import pprint
import pandas as pd
import math
import talib as ta
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
    closes = list(map(lambda v: v['closing_prices'], candles))
    volume = list(map(lambda v: v['Volume'], candles))
    lows = list(map(lambda v: v['Low_price'], candles))
    highs = list(map(lambda v: v['High_price'], candles))
    closes_serie = pd.Series(closes)
    highs_serie = pd.Series(highs)
    lows_serie = pd.Series(lows)
    volume_serie = pd.Series(volume)
    smaShort = ta.SMA(closes_serie, timeperiod=sPd)
    smaMedium = ta.SMA(closes_serie, timeperiod=mPd)
    smaLong = ta.SMA(closes_serie, timeperiod=lPd)
    rsi = ta.RSI(closes_serie, timeperiod=sPd)
    macd, macdsignal, macdhist = ta.MACD(closes_serie, fastperiod=sPd*2, slowperiod=sPd*3, signalperiod=sPd)
    mfi = ta.MFI( highs_serie,  lows_serie, closes_serie, volume_serie ,  timeperiod=mPd)
    dema = ta.DEMA(closes_serie, timeperiod=mPd)
    upperband, middleband, lowerband = ta.BBANDS(closes_serie, timeperiod=lPd, nbdevup=nbdevup, nbdevdn=nbdevdn, matype=0)
    if bot.confirm_mfi(mfi=mfi):
        alert_trading_mfi = bot.confirm_mfi(mfi=mfi)
    if bot.confirm_signal_sma(smaS=smaShort , smaM=smaMedium, smaL=smaLong):
        alert_trading_sma = bot.confirm_signal_sma(smaS=smaShort , smaM=smaMedium, smaL=smaLong)
    if bot.confirm_signal_rsi(rsi=rsi, closes=closes_serie):
        alert_trading_rsi = bot.confirm_signal_rsi(rsi=rsi, closes= closes_serie)
    if bot.confirm_signal_macd(macd, macdsignal, closes=closes_serie):
        alert_trading_macd = bot.confirm_signal_macd(macd, macdsignal, closes=closes_serie)
    if bot.confirm_signal_dema(dema, closes= closes_serie, price_market= price_market):
        alert_trading_dema=  bot.confirm_signal_dema(dema, closes= closes_serie, price_market= price_market)
    if bot.confirm_band(price_market, upperband, middleband, lowerband):
        alert_trading_band= bot.confirm_band(price_market, upperband, middleband, lowerband)    
    if bot.confirm_signal_all(data = [alert_trading_mfi, alert_trading_sma, alert_trading_rsi, alert_trading_macd, alert_trading_dema]):
        alert_trading = bot.confirm_signal_all(data = [alert_trading_mfi, alert_trading_sma, alert_trading_rsi, alert_trading_macd, alert_trading_dema]) 
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
    if orderId !=0:
        cancel_order= bot.get_orderId(orderId= orderId)
        aux_price = float(cancel_order['price'])
        aux_side = cancel_order['side']
        aux_perc = bot.percPro(last_price=aux_price, price=price_market)
        print(f" Trade: [{sTrade}] | alert:[{alert_trading}] band:[{alert_trading_band}] mfi:[{alert_trading_mfi}]| Price: {round(price_market,2)} | ear:{float(ear):.{3}f} = fiat: {float(fiat):.{2}f} + crypto: {float(quantity):.{8}f} | buy price: {round(aux_price,2)} dif:{round(aux_perc,2)}")    
        if aux_perc > 0.04 and ((alert_trading_band != "up" and  aux_side == "BUY" and price_market > aux_price) or (alert_trading_mfi == alert_trading_band == "up" and  aux_side == "BUY" and price_market < aux_price) or (alert_trading_mfi == alert_trading_band == "down"  and aux_side == "SELL" and price_market > aux_price)):
            if bot.get_orderId(orderId= orderId)['status']  == "NEW": 
                rs= bot.cancel_orderId(orderId= orderId)
                if rs["status"]=="CANCELED":
                    print(f"orden {rs['type']} ID: {rs['orderId']} {rs['status']}")
    else:
        if price_buy > 0 and (quantity > price_min_sell and fiat < price_min_buy):
            stopPrice=  int(price_market - price_market * 0.06 /100)
            price= int(stopPrice - stopPrice * 0.03 /100)
            perc_stop_loss= round(float(bot.percPro(last_price=price_buy, price=price)),2)
            print(f" Trade: [{sTrade}] | alert:[{alert_trading}] band:[{alert_trading_band}] mfi:[{alert_trading_mfi}]| Price: {round(price_market,2)} | ear:{float(ear):.{3}f} = fiat: {float(fiat):.{2}f} + crypto: {float(quantity):.{8}f} | buy price: {price_buy} porc:{perc_stop_loss}")
            if perc_stop_loss > perc_binance:
                if (price > price_buy and price_market > last_price_market) or (price_buy > price_market and alert_trading==alert_trading_mfi== alert_trading_band == "down"): #sell
                    result = bot.new_order(side="SELL",type="STOP_LOSS_LIMIT", quantity= float(math.floor(quantity/price_min_sell)* price_min_sell), stopPrice= stopPrice, price=price, mode=mode_Soft)                                
                    if len(result)>0 and len(bot.get_open_orders())> 0:
                        orderId_aux = int(bot.get_open_orders()[len(bot.get_open_orders())-1]['orderId'])    
                        price_aux= round(float(bot.get_open_orders()[len(bot.get_open_orders())-1]['price']),2)
                        print(f"Orden de venta STOP_LOSS_LIMIT {orderId_aux} creada con exito al precio {price_aux}")
        elif price_buy == 0 and (quantity < price_min_sell and fiat >= price_min_buy): 
            stopPrice=  int(price_market + price_market * 0.06 /100)
            price= int(stopPrice + stopPrice * 0.03  /100) 
            perc_stop_loss= round(float(bot.percPro(last_price=price_buy, price=price)),2)
            print(f" Trade: [{sTrade}] | alert:[{alert_trading}] band:[{alert_trading_band}] mfi:[{alert_trading_mfi}]| Price: {round(price_market,2)} | ear:{float(ear):.{3}f} = fiat: {float(fiat):.{2}f} + crypto: {float(quantity):.{8}f} | buy price: {price_buy} porc:{perc_stop_loss}")
            if alert_trading ==alert_trading_mfi== alert_trading_band == "up":
                print(f" buscando precio de compra... al precio: {last_price_market} | alert: {alert_trading_band}")
                buy_quantity =float(math.floor(fiat / price_market/price_min_sell)* price_min_sell) # calculo market buy
                if price_market <  last_price_market:
                    result = bot.new_order(side="BUY",type="STOP_LOSS_LIMIT",quantity= buy_quantity, stopPrice= stopPrice,price=price, mode=mode_Soft)
                    if len(result)>0 and len(bot.get_open_orders())> 0:
                        orderId_aux = int(bot.get_open_orders()[len(bot.get_open_orders())-1]['orderId'])
                        price_aux= round(float(bot.get_open_orders()[len(bot.get_open_orders())-1]['price']),2)
                        print(f"Orden de comptra {orderId_aux} creada con exito de {price_aux}")
                        
    time.sleep(3)
    candles = bot.addcandle(candles)
    last_alert_trading= alert_trading
    # si no hay orden activa
    last_price_market = price_market