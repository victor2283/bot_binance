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
last_order_tradeId =0
sTrade =0
last_trend=""
perc_stopSide= 0.035
perc_priceSide=0.0185
while True:
    price_market = bot.symbol_price(symbol)
    alert_band=""
    alert_mfi=""
    alert_rsi=""
    alert_macd=""
    alert_sma=""
    highs = bot.show_list(column='High_price', data=candles)
    lows = bot.show_list(column='Low_price', data=candles)
    closes= bot.show_list(column='Close_price', data=candles)
    volume = bot.show_list(column='Volume', data=candles)
    closes_serie =  bot.series(closes)
    highs_serie = bot.series(highs)
    lows_serie = bot.series(lows)
    volume_serie = bot.series(volume)
    mfi = bot.MFI(highs= highs_serie, lows= lows_serie, closes= closes_serie, volume= volume_serie ,  timeperiod=mPd)
    upperband, middleband, lowerband = bot.BBANDS(closes=closes_serie, timeperiod=lPd, nbdevup=nbdevup, nbdevdn=nbdevdn)
    rsi = bot.RSI(closes=closes_serie, timeperiod=sPd)
    macd, macdsignal, macdhist = bot.MACD(closes=closes_serie, fastperiod=sPd*2, slowperiod=sPd*3, signalperiod=sPd)
    smaS= bot.SMA(closes=closes_serie, timeperiod=sPd)
    smaM= bot.SMA(closes=closes_serie, timeperiod=mPd)
    smaL= bot.SMA(closes=closes_serie, timeperiod=lPd)
    if bot.confirm_signal_sma(smaS, smaM, smaL):
        alert_sma=bot.confirm_signal_sma(smaS, smaM, smaL)
    if bot.confirm_signal_macd(macd, macdsignal, closes=closes_serie):
        alert_macd = bot.confirm_signal_macd(macd, macdsignal, closes=closes_serie)
    if bot.confirm_signal_rsi(rsi=rsi, closes=closes_serie):
        alert_rsi = bot.confirm_signal_rsi(rsi=rsi, closes= closes_serie)
    if bot.confirm_mfi(mfi=mfi):
        alert_mfi = bot.confirm_mfi(mfi=mfi)
    if bot.confirm_band(price_market, upperband, middleband, lowerband):
        alert_band= bot.confirm_band(price_market, upperband, middleband, lowerband)    
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
    
    trend, entry_signal, exit_signal = bot.analyze_trend_and_signals(candles=candles)
    print_ear = f"ear:{float(ear):.{3}f} = {asset_secundary}: {float(fiat):.{2}f} + {asset_primary}: {float(quantity):.{8}f}"
    print_signals= f"alert:[{trend}] band:[{alert_band}] mfi:[{alert_mfi}]"
    #price sell***
    stopPriceSide, priceSide = bot.stop_price(side="SELL", price=price_market, perc_stop=perc_stopSide, perc_price=perc_priceSide)
    stopPriceSell=  stopPriceSide
    priceSell= priceSide
    #priceBuy *****
    stopPriceSide, priceSide = bot.stop_price(side="BUY", price=price_market, perc_stop=perc_stopSide, perc_price=perc_priceSide)
    stopPriceBuy=  stopPriceSide
    priceBuy= priceSide
    buy_quantity =float(math.floor(fiat / priceBuy/price_min_sell)* price_min_sell) # calculo market buy

    #****
    
    if orderId !=0:
        cancel_order= bot.get_orderId(orderId= orderId)
        aux_price = float(cancel_order['price'])
        aux_side = cancel_order['side']
        print(f" Trade: [{sTrade}] | {print_signals} | Price: {round(price_market,2)} | {print_ear} | buy price: {round(aux_price,2)}")    
        if (last_trend=="consolidation" or last_trend=="neutral")   and ((alert_macd !="down_div"  and trend == "up" and aux_side == "SELL" and priceSell > aux_price) or (alert_macd !="up_div"  and trend== "down" and aux_side == "BUY" and priceBuy < aux_price)):
            if bot.get_orderId(orderId= orderId)['status']  == "NEW": 
                rs= bot.cancel_orderId(orderId= orderId)
                if rs["status"]=="CANCELED":
                    print(f"orden {rs['type']} ID: {rs['orderId']} {rs['status']}")
    else:
        if price_buy > 0 and (quantity > price_min_sell and fiat < price_min_buy):
            perc_stop_loss= round(float(bot.percPro(last_price=price_buy, price=priceSell)),2)
            print(f" Trade: [{sTrade}] | {print_signals} | Price: {round(price_market,2)} | {print_ear} | buy price: {price_buy} perc:{perc_stop_loss}")
            if exit_signal ==True and  alert_mfi== "down" and alert_sma !="up" and alert_rsi !="up_div" and alert_macd !="up_div" and  ((priceSell < price_buy and perc_stop_loss > perc_binance * 0.19) or  (priceSell > price_buy and perc_stop_loss > perc_binance * 1.19)):
                result = bot.new_order(side="SELL",type="STOP_LOSS_LIMIT", quantity= float(math.floor(quantity/price_min_sell)* price_min_sell), stopPrice= stopPriceSell, price=priceSell, mode=mode_Soft)                                
                if len(result)>0:
                    rs =bot.get_orderId(orderId= result["orderId"])
                    print(f"order type: {rs['type']} | ID: {rs['orderId']} | status: {rs['status']} | price:{round(float(rs['price']),2)}")
            
        elif price_buy == 0 and (quantity < price_min_sell and fiat >= price_min_buy): 
            perc_stop_loss= round(float(bot.percPro(last_price=price_buy, price=priceBuy)),2)
            print(f" Trade: [{sTrade}] | {print_signals} | Price: {round(price_market,2)} | {print_ear} |  buy price: {price_buy} ")
            if  alert_sma != "down" and price_market < lowerband.iloc[-1] and alert_mfi== "up" and alert_rsi !="down_div" and alert_macd !="down_div" and entry_signal == True: 
                print(f" buscando precio de compra... al precio: {last_price_market} | alert: {alert_band}")
                result = bot.new_order(side="BUY",type="STOP_LOSS_LIMIT",quantity= buy_quantity, stopPrice= stopPriceBuy,price=priceBuy, mode=mode_Soft)
                if len(result)>0:
                    rs =bot.get_orderId(orderId= result["orderId"])
                    print(f"order type: {rs['type']} | ID: {rs['orderId']} | status: {rs['status']} | price:{round(float(rs['price']),2)}")

        
    time.sleep(3)
    candles = bot.addcandle(candles)
    last_trend= trend
    # si no hay orden activa
    last_price_market = price_market
    
