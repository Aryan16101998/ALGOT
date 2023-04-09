import sys
## import common packages
sys.path.append('../common')
from kiteSession import KiteSession
import utility
from logger import logger
import kiteWebSocket
from symbol import Symbol, OptionType, Side
import orderManager
## import other libs
import pandas as pd
import datetime
import time
import positionHandler


##########################################################################
##########################################################################
####################    DECLARE  GLOBALS VARIABLES    ####################
##########################################################################
##########################################################################


####################initialize kite objects####################
kite_session = KiteSession()
kite = kite_session.kite
kws = kite_session.kws
############# strategy input parameters ###############

name = "BANKNIFTY"
index_name = "NIFTY BANK"
expiry = datetime.date(2023, 4, 6)
time_frame = "minute"

position_open_time = datetime.time(hour=10, minute=00)
position_close_time = datetime.time(hour=15, minute=29)


inv_size = 1 # in lots

target_pct = 2
stop_loss_pct = 5

trailing_target_pct = 1
trailing_stop_loss_pct = 1

curr_signal = 0
#####################################################

active_call_token = 0
active_put_token = 0
timenow_ = datetime.datetime.now()
tokens_  = []
active_symbol = []

# bnf_components_names = ["AUBANK", "AXISBANK", "BANDHANBNK", "BANKBARODA", "FEDERALBNK", "HDFCBANK", "ICICIBANK", "IDFCFIRSTB", "INDUSINDBK", "KOTAKBANK", "PNB", "SBIN"]
bnf_components_names = ["HDFCBANK" , "ICICIBANK","SBIN"]
bnf_component_tokens = []
bnf_components_syminfo = []
##########################################################################
##########################################################################
####################    PROCESS  GLOBALS VARIABLES    ####################
##########################################################################
##########################################################################


today = datetime.date.today()
open_time = datetime.datetime.combine(today, position_open_time)
close_time = datetime.datetime.combine(today, position_close_time)

market_open_time = datetime.datetime.combine(today, datetime.time(hour = 10, minute = 00))
market_close_time = datetime.datetime.combine(today, datetime.time(hour = 15, minute = 28))

logger.info("INIT, Position Open: %s, Position Close:  %s, Market Open Time: %s, Market Close Time: %s", open_time, close_time, market_open_time, market_close_time)
logger.info("INIT, Underlying symbol to Trade: %s, Expiry: %s", name, expiry)

logger.info("INIT, Downloading instrument info.......")
instrument_info = pd.DataFrame(utility.getInstrumentInfo(kite))

stock_token = []
stock_syminfo = []
for i in range(0,3) :
    stock_token[i], stock_syminfo[i] = utility.getIndexInfo(instrument_info, bnf_components_names[i])
    syminfo = instrument_info[(instrument_info['name'] == name) & (instrument_info['expiry'] == expiry)]

# logger.info("INIT, Loaded Index\n%s", index_syminfo[['name', 'instrument_token', 'tradingsymbol', 'expiry', 'lot_size', 'exchange']])
# logger.info("INIT, Loaded Symbols\n%s", syminfo[['name', 'instrument_token', 'tradingsymbol', 'expiry', 'strike', 'lot_size', 'exchange']])

lotSize_ = utility.getLotSize(syminfo)
inv_size *= lotSize_ 
logger.info("INIT, LotSize: %s, MaxInv %s\n", lotSize_, inv_size)


stock_symbol = []
for i in range(0,3) :
    stock_symbol[i] = Symbol(index_syminfo)

# for component in bnf_components_names:
#     sym_info = instrument_info[(instrument_info['tradingsymbol'] == component) & (instrument_info['instrument_type'] == "EQ") & (instrument_info['exchange'] == "NSE")] ## for equity
#     bnf_component_tokens.append(int(sym_info['instrument_token'].to_string(index = False)))
#     bnf_components_syminfo.append(sym_info)
    


positionHandler_ = positionHandler.PositionHandler(inv_size)

##########################################################################
##########################################################################
####################    STRATEGY LOGIC STARTS HERE    ####################
##########################################################################
##########################################################################

# Callback for tick reception.
# on_ticks(ws, ticks) - Triggered when ticks are recevied.
# ticks - List of tick object. Check below for sample structure.

## this function will be called every time tick is received. Do all the logic here
def onMarketData(ws):
    global positionHandler_, tokens_
    syms_to_remove = positionHandler_.onMarketData()
    
    if len(syms_to_remove) > 0:
        # we need to remove some symbols
        for sym_type in syms_to_remove:
            token = positionHandler_.getSymbolFromHandler(sym_type).token
            kiteWebSocket.removeSymbolFromSubscriptionList(tokens_, token)
            kiteWebSocket.unsubscribeSymbol(ws, token)
            positionHandler_.removeSymbolFromHandler(sym_type)
    return

