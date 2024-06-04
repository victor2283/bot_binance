# bot_binance
Version 3 of the binance bot with technical indicators and strategies implemented. developed in python

Requires the following packages for its operation: Package Version:

* binance-connector, 
* matplotlib, 
* pandas, 
* TA-Lib,
* time,

And a config.py file of the binance credentials previously created with super user permissions in the following format: api_key="" api_secret="" replace the "" with your key between ""

The application works very easily, it looks for the lowest price when the mfi indicator and the bollinger band are in the "up" state and the trading alert is "up", when this occurs it creates an order at a price that is 0.06 percent higher higher than that price because when the trend changes and the price begins to rise the buy order is completed, then when it reaches the top of bollinger it asks if the status is down and the mfi and the alert are also down and looks for the price highest possible and creates a sell order below the highest price that meets the condition that this sale price is greater than the purchase price and also greater than the binance commission which is 0.166 percent and if this is met the The order is completed at the moment the price begins to fall, and also has an emergency stop loss option where the trend changes more than 0.16 percent downward due to the collapse of the bullish trend and the asset is showing a loss. to sell immediately and look to buy much lower on the price list.

The code can be modified to your personalized strategy but I did it this way because I think that everything that goes up tends to go down many more times than it goes up, so the sell order is not created based on the market price but rather waiting for the price to market falls to complete the sell order and in turn to buy I buy at a higher price when the price is forming new lows when the mfi indicates that it is oversold and the price will rise.

The trading alert is a set of MACD alerts, moving average crossovers, RSI, EMA, DEMA to confirm the current trend, which accompanies the Bollinger and MFI alert that indicates the volume and strength at the moment, looking for overshoot zones. buying and overselling.
