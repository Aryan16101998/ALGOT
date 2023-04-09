import sys
## import common packages
sys.path.append('../common')
from symbol import Side, Symbol
from logger import logger
import utility

class PositionHandler():
    symbols_ = []
    max_inv = 0
    pnl  = []
    cost = []
    net_pnl = []
    n_trades = 0
    n_win_trades = 0
    n_lose_trades = 0

    def __init__(self, max_inv):
        self.symbols_.append(Symbol())
        self.symbols_.append(Symbol())
        self.max_inv = max_inv
        self.pnl = []
        self.cost = []
        self.net_pnl = []
        self.n_trades = 0
        self.n_win_trades = 0
        self.n_lose_trades = 0

    def addSymbolToHandler(self, type, symbol):
        self.symbols_[type] = symbol
        logger.info("ADDED SYMBOL TO HANDLER")
        logger.info("%s %s %s", symbol.name, symbol.fill_qty[Side.BUY.value], symbol.fill_qty[Side.SELL.value])
    
    def removeSymbolFromHandler(self, type):
        self.symbols_[type].is_valid_symbol = False
        logger.info("SYMBOL REMOVED FROM HANDLER")
        logger.info("%s %s", self.symbols_[type].name, self.symbols_[type].is_valid_symbol)

    def getSymbolFromHandler(self, type):
        return self.symbols_[type]
    
    def doExistSymbol(self, type):
        return self.symbols_[type].is_valid_symbol
        
    
    def on_ticks(self, token, ltp):
        for sym_type, symbol in enumerate(self.symbols_):
            sym_id =  symbol.token if symbol.is_valid_symbol else 0
            if sym_id == token:
                self.symbols_[sym_type].ltp = ltp
                return True
        return False
    
    def onMarketData(self):
        ## for each symbol we need to do following steps:
        ## 1. if we don't have position -> send order
        ## 2. if we have position
        ##      a. if stop loss order standing
        ##          i. check for trailing condition
        ##      b. if no stop loss order standing
        ##          i. send a stop loss order

        logger.debug("CURRENT_HANDLER_STATUS:")
        for symbol in self.symbols_:
            if symbol.is_valid_symbol:
                logger.debug("%s", symbol.name)   
        
        syms_to_remove = []
        for sym_type in range(len(self.symbols_)):
            symbol = self.symbols_[sym_type]

            net_pos = symbol.net_pos
            
            if symbol.ltp  == 0 or not symbol.is_valid_symbol: 
                continue
            
            if net_pos == 0:
                order_qty = self.max_inv
                order_qty -= symbol.fill_qty[Side.BUY.value]
                order_qty -= symbol.inflight_qty[Side.BUY.value]
                symbol.order_qty = order_qty
                logger.info("GET_ORDER_QTY %s %s, %s, %s, %s", symbol.name,  symbol.order_qty, self.max_inv, symbol.fill_qty[Side.BUY.value], symbol.inflight_qty[Side.BUY.value])
                #### now send order for this symbol here itself
                # self.sendMarketOrder(symbol)
                if order_qty > 0:
                    symbol.inflight_qty[Side.BUY.value] += order_qty
                    
                    ############ for testing purpose only #########################
                    #### assuming that we got fill at ltp itself
                    symbol.fill_qty[Side.BUY.value] = order_qty
                    symbol.net_pos = order_qty
                    symbol.inflight_qty[Side.BUY.value] = 0
                    symbol.avg_price[Side.BUY.value] = symbol.ltp
                    symbol.fill_value[Side.BUY.value] = symbol.ltp * order_qty
                    symbol.trade_count[Side.BUY.value] += 1
                    symbol.stop_loss_price = symbol.avg_price[Side.BUY.value] * ( 1 - symbol.stop_loss_pct / 100)
                    symbol.target_price = symbol.avg_price[Side.BUY.value] * ( 1 + symbol.target_pct / 100)
                    symbol.to_send_stop_loss_order = True
                    logger.info("BUY %s at %s, qty %s", symbol.name, symbol.avg_price[Side.BUY.value], symbol.fill_qty[Side.BUY.value])
                ############ testing code finish here #########################
            
            
            elif net_pos > 0:
                
                if symbol.to_send_stop_loss_order:
                    #### now send stop loss order for this symbol
                    #  self.sendStopLossOrder(symbol)
                    symbol.to_send_stop_loss_order = False ## made false here, need to make it True if SL order is not placed

                    ############ for testing purpose only #########################
                    #### assuming that we have sent the stop loss order now
                    logger.info("STOP_LOSS_ORDER, NEW, %s at %s, TARGET AT %s", symbol.name, symbol.stop_loss_price , symbol.target_price)
                    symbol.stop_loss_order_standing = True
                    ############ testing code finish here #########################
                
                elif symbol.stop_loss_order_standing:
                    
                    ############ for testing purpose only #########################
                    ## in prod, this part will be handled by different function
                    is_stop_loss_hit = (symbol.ltp <= symbol.stop_loss_price)
                    if is_stop_loss_hit:
                        logger.info("STOP_LOSS_HIT, %s %s %s", symbol.name, symbol.stop_loss_price, symbol.ltp)
                        ## stop loss hit, assuming that our position will be closed at stop loss price
                        symbol.fill_qty[Side.SELL.value] = symbol.fill_qty[Side.BUY.value]
                        symbol.net_pos = 0
                        symbol.avg_price[Side.SELL.value] = symbol.stop_loss_price
                        symbol.fill_value[Side.SELL.value] = symbol.stop_loss_price * symbol.fill_qty[Side.SELL.value]
                        symbol.trade_count[Side.SELL.value] += 1
                        pnl = utility.calcPnlForSymbol(symbol)
                        cost = utility.calcCostForSymbol(symbol)
                        net_pnl = pnl - cost
                        logger.info("POSITION CLOSED %s %s %s %s %s %s", symbol.name, symbol.avg_price[Side.BUY.value], symbol.avg_price[Side.SELL.value], pnl, cost, net_pnl)
                        self.pnl.append(pnl)
                        self.cost.append(cost)
                        self.net_pnl.append(net_pnl)
                        self.n_trades += 1
                        if net_pnl > 0:
                            self.n_win_trades += 1
                        else:
                            self.n_lose_trades += 1
                        syms_to_remove.append(sym_type)
                    ############ testing code finish here #########################

                    else:
                        #### now check if trailing target is met or not    
                        #### for various strategies we might need to change only this part, whether to check target hit or not
                        is_target_hit = (symbol.ltp >= symbol.target_price)
                        if is_target_hit:
                            logger.info("TARGET_HIT, %s %s %s", symbol.name, symbol.target_price, symbol.ltp)
                            symbol.stop_loss_price = symbol.target_price * ( 1 - symbol.trailing_stop_loss_pct / 100)
                            symbol.target_price = symbol.target_price * ( 1 + symbol.trailing_target_pct / 100)

                            #### now modify existing stop loss order
                            # self.modifyStandingStopLossOrder(symbol)

                            ############ for testing purpose only #########################
                            #### assuming that we have sent the stop loss order now
                            logger.info("STOP_LOSS_ORDER, MODIFY, %s to %s, and new target: %s", symbol.name, symbol.stop_loss_price, symbol.target_price)
                            ############ testing code finish here #########################
        self.symbols_[sym_type] = symbol

        return syms_to_remove
                    