def on_ticks(ws, ticks):
    logger.debug("Tick Received {}".format(ticks))
    global timenow_, positionHandler_, index_symbol, index_token
            
    timenow_ = datetime.datetime.now()
    for tick in ticks:
        ltp = tick['last_price']
        token = tick['instrument_token']
        if token == index_token:
            index_symbol.ltp = ltp
        elif not positionHandler_.on_ticks(token, ltp):
            logger.warning("Tick, Unknown Symbol, %s %s", token, ltp)
            tokens = [int(token)]
            ws.unsubscribe(tokens)

    onMarketData(ws)
    

# on_order_update(ws, data) - Triggered when there is an order update for the connected user.
def on_order_update(ws, data):
    logger.debug("Order Update: {}".format(data))

##########################################################################
####################      KITE TICKER INITIALIZER     ####################
##########################################################################

# Callback for successful connection.
# on_connect - Triggered when connection is established successfully.
# response - Response received from server on successful connection.
def on_connect(ws, response):
    logger.info("Successfully connected. Response: {}".format(response))
    kiteWebSocket.subscribeToSymbols(ws, tokens_, ws.MODE_LTP)

## no need to modify this part of code generally. Only edit on_ticks and on_order_update function based on strategy logic
## Assign the callbacks.
kws.on_close = kiteWebSocket.on_close
kws.on_error = kiteWebSocket.on_error
kws.on_reconnect = kiteWebSocket.on_reconnect
kws.on_noreconnect = kiteWebSocket.on_noreconnect
kws.on_message = kiteWebSocket.on_message
kws.on_ticks = on_ticks
kws.on_order_update = on_order_update
kws.on_connect = on_connect
kiteWebSocket.addSymbolToSubscriptionList(tokens_, int(index_token)) ## initial list to subscribe
kws.connect(threaded = True)

logger.info("Kite Web Socket Started. Sleeping for 5 seconds to let it connect.....")
time.sleep(5) ## sleep for 5 seconds, give it time to connect. then we can move on to our next part of code


















##########################################################################
####################      STRATEGY FUNCTIONS HERE     ####################
##########################################################################


def downloadDataAndCalculateSignal(start_time , end_time):
    logger.info("Downloading data from %s to %s", start_time, end_time)
    global index_data, index_token, time_frame
    index_df = pd.DataFrame(kite.historical_data(str(index_token), from_date=start_time, to_date=end_time, interval=time_frame))
    if len(index_df) <= 0:
        return 0
    
    for component_token in bnf_component_tokens:
        component_df = pd.DataFrame(kite.historical_data(str(component_token), from_date=start_time, to_date=end_time, interval=time_frame))
        index_df.volume += component_df.volume

    index_data = pd.concat([index_data, index_df])
    
    calculateVwapSignal()
    signal = getLatestSignal()
    return signal

def calculateVwapSignal():
    global index_data
    ## change index of data to its date column
    index_data.index = index_data['date']
    
    ## calculate vwap for banknifty
    index_data["typical_price"] = (index_data["high"] + index_data["low"] + index_data["close"] + index_data['open']) / 4
    index_data["cumulated_price_volume"] = (index_data["typical_price"] * index_data["volume"]).cumsum()
    index_data["cumulated_volume"] = index_data["volume"].cumsum()
    index_data["vwap"] = index_data["cumulated_price_volume"] / index_data["cumulated_volume"]
    
    ## calculate vwap std bands
    std_dev = 2 * index_data["vwap"].rolling(window=len(index_data), min_periods = 1).std()
    num_std_dev = 1
    index_data["upper_band1"] = index_data["vwap"] + (num_std_dev * std_dev)
    index_data["lower_band1"] = index_data["vwap"] - (num_std_dev * std_dev)

    num_std_dev = 2
    index_data["upper_band2"] = index_data["vwap"] + (num_std_dev * std_dev)
    index_data["lower_band2"] = index_data["vwap"] - (num_std_dev * std_dev)
    return

def getLatestSignal():
    global index_data
    ## calculate signals
    signal_arr = []
    for i, data in index_data.iterrows():
        signal = 0
        if data['close'] > data['lower_band1'] and data['open'] < data['lower_band1']:
            signal = 1
        elif data['close'] < data['upper_band1'] and data['open'] > data['upper_band1']:
            signal = -1
        elif data['close'] < data['lower_band1'] and data['open'] > data['lower_band1']:
            signal = -1
        elif data['close'] > data['upper_band1'] and data['open'] < data['upper_band1']:
            signal = 1
        signal_arr.append(signal)
    index_data['signal'] = signal_arr
    return signal_arr[-1]






















