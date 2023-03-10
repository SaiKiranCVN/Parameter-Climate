import pandas as pd
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
from scipy.optimize import minimize
from datetime import timedelta
import plotly
import plotly.express as px



class Process:
    def __init__(self,data,df,df_xl):
        # Read Data
        print('In Init !!')
        self.df = df
        self.df_xl = df_xl
        self.MW_Notional = int(data.get('mwNotional'))
        self.Power_Price_Strike = int(data.get('strikeCallPrice'))
        self.futures_level = int(data.get('futuresLevel'))
        self.start_date = datetime.datetime.strptime(data.get('startDate')[:10],'%Y-%m-%d')
        self.end_date = datetime.datetime.strptime(data.get('endDate')[:10],'%Y-%m-%d')
        self.strikeCallPrice = int(data.get('strikeCallPrice'))
        self.tmaxs = self.compute_tmax([int(t) for t in data.get('monthlyData')])
        print('Init Done!!')

    def compute_tmax(self,tmaxs):
        current_date = self.start_date
        interval = timedelta(days=1)
        current_month = current_date.month
        tmx = 0
        tmax_array = []
        while current_date <= self.end_date:
            if current_date.month != current_month:
                current_month = current_date.month
                tmx += 1
            if tmx == len(tmaxs):
                break
            tmax_array.append(tmaxs[tmx])
            current_date += interval
        tmax_array.append(tmaxs[-1])
        return tmax_array





    def calculate_payout(self,df_slice,Power_Price_Strike=300):
        return self.MW_Notional * 1/12 * df_slice['Price'].apply(lambda x: max(x - Power_Price_Strike, 0))
    
    # Quanto
    def qcalculate_payout(self,df_slice,df_xl_slice,Power_Price_Strike=300):
        lambda_func = lambda x: max(x['Price'] - Power_Price_Strike, 0)
        df_slice['Only Date'] = df_slice['Only Date'].dt.normalize()
        sliced_prices = df_slice[['Price', 'Only Date']].apply(lambda_func, axis=1)
        while (len(self.tmaxs) != len(df_xl_slice['Tmax']) and len(self.tmaxs) > len(df_xl_slice['Tmax'])):
            self.tmaxs.pop()
        df_xl_slice['diff'] = df_xl_slice['Tmax'] - self.tmaxs
        sliced_temps = df_xl_slice[df_xl_slice['diff']>0]
        sliced_prices = sliced_prices[sliced_prices>0].to_frame()
        sliced_prices['Only Date'] = sliced_prices.index.date
        sliced_prices['Only Date'] = pd.to_datetime(sliced_prices['Only Date'])
        joined = pd.merge(sliced_prices,sliced_temps, how='inner', left_on='Only Date', right_on='Date')
        joined = joined.rename(columns={0: 'Price'})
        joined['Price'] = self.MW_Notional * 1/12 *joined['Price']
        return joined[['Price','Date']]

    def futures(self):
        self.df['yr'] = self.df['Only Date'].dt.year
        f_prices = self.df.groupby(by='yr')['Price'].mean()
        # Detrend the prices by dividing them by a linear trend
        trend = np.polyfit(range(len(f_prices)), f_prices, 1)[0]
        #Detrended
        dtrend = self.df['Price']/abs(trend)
        #Avg of annual averages
        a_yr_a = dtrend.mean()
        #factor 
        factor = self.futures_level/a_yr_a
        # Future Scaled
        scaled_prices = factor * dtrend
        print('Futures Done !!')
        return scaled_prices
    
    def xl_future(self):
        current_date = self.start_date
        interval = timedelta(days=1)
        pred = {}
        cr = []
        ag = []
        while current_date <= self.end_date:
            sm = 0
            cnt = 0
            t_date = current_date
            while True:
                ans = self.df_xl.loc[self.df_xl.index == str(t_date.date())]
                if t_date.year < 1997:
                    break
                if not ans.empty:
                    cnt += 1
                    sm += ans.iloc[0]['Tmax']

                # Increment the current date by 1 year
                t_date -= timedelta(days=365)
            avg = 0
            if cnt != 0:
                avg = sm/cnt 
            cr.append(current_date)
            ag.append(avg)
            #Next 5 min
            current_date += interval

        pred['Date'] = cr
        pred['Tmax'] = ag
        print('xl_future Done!!')
        return pd.DataFrame(pred) 


    def fiveMinPricesGivenDates(self,scaled_prices):
        current_date = self.start_date
        interval = timedelta(minutes=5)
        pred = {}
        cr = []
        ag = []
        while current_date <= self.end_date:
            sm = 0
            cnt = 0
            t_date = current_date
            while True:
                ans = scaled_prices.get(t_date,default=-1)
                if ans == -1 and t_date.year == 1997:
                    break
                if ans != -1:
                    cnt += 1
                    sm += ans

                # Increment the current date by 1 year
                t_date -= timedelta(days=365)
            if cnt != 0:
                avg = sm/cnt 
            cr.append(current_date)
            ag.append(avg)
            #Next 5 min
            current_date += interval

        pred['Date'] = cr
        pred['Price'] = ag
        print('fiveMinPricesGivenDates Done!!')
        return pd.DataFrame(pred) 


    def options(self):
        scaled_prices = self.futures() 
        df_slice = self.fiveMinPricesGivenDates(scaled_prices) # Only risk period
        vanila_payout = self.calculate_payout(df_slice)
        days_between = self.end_date - self.start_date 
        years = relativedelta(self.end_date, self.start_date)
        years = years.year
        anunal_historic_cap_price = vanila_payout.sum() / (24 * days_between.days)
        avg_anunal_historic_cap_price = anunal_historic_cap_price
        if years is not None: # year >= 1
            avg_anunal_historic_cap_price = anunal_historic_cap_price / years

        def difference(factor):
            nonlocal avg_anunal_historic_cap_price
            return avg_anunal_historic_cap_price * factor - self.strikeCallPrice
        result = minimize(difference, x0=1)

        # Extract the optimal multiplicative factor from the optimization result
        goal_seek_factor = result.x[0]    
        # Scale the 5-minutely prices by the goal seek factor
        df_slice['Price'] = goal_seek_factor * df_slice['Price']
        print('Options Done!!')
        return df_slice

    def payouts(self):
        df_slice = self.options()
        # Adding date col
        df_slice['Only Date'] = df_slice['Date']
        df_slice['Only Date'] = pd.to_datetime(df_slice['Only Date'])
        df_slice = df_slice.set_index('Date')
        vanila = self.calculate_payout(df_slice)
        df_xl_slice = self.xl_future()
        print('Future tmaxes')
        quanto = self.qcalculate_payout(df_slice,df_xl_slice)
        print('Payout Done!!')
        return vanila,quanto

    def plot(self):
        vanila,quanto = self.payouts()
        fig = px.bar(quanto, x='Date', y='Price',   
        barmode='group')
        graphJSON = plotly.io.to_json(fig, pretty=True)
        return graphJSON







