import pandas as pd
import requests
from datetime import date, datetime,timedelta
from bs4 import BeautifulSoup
import json
import zipfile, io
import yfinance as yf

current_date = date.today()

class NSEData:
    '''
    Class to open NSE data
    '''
    def __init__(self):
        '''
        '''
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'connection': 'keep-alive'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.base_url = "https://www.nseindia.com"
        self.cookies = {}
        self._setup_session()

    def _setup_session(self):
        try:
            # First request to get cookies
            response = self.session.get(
                "https://www.nseindia.com/get-quotes/equity?symbol=SBIN",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                self.cookies = response.cookies
                print("Session setup successful")
            else:
                print(f"Failed to setup session. Status code: {response.status_code}")
                
            # Update headers with common tokens
            self.session.headers.update({
                'referer': 'https://www.nseindia.com/get-quotes/equity?symbol=SBIN',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
            })
            
        except Exception as e:
            print(f"Error setting up session: {str(e)}")

    def get_stock_data(self, symbol, days=30):
        """
        Get stock data using NSE APIs
        """
        try:
            # Clean up symbol
            symbol = symbol.replace('.NS', '').strip().upper()
            
            # Try to get historical data
            url = f"https://www.nseindia.com/api/historical/cm/equity?symbol={symbol}&series=[%22EQ%22]&from={date.today() - timedelta(days=days)}&to={date.today()}"
            
            response = self.session.get(
                url,
                headers=self.headers,
                cookies=self.cookies,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    df = pd.DataFrame(data['data'])
                    # Rename columns to match expected format
                    df = df.rename(columns={
                        'CH_TIMESTAMP': 'DATE',
                        'CH_OPENING_PRICE': 'OPEN',
                        'CH_TRADE_HIGH_PRICE': 'HIGH',
                        'CH_TRADE_LOW_PRICE': 'LOW',
                        'CH_CLOSING_PRICE': 'CLOSE',
                        'CH_TOT_TRADED_QTY': 'VOLUME'
                    })
                    return df
                
            # If historical data fails, try quote data
            quote_url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
            quote_response = self.session.get(
                quote_url,
                headers=self.headers,
                cookies=self.cookies,
                timeout=10
            )
            
            if quote_response.status_code == 200:
                quote_data = quote_response.json()
                if 'priceInfo' in quote_data:
                    # Create single row DataFrame with current data
                    current_data = {
                        'DATE': pd.Timestamp.now(),
                        'OPEN': quote_data['priceInfo']['open'],
                        'HIGH': quote_data['priceInfo']['intraDayHighLow']['max'],
                        'LOW': quote_data['priceInfo']['intraDayHighLow']['min'],
                        'CLOSE': quote_data['priceInfo']['lastPrice'],
                        'VOLUME': quote_data['priceInfo']['totalTradedVolume']
                    }
                    return pd.DataFrame([current_data])
            
            print(f"Failed to fetch data for {symbol}")
            return None
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return None

    def get_market_status(self):
        """
        Get market status with proper headers
        """
        try:
            url = "https://www.nseindia.com/api/marketStatus"
            response = self.session.get(
                url,
                headers=self.headers,
                cookies=self.cookies,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            print(f"Failed to get market status. Status code: {response.status_code}")
            return None
            
        except Exception as e:
            print(f"Error fetching market status: {str(e)}")
            return None

    def get_indices_data(self):
        """
        Get all indices data
        """
        try:
            url = "https://www.nseindia.com/api/allIndices"
            response = self.session.get(
                url,
                headers=self.headers,
                cookies=self.cookies,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            print(f"Error fetching indices data: {str(e)}")
            return None

    def get_fno_list(self):
        """
        Get list of F&O stocks
        """
        try:
            url = "https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20F%26O"
            response = self.session.get(
                url,
                headers=self.headers,
                cookies=self.cookies,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    return [stock['symbol'] for stock in data['data']]
            return None
            
        except Exception as e:
            print(f"Error fetching F&O list: {str(e)}")
            return None

    def get_stock_quote(self, symbol):
        """
        Get real-time stock quote
        """
        try:
            url = f"{self.base_url}/api/quote-equity?symbol={symbol}"
            response = self.session.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching quote for {symbol}: {str(e)}")
            return None

    def get_live_nse_data(self, url:str):
        '''
        Get Live market data available on NSE website as PDF
        args:
           url: corresponding url
        '''
        response = self.session.get(url, headers=self.headers, cookies=self.cookies)
        return response
    

    def current_indices_status(self,show_n:int=5):
        '''
        Get current status of all the available indices. It could be pre, dyring or post market. Will tell how much each index or sector moved as other details
        args:
            show_n: Show top N sorted by ABSOLUTE % change Values such that -3.2 will be shown first than 2.3
        '''
        df = pd.DataFrame(self.get_live_nse_data("https://www.nseindia.com/api/allIndices").json()['data'])
        df['absolute_change'] = df['percentChange'].apply(lambda x: abs(x))
        df.sort_values('absolute_change',ascending=False, inplace=True)
        return df.iloc[:show_n,[1,5,0,4]]
    
    
    def open_nse_index(self,index_name:str,show_n:int=10, drop_index:bool = True):
        '''
        Open the current index. DataFrame with all the members of the index and theit respective Open, High, Low, Percentange chnge etc etc
        args:
            index_name: Name of the Index such as NIFTY 50, NIFTY Bank, NIFTY-IT etc
            show_n: Show top N sorted by ABSOLUTE % change Values such that -3.2 will be shown first than 2.3
            driop_index: Whether to drop the Index Value row itsels
        '''
        index_name = index_name.replace(' ','%20')
        index_name = index_name.replace(':','%3A')
        index_name = index_name.replace('/','%2F')
        index_name = index_name.replace('&','%26')

        url = f"https://www.nseindia.com/api/equity-stockIndices?index={index_name}"

        resp = self.get_live_nse_data(url)
        
        df = pd.DataFrame(resp.json()['data'])
        df['absolute_change'] = df['pChange'].apply(lambda x: abs(x))
        # df['Index'] = df['symbol'].apply(lambda x: In.get_index(x))
        df.sort_values('absolute_change',ascending=False, inplace=True)
        
        if drop_index: df.drop(0,inplace = True) # Drop the index name
        return df.iloc[:show_n,[1,9,3,4,5,6,-1]]
        

    def get_VIX(self, whole_data:bool = False):
        '''
        Get the Volatility Index Value. 
        Read more at: 
        https://tradebrains.in/india-vix/
        https://www.motilaloswal.com/blog-details/6-things-that-the-Volatility-Index-(VIX)-indicates-to-you../1929
        args:
            whole_data: Get the Whole Current +  historical data of VIX
        '''
        result = self.get_live_nse_data('https://www1.nseindia.com/live_market/dynaContent/live_watch/VixDetails.json').json()
        if whole_data:
            return result
        print(f"Current VIX: {result['currentVixSnapShot'][0]['CURRENT_PRICE']}")


    def fifty_days_data(self, symbol:str):
        '''
        Get Historical Data for each equity for the past 50 trading days
        args:
            symbol: Listed name of the stock on NSE
        '''
        url = f"https://www.nseindia.com/api/historical/cm/equity?symbol={symbol}&series=[%22EQ%22]&from={self.from_}&to={self.to}"
        result = self.get_live_nse_data(url = url)
        df = pd.DataFrame(result.json()['data'])
        df.columns = df.columns.map({'CH_SYMBOL':'SYMBOL',"CH_TRADE_HIGH_PRICE":"HIGH","CH_TRADE_LOW_PRICE":"LOW","CH_OPENING_PRICE":"OPEN","CH_CLOSING_PRICE":"CLOSE",
                "CH_TIMESTAMP":"DATE","CH_52WEEK_LOW_PRICE":"52W L","CH_52WEEK_HIGH_PRICE":"52W H"})

        df = df.loc[:,["DATE","OPEN","HIGH","LOW","CLOSE","52W H","52W L","SYMBOL"]] # to match previous API's Columns and structure
        return df


    def stocks_at_52W(self, direction:str = 'high' ):
        '''
        Get stocks trading currently at their 52W High / Low
        args:
            direction: direction of 52 Week. 'high', 'low'
        '''
        x = self.get_live_nse_data(f'https://www.nseindia.com/api/live-analysis-52Week?index={direction}')
        return pd.concat([pd.DataFrame(x.json()['dataLtpGreater20']), pd.DataFrame(x.json()['dataLtpLess20'])],ignore_index = True)

    
    
class MarketSentiment:
    '''
    Get the market sentiment based on TICK, TRIN etc
    '''
    def check_fresh_data(self):
        '''
        Get fresh updated data scraped from the website https://www.traderscockpit.com/?pageView=live-nse-advance-decline-ratio-chart
        '''
        page = requests.get('https://www.traderscockpit.com/?pageView=live-nse-advance-decline-ratio-chart')
        soup = BeautifulSoup(page.content, "lxml")
        latest_updated_on = soup.find("span", {"class": "hm-time"})
        divs = soup.find_all("div", {"class": "col-sm-6"})
        return divs, latest_updated_on
    
    
    def get_TRIN(self, divs):
        '''
        Get the TRIN or so called Arm's Index of the market at any given point of time. Gives the market sentiment along with TICK. TRIN < 1 is Bullishh and  TRIN > 1 is bearish.
        Values below 0.5 or greater than 3 shows Overbought and Oversold zone respectively. Check: https://www.investopedia.com/terms/a/arms.asp
        args:
            divs: Div elements scraped from website
        returns:
             dictonary of volume in Millions of shares for inclining or declining stocks along with the TRIN value
        '''
        self.volume_up = float(divs[4].text[1:-1])
        self.volume_down = float(divs[5].text[1:-1])
        
        self.trin = float(divs[3].find('h4').text.split(' ')[-1].split(':')[-1][:-1])
        return {'Volume Up':self.volume_up, 'Volume Down': self.volume_down, 'TRIN': self.trin}
    
    
    def get_TICK(self, divs):
        '''
        Get the TICK data for live market. TICK is the difference between the gaining stocks and losing stocks at any point in time. Show nmarket sentiment and health along with TRIN.           Buy/ Long Position if TRIN is > 0; sell/short otherwise
        args:
            divs: BeautifulSoup object of all the div elements.
        returns: Dictonary showing stocks which are up/ down corresponding to LAST tick traded value along with the differene betwwn no of stocks and no of stocks down
        '''
        self.stock_up = int(divs[1].text.split(' ')[-1][:-1])
        self.stock_down = int(divs[2].text.split(' ')[-1][:-1])

        self.tick = self.stock_up - self.stock_down
        return {'Up':self.stock_up, "Down":self.stock_down, 'TICK':self.tick}
    
    
    def get_high_low(self, divs):
        '''
        Get no of stocks trading at 52 Week high or 52 week low at any given point of time
        args:
            divs: BeautifulSoup object of all the div elements
        returns: Dictonary of no of stocks trading at high and low
        '''  
        high = int(divs[7].find('p').text.split(' ')[-1])
        low = int(divs[8].find('p').text.split(' ')[-1])

        return {'52W High':high, "52W Low":low}

    
    def get_live_sentiment(self, print_analysis:bool = True):
        '''
        Get the live sentiment of market based on TICK and TRIN
        args:
            print_analysis: Whether to print only the analysis
        '''
        result = {}
        divs, latest_updated_on = self.check_fresh_data()
        
        result['Latest Updated on'] =  latest_updated_on.text[7:]
        result.update(self.get_TICK(divs))
        result.update(self.get_TRIN(divs))
        result.update(self.get_high_low(divs))

        if print_analysis:
            tick = result['TICK']
            trin = result['TRIN']
            tick_sentiment = 'Bullish' if tick > 0 else "Bearish"
            trin_sentiment = 'Bullish' if trin < 1 else "Bearish"
            if trin > 3:
                print(f'Currently Bearish but may reverse soon due to TRIN value {trin} > 3')

            if trin < 0.5:
                print(f'Currently Bullish but may reverse soon due to TRIN value {trin} < 0.5')

            if tick < 0 and trin > 1:
                print(f"Pure Bearish due to negative tick {tick} and TRIN {trin} > 1")

            if tick > 0 and trin < 1:
                print(f"Pure Bullish due to positive tick {tick} and TRIN {trin} < 1")

            if (tick > 0 and trin > 1) or (tick < 0 and trin < 1):
                print(f"Watch out as TICK {tick} {tick_sentiment} and TRIN {trin} {trin_sentiment} have opposite sentiments")

        return result
    

def get_mmi(raw = False):
    '''
    All credits to https://www.tickertape.in/market-mood-index. Please refer to the link
    args:
        raw: Whether to return the raw json of data for MMI
    '''
    url = "https://www.tickertape.in/market-mood-index"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "lxml")


    script = soup.find_all('script' ,{"id":"__NEXT_DATA__"})[0]
    values = json.loads(script.string)['props']['pageProps']['nowData']
    current = values['currentValue']
    last_day = values['lastDay']['indicator']
    last_week = values['lastWeek']['indicator']
    last_month = values['lastMonth']['indicator']
    
    if raw:
        return values
    
    if current < 30:
        print('Boom!!! You might want to Buy for Investment purpose. Market is in Extreme Fear')
        
    elif 30 < current < 50:
        print('Market is in Fear Zone. You might want it to go to Extreme Fear to start buying')
        
    elif 50 < current < 80:
        print('Market is in Greed zone! You might want to book profits. Keep yourself from taking new positions')
    
    elif current > 80:
        print("WARNING!!! You might want to book profits. Do not take fresh positions for Investment purpose now. Market is Extremely Greedy")
        

def get_Bhavcopy(start = None, no_days = 5):
    res = []
    if not start:
        start = current_date
        end = start - timedelta(days = no_days)
        
    for i in range(no_days):
        day = start - timedelta(days = i)
        try:
            r = requests.get(f'https://www1.nseindia.com/content/historical/EQUITIES/2022/JAN/cm{day}bhav.csv.zip')
            z = zipfile.ZipFile(io.BytesIO(r.content))
            z = z.open(z.namelist()[0])
            res.append(pd.read_csv(z))
        except:
            pass
    return res
