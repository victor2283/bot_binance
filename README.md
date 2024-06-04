# bot_binance
versión 3 del bot de binance con indicadores técnicos y estrategias implementadas. desarrollado en python

requiere de los siguientes paquetes para su funcionamiento:
Package            Version
------------------ -----------
binance-connector  
matplotlib         
pandas             
TA-Lib             
time

y un archivo config.py de las credenciales de binance previamente creadas con permisos de super usuario en el siguiente formato: 
api_key="" 
api_secret="" 
remplace los "" por su key entre ""

la aplicacion funciona muy facil, busca el precio mas bajo cuando el indicador mfi y la banda de bollinger estan en estado "up" y la alerta de trading es "up", cuando esto ocurre crea una orden a un precio con un 0.06 porciento mas alto que ese precio porque cuando cambia la tendencia y comienza a ascender el precio se completa la orden de compra, luego cuando llega a la parte superior de bollinger pregunta si el estado es down y el mfi y la alerta tambien lo son y busca el precio mas alto posible y crea una orden de venta por debajo del precio mas alto que cumpla la condicion de que este precio de venta sea mayor al precio de compra y tambien mayor a la comision de binance que es un 0.166 porciento y si esto se cumple la orden se completa al momento que el precio comienza a caer, y ademas tiene una opcion de stop loss de emergencia donde se diera el caso que la tendencia cambie mas de un 0.16 porciento hacia abajo por derrumbe de la tendencia alcista y el activo este presentando perdida para vender inmediatamente y buscar comprar mucho a mas bajo en la lista de precios.

el codigo puede modificarlo a su estratgegia personalizada pero yo lo hice asi porque pienso que todo lo que sube tiende a  bajar en muchas mas oportunidades de lo que sube entonces la orden de venta no la crea sobre el precio de mercado si no esperando que el precio de mercado caiga para completar la orden de venta y a su vez para comprar compro a un precio mas alto cuando el precio va formando nuevos minimos cuando el mfi indica que esta sobrevendido y el precio subira.

la alerta de trading es un conjunto de alertas macd, cruces de medias moviles, rsi, ema, dema para confirmar a tendencia actual por lo que acompaña a la alerta de bollinger y mfi que indica el volumen y fuerza en el momento buscando zonas de sobre compra y sobreventa.
