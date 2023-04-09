from enum import Enum
import pandas as pd
class OptionType(Enum):
    CALL = 0
    PUT = 1
    NONE = 2

class Side(Enum):
    BUY = 0
    SELL = 1

class OrderType(Enum):
    NONE = 0
    MARKET = 1
    LIMIT = 2

def getSideChar(side):
    if side == Side.BUY.value:
        return "B"
    else:
        return "S"

class Symbol():
    def __init__(self, syminfo = pd.DataFrame()):
        self.net_pos = 0
        self.order_id = [] ## id through which position was taken on this symbol
        self.fill_qty = []
        self.avg_price = []
        self.inflight_qty = []
        self.fill_value = []
        self.trade_count = []
        
        for i in range(2):
            self.avg_price.append(0)
            self.fill_qty.append(0)
            self.order_id.append(0)
            self.inflight_qty.append(0)
            self.fill_value.append(0)
            self.trade_count.append(0)

        self.syminfo = syminfo
        # self.type = OptionType.CALL if syminfo['instrument_type'].to_string(index = False) == 'CE' else (OptionType.PUT if syminfo['instrument_type'].to_string(index = False) == 'PE' else OptionType.NONE)
        self.token = int(syminfo['instrument_token'].to_string(index = False)) if len(syminfo) > 0 else 0
        self.name = (syminfo['tradingsymbol'].to_string(index = False)) if len(syminfo) > 0 else ""
        self.order_qty = 0
        self.order_price = 0

        self.to_send_stop_loss_order = False
        self.stop_loss_price = 0
        self.is_stop_loss_hit = False
        self.stop_loss_pct = 0
        self.trailing_stop_loss_pct = 0
        self.stop_loss_order_id = 0
        self.stop_loss_order_standing = False

        self.target_pct = 0
        self.trailing_target_pct = 0
        self.target_price = 0

        self.ltp = 0
        self.pnl = 0
        self.cost = 0
        self.is_valid_symbol = False
    
    