##########################################################################
####################      KITE CONNECT LOGIC HERE     ####################
##########################################################################
prev_download_time = timenow_         
index_data = pd.DataFrame()



## if launched after market open, download data till now
if prev_download_time > market_open_time:
    start_time_ = time.perf_counter()
    curr_signal = downloadDataAndCalculateSignal(start_time = market_open_time, end_time = prev_download_time)
    end_time_ = time.perf_counter()
    prf_time = end_time_ - start_time_
    logger.info("SIGNAL, %s", curr_signal)
    logger.info("PRF, %s(seconds) from %s to %s", prf_time, market_open_time, prev_download_time)
    prev_download_time = market_open_time
    



# logger.info("Sleeping for 60 seconds .....")
# time.sleep(60) ## sleep for 1 minute
# logger.info("Continuing ..... ")

#### this loop can be used to write signal calculation logic
while True:
    curr_time = datetime.datetime.now()
    
    if curr_time > market_close_time:
        logger.info("Market Closed, Exiting.....!!")
        kws.stop()
        break
    
    elif curr_time < market_open_time:
        logger.info("Market Not Open, Waiting....!!")
    
    elif curr_time.second >= 59:
        start_time_ = time.perf_counter()
        logger.info("Calculating signal ...... ")
        
        ## time is XX:XX:59 seconds. Download data, and update signal flag        
        curr_signal = downloadDataAndCalculateSignal(start_time = prev_download_time, end_time = curr_time)
        prev_download_time = curr_time
        logger.info("SIGNAL, %s", curr_signal)
        
        if not curr_signal == 0:
            
            atm_strike, atm_call_syminfo, atm_put_syminfo, atm_call_token, atm_put_token = utility.findAtmStrike(float(index_data.iloc[-1].close), syminfo)
            
            if curr_signal == 1:
                logger.info("BULLISH SIGNAL, %s", atm_call_syminfo['tradingsymbol'].to_string(index = False))
                
                ## if we have positions in CE options, we can skip this signal
                if not positionHandler_.doExistSymbol(OptionType.CALL.value):
                    call_symbol = Symbol(atm_call_syminfo)
                    
                    call_symbol.stop_loss_pct = stop_loss_pct
                    call_symbol.trailing_stop_loss_pct = trailing_stop_loss_pct
                    call_symbol.target_pct = target_pct
                    call_symbol.trailing_target_pct = trailing_target_pct
                    call_symbol.is_valid_symbol = True
                    #subscribe to this option
                    kiteWebSocket.addSymbolToSubscriptionList(tokens_, atm_call_token)
                    kiteWebSocket.subscribeToSymbol(kws, atm_call_token, kws.MODE_LTP)

                    #send buy order for this option, with stop loss
                    positionHandler_.addSymbolToHandler(OptionType.CALL.value, call_symbol)

                else:
                    logger.info("Ignoring signal, already in a trade")

            else:
                logger.info("BEARISH SIGNAL, %s", atm_put_syminfo['tradingsymbol'].to_string(index = False))
                
                ## if we have positions in PE options, we can skip this signal
                if not positionHandler_.doExistSymbol(OptionType.PUT.value):
                    put_symbol = Symbol(atm_put_syminfo)
                    
                    put_symbol.stop_loss_pct = stop_loss_pct
                    put_symbol.trailing_stop_loss_pct = trailing_stop_loss_pct
                    put_symbol.target_pct = target_pct
                    put_symbol.trailing_target_pct = trailing_target_pct
                    put_symbol.is_valid_symbol = True
                    #subscribe to this option
                    kiteWebSocket.addSymbolToSubscriptionList(tokens_, atm_put_token)
                    kiteWebSocket.subscribeToSymbol(kws, atm_put_token, kws.MODE_LTP)

                    #send buy order for this option, with stop loss
                    positionHandler_.addSymbolToHandler(OptionType.PUT.value, put_symbol)
                else:
                    logger.info("Ignoring signal, already in a trade")
        
        end_time_ = time.perf_counter()
        prf_time = end_time_ - start_time_
        logger.info("PRF: %s(seconds)", prf_time)
        logger.info("PNL %s %s %s %s %s", positionHandler_.n_trades, positionHandler_.n_win_trades, positionHandler_.n_lose_trades, sum(positionHandler_.pnl), sum(positionHandler_.net_pnl))

    ## can do calculations like pnl, input output, etc here
    logger.debug("PNL %s %s %s %s %s", positionHandler_.n_trades, positionHandler_.n_win_trades, positionHandler_.n_lose_trades, sum(positionHandler_.pnl),  sum(positionHandler_.net_pnl))
    time.sleep(0.5)
    