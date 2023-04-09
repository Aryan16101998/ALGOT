from logger import logger
from symbol import Side

BROKERAGE_PER_TRADE = 20

# get instrument info data
def getInstrumentInfo(kite):
    instrument_list = kite.instruments()
    return instrument_list

## eturn index syminfo, and index_token as int
def getIndexInfo(instrument_df, index_name):
    index_syminfo = instrument_df[(instrument_df['tradingsymbol'] == index_name)]
    index_token = int(index_syminfo['instrument_token'].to_string(index = False))
    return index_token, index_syminfo

def getLotSize(syminfo):
    lot_size = 0
    for index, syminfo_ in syminfo.iterrows():
        lot_size = int(syminfo_['lot_size'])
        if lot_size > 0:
            return lot_size
    return lot_size

def findAtmStrike(ltp, syminfo):
    atm_strike = float(ltp)
    abs_diff = 99999999
    
    for index, syminfo_ in syminfo.iterrows():
        curr_strike = float(syminfo_['strike'])
        if curr_strike == 0.0:
            continue
        if abs(curr_strike - float(ltp)) < abs_diff:
            atm_strike = curr_strike
            abs_diff = abs(curr_strike - float(ltp))

    atm_call_syminfo = syminfo[(syminfo['strike'] == atm_strike) & (syminfo['instrument_type'] == 'CE')]
    atm_put_syminfo = syminfo[(syminfo['strike'] == atm_strike) & (syminfo['instrument_type'] == 'PE')]
    atm_call_token = int(atm_call_syminfo['instrument_token'].to_string(index = False))
    atm_put_token = int(atm_put_syminfo['instrument_token'].to_string(index = False))
    logger.info("findAtmStrike, atm_strike %s, atm_call_token %s, atm_put_token %s", atm_strike, atm_call_token, atm_put_token)
    logger.info("findAtmStrike, atm_call_syminfo \n%s\n atm_put_syminfo \n%s", atm_call_syminfo, atm_put_syminfo)
    return atm_strike, atm_call_syminfo, atm_put_syminfo, atm_call_token, atm_put_token

def calcPnlForSymbol(symbol):
    pnl = 0
    pnl = symbol.fill_value[Side.SELL.value] - symbol.fill_value[Side.BUY.value]
    pnl += (symbol.ltp * symbol.net_pos)
    symbol.pnl = pnl
    return pnl

def calcCostForSymbol(symbol): 
    brokerage = sum(symbol.trade_count) * BROKERAGE_PER_TRADE
    stt = symbol.fill_value[Side.SELL.value] * 0.05 * 0.01
    stamp_charges = symbol.fill_value[Side.BUY.value] * 0.003 * 0.01
    sebi_charges = sum(symbol.fill_value) * 10 * 0.0000001
    txn_charges = sum(symbol.fill_value) * 0.053 * 0.01
    gst = 0.18 * (brokerage + sebi_charges  + txn_charges)
    cost = brokerage + stt + stamp_charges + sebi_charges + txn_charges + gst 
    symbol.cost = cost
    return cost