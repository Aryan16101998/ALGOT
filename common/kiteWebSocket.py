from logger import logger
tokens_  = []

def addSymbolToSubscriptionList(tokens_, token):
    tokens_.append(token)

def removeSymbolFromSubscriptionList(tokens_, token):
    tokens_.remove(token)

def subscribeToSymbol(ws, token, mode):
    tokens = [int(token)]
    ws.subscribe(tokens)
    ws.set_mode(mode, tokens)
    logger.info("Subscribe to token %s in mode %s", token, mode)

def subscribeToSymbols(ws, tokens, mode):
    ws.subscribe(tokens)
    ws.set_mode(mode, tokens)
    logger.info("Subscribe to tokens %s in mode %s", tokens, mode)

def unsubscribeSymbol(ws, token):
    tokens = [int(token)]
    ws.unsubscribe(tokens)
    logger.info("Unsubscribe to token %s", token)

# Callback for successful connection.
# on_connect - Triggered when connection is established successfully.
# response - Response received from server on successful connection.
def on_connect(ws, response):
    logger.info("Successfully connected. Response: {}".format(response))
    subscribeToSymbols(ws, tokens_, ws.MODE_LTP)

# Callback when current connection is closed.
# on_close(ws, code, reason) - Triggered when connection is closed.
# code - WebSocket standard close event code (https://developer.mozilla.org/en-US/docs/Web/API/CloseEvent)
# reason - DOMString indicating the reason the server closed the connection
def on_close(ws, code, reason):
    logger.info("Connection closed: {code} - {reason}".format(code=code, reason=reason))


# Callback when connection closed with error.
# on_error(ws, code, reason) - Triggered when connection is closed with an error.
# code - WebSocket standard close event code (https://developer.mozilla.org/en-US/docs/Web/API/CloseEvent)
# reason - DOMString indicating the reason the server closed the connection
def on_error(ws, code, reason):
    logger.error("Connection error: {code} - {reason}".format(code=code, reason=reason))

# Callback when reconnect is on progress
# on_reconnect(ws, attempts_count) - Triggered when auto reconnection is attempted.
# attempts_count - Current reconnect attempt number.
def on_reconnect(ws, attempts_count):
    logger.warn("Reconnecting: {}".format(attempts_count))


# Callback when all reconnect failed (exhausted max retries)
# on_noreconnect(ws) - Triggered when number of auto reconnection attempts exceeds reconnect_tries.
def on_noreconnect(ws):
    logger.error("Reconnect failed.")



# on_message(ws, payload, is_binary) - Triggered when message is received from the server.
# payload - Raw response from the server (either text or binary).
# is_binary - Bool to check if response is binary type.
def on_message(ws, payload, is_binary):
    if not is_binary:
        logger.info("Message received %d - %s", is_binary, payload)
