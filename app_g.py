from bot import BotBinance
from tkinter import messagebox
import tkinter as tk
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import mplfinance as mpf
from mplfinance.original_flavor import candlestick_ohlc
import pandas as pd
import math
import datetime
from matplotlib.dates import date2num

import time
from pprint import pprint


mode_Soft=1 # modo 0 como demo - modo 1 produccion con datos reales
asset_primary = "BTC"
asset_secundary="TRY"
symbol = asset_primary + asset_secundary
bot = BotBinance(symbol=symbol, interval="1m", limit=300)
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
running = False  # Estado del bot
candles=[]

# Crear la ventana principal
root = tk.Tk()
root.title("Bot de Trading")
root.geometry("1200x800")  # Ajustar el tamaño de la ventana

# Crear frames para organización
frame_top = tk.Frame(root)
frame_top.pack(pady=10)

frame_middle = tk.Frame(root)
frame_middle.pack(pady=10)

frame_bottom = tk.Frame(root)
frame_bottom.pack(pady=10)

# Función para actualizar los datos
def update_data():
    global candles, price_market, last_price_market, ear, last_order_tradeId, sTrade, last_trend
    candles = bot.candlestick()
    if not running:
        return
    
    price_market = bot.symbol_price(symbol)
    price_min_sell = bot.min_crypto_buy() #BTC_TRY 0.00001 ETH_TRY 0.0001 BTC_ARS 0.00003
    alert_band = ""
    alert_mfi = ""
    alert_rsi = ""
    alert_macd = ""
    alert_sma = ""
    
    highs = bot.show_list(column='High_price', data=candles)
    lows = bot.show_list(column='Low_price', data=candles)
    closes = bot.show_list(column='Close_price', data=candles)
    volume = bot.show_list(column='Volume', data=candles)
    closes_serie = bot.series(closes)
    highs_serie = bot.series(highs)
    lows_serie = bot.series(lows)
    volume_serie = bot.series(volume)
    
    mfi = bot.MFI(highs=highs_serie, lows=lows_serie, closes=closes_serie, volume=volume_serie, timeperiod=mPd)
    upperband, middleband, lowerband = bot.BBANDS(closes=closes_serie, timeperiod=lPd, nbdevup=nbdevup, nbdevdn=nbdevdn)
    rsi = bot.RSI(closes=closes_serie, timeperiod=sPd)
    macd, macdsignal, macdhist = bot.MACD(closes=closes_serie, fastperiod=sPd * 2, slowperiod=sPd * 3, signalperiod=sPd)
    smaS = bot.SMA(closes_serie, timeperiod=sPd)
    smaM = bot.SMA(closes_serie, timeperiod=mPd)
    smaL = bot.SMA(closes_serie, timeperiod=lPd)
    
    if bot.confirm_signal_sma(smaS, smaM, smaL):
        alert_sma = bot.confirm_signal_sma(smaS, smaM, smaL)
    if bot.confirm_signal_macd(macd, macdsignal, closes_serie):
        alert_macd = bot.confirm_signal_macd(macd, macdsignal, closes_serie)
    if bot.confirm_signal_rsi(rsi=rsi, closes=closes_serie):
        alert_rsi = bot.confirm_signal_rsi(rsi=rsi, closes= closes_serie)
    if bot.confirm_mfi(mfi=mfi):
        alert_mfi = bot.confirm_mfi(mfi=mfi)
    if bot.confirm_band(price_market, upperband, middleband, lowerband):
        alert_band = bot.confirm_band(price_market, upperband, middleband, lowerband)

    price_min_buy = price_market * price_min_sell    
    if len(bot.user_asset(asset=asset_primary)) > 0:
        quantity = float(bot.user_asset(asset_primary)[0]["free"])
    else:
        quantity = 0
    if len(bot.user_asset(asset=asset_secundary)) > 0:
        fiat = float(bot.user_asset(asset_secundary)[0]["free"])
    else:
        fiat = 0
    
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
    print_alert=""
    print_msg = ""
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
        print_alert= f" Trade: [{sTrade}] | {print_signals} | buy price: {round(aux_price,2)}"    
        if (last_trend=="consolidation" or last_trend=="neutral")   and ((alert_macd !="down_div"  and trend == "up" and aux_side == "SELL" and priceSell > aux_price) or (alert_macd !="up_div"  and trend== "down" and aux_side == "BUY" and priceBuy < aux_price)):
            if bot.get_orderId(orderId= orderId)['status']  == "NEW": 
                rs= bot.cancel_orderId(orderId= orderId)
                if rs["status"]=="CANCELED":
                    print_msg=f"orden {rs['type']} ID: {rs['orderId']} {rs['status']}"
    else:
        if price_buy > 0 and (quantity > price_min_sell and fiat < price_min_buy):
            perc_stop_loss= round(float(bot.percPro(last_price=price_buy, price=priceSell)),2)
            print_alert=f" Trade: [{sTrade}] | {print_signals} | buy price: {price_buy} perc:{perc_stop_loss}"
            if trend=="up" and entry_signal==False and  exit_signal ==True and alert_mfi== "down" and alert_rsi =="down" and alert_macd !="up_div" and alert_sma !="up" and  ((priceSell < price_buy and perc_stop_loss > perc_binance) or  (priceSell > price_buy and perc_stop_loss > perc_binance * 1.69)):
                result = bot.new_order(side="SELL",type="STOP_LOSS_LIMIT", quantity= float(math.floor(quantity/price_min_sell)* price_min_sell), stopPrice= stopPriceSell, price=priceSell, mode=mode_Soft)                                
                if len(result)>0:
                    rs =bot.get_orderId(orderId= result["orderId"])
                    print_msg=f"order type: {rs['type']} | ID: {rs['orderId']} | status: {rs['status']} | price:{round(float(rs['price']),2)}"
            
        elif price_buy == 0 and (quantity < price_min_sell and fiat >= price_min_buy): 
            perc_stop_loss= round(float(bot.percPro(last_price=price_buy, price=priceBuy)),2)
            print_alert=f" Trade: [{sTrade}] | {print_signals} |  buy price: {price_buy}"
            if trend=="up"  and entry_signal==True and  exit_signal ==False and  alert_sma != "down" and alert_macd !="down_div" and alert_rsi =="up" and alert_mfi== "up" and alert_band=="up" and  price_market < lowerband.iloc[-1]: 
                print_msg=f" buscando precio de compra... al precio: {last_price_market} | alert: {alert_band}"
                result = bot.new_order(side="BUY",type="STOP_LOSS_LIMIT",quantity= buy_quantity, stopPrice= stopPriceBuy,price=priceBuy, mode=mode_Soft)
                if len(result)>0:
                    rs =bot.get_orderId(orderId= result["orderId"])
                    print_msg=f"order type: {rs['type']} | ID: {rs['orderId']} | status: {rs['status']} | price:{round(float(rs['price']),2)}"

    
    # Actualizar etiquetas
    color = "green" if price_market >= last_price_market else "red"
    label_price.config(text=f"Price Market: {round(price_market, 2)}", fg=color)
    label_alerts.config(text=print_alert)
    label_ear.config(text= print_ear )
    label_msg.config(text= print_msg, fg=color)    
    
    
    # Actualizar gráfico
    update_chart(candles, closes, upperband, lowerband, smaS, smaM, smaL, rsi)
    root.after(3000, update_data)  # Actualizar cada 3000 ms si el bot está en ejecución
    
    last_trend= trend
    last_price_market = price_market
    #candles = bot.addcandle(candles)

