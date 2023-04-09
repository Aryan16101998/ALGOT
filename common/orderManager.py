from logger import logger
from symbol import Side, getSideChar

def sendMarketOrderForSymbol(kite, side, symbol, max_qty):
    txn_type = kite.TRANSACTION_TYPE_BUY if side == Side.BUY.value else kite.TRANSACTION_TYPE_SELL
    order_size = max_qty - symbol.fill_qty[side] - symbol.inflight_qty[side]
    if order_size <= 0:
        logger.info("NEW", "NOT_SENT", "MARKET_ORDER", symbol.syminfo['tradingsymbol'].to_string(index = False), getSideChar(side), "ZERO_QTY", max_qty, symbol.fill_qty[side], symbol.inflight_qty[side])
        return
    
    try:
        symbol.order_id[side] = kite.place_order(variety=kite.VARIETY_REGULAR,
                                    tradingsymbol=symbol.syminfo['tradingsymbol'],
                                    exchange=symbol.syminfo['exchange'],
                                    transaction_type=txn_type,
                                    quantity=order_size,
                                    order_type=kite.ORDER_TYPE_MARKET,
                                    product=kite.PRODUCT_MIS,
                                    validity=kite.VALIDITY_DAY)
    except Exception as e:
        logger.error("New Order placement failed: {}".format(e))
    else:
        logger.info("NEW", "MARKET_ORDER", symbol.order_id[side], symbol.syminfo['tradingsymbol'].to_string(index = False), getSideChar(side), order_size)
        symbol.inflight_qty[side] += order_size
        symbol.to_send_order = False
    return

def closePositions(kite, symbol):
    order_side = Side.SELL.value if symbol.net_pos > 0 else Side.BUY.value
    txn_type = kite.TRANSACTION_TYPE_BUY if order_side == Side.BUY.value else kite.TRANSACTION_TYPE_SELL

    order_size = symbol.net_pos - symbol.inflight_qty[order_side]
    if order_size <= 0:
        logger.info("NEW", "NOT_SENT", "MARKET_COVER_ORDER", symbol.syminfo['tradingsymbol'].to_string(index = False), "ZERO_QTY", order_size, symbol.net_pos, symbol.inflight_qty[order_side])
        return
    try:
        symbol.order_id[order_side] = kite.place_order(variety=kite.VARIETY_REGULAR,
                                        tradingsymbol=symbol.syminfo['tradingsymbol'],
                                        exchange=symbol.syminfo['exchange'],
                                        transaction_type=txn_type,
                                        quantity=order_size,
                                        order_type=kite.ORDER_TYPE_MARKET,
                                        product=kite.PRODUCT_MIS,
                                        validity=kite.VALIDITY_DAY)
    except Exception as e:
        logger.error("Cover Order placement failed: {}".format(e))
    else:
        logger.info("NEW", "MARKET_ORDER", symbol.order_id[order_side], symbol.syminfo['tradingsymbol'].to_string(index = False), getSideChar(order_side), order_size)
        symbol.inflight_qty[order_side] += order_size
        symbol.to_send_order = False
    return

