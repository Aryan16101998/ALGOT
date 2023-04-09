import kiteconnect
import webbrowser
import os
import datetime
from logger import logger

class KiteSession:
    API_KEY = "zz11c9b75jz200r1"
    def generateAccessToken(self):
        API_SECRET = "bxbs2p2jh25zh9eotvwbx8dukxyx30y3"
        REQUEST_TOKEN_URL = self.kite.login_url()
        print("Making request for token.....")
        webbrowser.open(REQUEST_TOKEN_URL)
        request_token = input("Enter the request token from the browser: ")
        print("Got Response: " + request_token)
        kite_session = self.kite.generate_session(request_token, api_secret=API_SECRET)
        return kite_session["access_token"]
    

    def __init__(self):
        today_date = datetime.date.today()
        token_filename = "access_token" + today_date.strftime('%Y%m%d')
        curr_dir = os.getcwd()
        isSessionExist = os.path.exists(curr_dir + token_filename)
        self.kite = kiteconnect.KiteConnect(api_key=self.API_KEY)
        ## use already existing token if present, else login and create a new token for the day
        if isSessionExist:
            with open(curr_dir + token_filename, "r") as file_:
                REQUEST_TOKEN = file_.read()
        else:
            REQUEST_TOKEN = self.generateAccessToken()
            with open(curr_dir + token_filename, "w") as file_:
                file_.write(str(REQUEST_TOKEN))
    
        self.kite.set_access_token(REQUEST_TOKEN)
        self.kws = kiteconnect.KiteTicker(self.API_KEY, REQUEST_TOKEN)
        