def start_bot():
    global running
    running = True
    update_data()

def stop_bot():
    global running
    running = False
    messagebox.showinfo("Stop Bot..", "bot status = stop.")


button_start = tk.Button(frame_middle, text="start bot", command=start_bot)
button_start.grid(row=0, column=0,  columnspan=3, padx=3)

button_stop = tk.Button(frame_middle, text="stop Bot", command=stop_bot)
button_stop.grid(row=0, column=3, columnspan=3, padx=3)



# Crear widgets
label_price = tk.Label(frame_top, text="Price Market: ", font=("Arial", 14))
label_price.grid(row=0, column=0, columnspan=3, pady=3)

label_ear = tk.Label(frame_top, text="Ear: ", font=("Arial", 13))
label_ear.grid(row=0, column=5, columnspan=3, pady=3)

label_alerts = tk.Label(frame_top, text="Alerts: ", font=("Arial", 12))
label_alerts.grid(row=1, column=1, columnspan=3, pady=3)

label_msg = tk.Label(frame_top, text="Msg: ", font=("Arial", 12))
label_msg.grid(row=1, column=6, columnspan=3, pady=3)



def update_chart(candles, closes, upperband, lowerband, smaS, smaM, smaL, rsi):
    fig.clear()

    # Subgráfico de velas e indicadores
    ax1 = fig.add_subplot(2, 1, 1)
    ax1.set_ylabel('Price')
    df = bot.create_dataframe(candles)
    df['Datetime'] = df.index.map(mdates.date2num)
    ohlc = df[['Datetime', 'Open', 'High', 'Low', 'Close']].values
    # Crear el gráfico de velas
    candlestick_ohlc(
        ax=ax1,
        quotes=ohlc,
        width=0.00095,  # Ajustar el ancho de las velas
        colorup='green',  # Color de las velas alcistas
        colordown='red',  # Color de las velas bajistas
    )
 

    
    dates = [datetime.datetime.fromtimestamp(candle['Open_time'] / 1000) for candle in candles]
    # Graficar los otros indicadores
    ax1.plot(dates, closes, label='Closes prices', color='black', linewidth=0.5)
    ax1.plot(dates, upperband, label='Upper Band', color='blue', linewidth=0.5)
    ax1.plot(dates, lowerband, label='Lower Band', color='red', linewidth=0.5)
    ax1.plot(dates, smaS, label='SMA Short', color='orange', linewidth=0.5)
    ax1.plot(dates, smaM, label='SMA Medium', color='purple', linewidth=0.5)
    ax1.plot(dates, smaL, label='SMA Long', color='green', linewidth=0.5)
    ax1.legend(loc='upper left', fontsize='small')

    
    
    # Subgráfico de RSI
    ax2 = fig.add_subplot(2, 1, 2)
    ax2.plot(dates, rsi, label='RSI', color='blue')
    ax2.legend(loc='upper left', fontsize='small')

    # Ajustar el espaciado entre subgráficos
    fig.tight_layout(pad=1.0)

    canvas.draw()    

# Crear la figura de Matplotlib
fig = Figure(figsize=(10, 6), dpi=100)

# Crear el lienzo de Matplotlib para Tkinter
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()


# Iniciar la aplicación
root.mainloop()
