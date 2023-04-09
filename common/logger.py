import logging
import datetime
# Create a new logger object
logger = logging.getLogger()

# Configure the logger with your desired settings
logger.setLevel(logging.DEBUG)


today = datetime.date.today()
todayStr = today.strftime("%Y-%m-%d")
# Create a file handler
fh = logging.FileHandler('strat_logs' + todayStr + '.log')
fh.setLevel(logging.DEBUG)

# Create a stream handler
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s,[%(levelname)s],%(message)s')

fh.setFormatter(formatter)
sh.setFormatter(formatter)

logger.addHandler(sh)
logger.addHandler(fh)