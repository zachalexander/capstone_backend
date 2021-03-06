from flask import Flask, session, request, jsonify, render_template, redirect, url_for, make_response;
from flask_session import Session
from flask_cors import CORS, cross_origin
from flask import jsonify
import math
import random
import requests
import json
import time
import os
from markupsafe import escape
from flask_sqlalchemy import SQLAlchemy;
from sqlalchemy import event, create_engine, inspect, DDL
from sqlalchemy.dialects.postgresql import UUID
import uuid
from uuid import uuid1
import urllib.request as urllib2
from urllib.parse import quote
import json
from dotenv import load_dotenv
import pandas as pd

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import SessionNotCreatedException
import modsim
from modsim import *
import math
import psycopg2
import base64

from bs4 import BeautifulSoup
from googlesearch import search as gsearch
import re
import timeit

from fake_headers import Headers
import itertools

load_dotenv()
app = Flask(__name__)

ENV = 'prod'

LOCAL_DB_URL = 'postgresql://postgres:NewYork512@localhost:5432/capstone'
REMOTE_DB_URL = 'postgres://zqeqylqmnbbtsq:9752c59faf5674de11c547657c271f826781f010d7a3355e4a7a644a62c8d5ac@ec2-3-217-219-146.compute-1.amazonaws.com:5432/dcghtng3l8p37g'

# Setting database configs
if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = LOCAL_DB_URL
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = REMOTE_DB_URL

# app.config['SQL_ALCHEMY_TRACK_MODIFICATIONS'] = False

# app.config['SECRET_KEY'] = SECRET_KEY

SECRET_KEY = b'_5#t2L"F7Q8x\n\xec]/'
CORS(app)

db = SQLAlchemy(app)

# Building user model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(UUID(as_uuid=True), default=uuid.uuid4())
    address = db.Column(db.String(200), primary_key=True)
    sqr_footage = db.Column(db.Integer)
    panel_area = db.Column(db.Integer)
    azimuth = db.Column(db.Integer)
    year_built = db.Column(db.Integer)
    household_members = db.Column(db.Integer)
    ratio = db.Column(db.Numeric)

    def __init__(self, address, sqr_footage, panel_area, azimuth, year_built, household_members, ratio):
        self.address = address
        self.sqr_footage = sqr_footage
        self.panel_area = panel_area
        self.azimuth = azimuth
        self.year_built = year_built
        self.household_members = household_members
        self.ratio = ratio

class SunRoof(db.Model):
    __tablename__ = 'sunroof'
    address = db.Column(db.String(200), primary_key=True)
    estimate = db.Column(db.Integer)
    screenshot = db.Column(db.LargeBinary)

    def __init__(self, address, estimate, screenshot):
        self.address = address
        self.estimate = estimate
        self.screenshot = screenshot

class Realtor(db.Model):
    __tablename__ = 'realtor'
    address = db.Column(db.String(200), primary_key=True)
    square_footage_house = db.Column(db.Integer)
    year_built = db.Column(db.Integer)
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)

    def __init__(self, address, square_footage_house, year_built, bedrooms, bathrooms):
        self.address = address
        self.square_footage_house = square_footage_house
        self.year_built = year_built
        self.bedrooms = bedrooms
        self.bathrooms = bathrooms

def user_id(address):
    if db.session.query(User).filter(User.address == address).count() == 0:
        pass
    else:
        idquery = db.session.query(User).filter(User.address == address).first()
        idquery_old = idquery.id
        return idquery_old


@app.route('/calc/<address>', methods=['GET'])
def model(address):

    try:

        if (db.session.query(User).filter(User.address == address).count() == 0):
            return jsonify('We could not locate the input data')
        else:
            user_inputs = db.session.query(User).filter(User.address == address).first()
            
        
            ##### START OF MISHA'S CODE #####
        
            #############################################################################################
            ### Inputs we will need to get from the front-end:
            sqft = user_inputs.sqr_footage
            roof_sqft = user_inputs.panel_area
            HHM = user_inputs.household_members
            roof_azimuth = user_inputs.azimuth
            roof_m = float(roof_sqft) * 0.092903
            Year_Blt = user_inputs.year_built
            ratio_update = user_inputs.ratio
            price = 0.1174

            #coordinates of Albany, NY (29.42412, -98.49363)
            la=29.42412
            lo=-98.49363


            #Daily_bool below directs whether to use stock Albany data or pull from NSRDB API (True = stock)
            daily_bool = True

            #### FUNCTION DECLARATIONS ####


            #############################################################################################
            ### If necessary (daily_bool = False), pull data from NSRDB
            #############################################################################################

            def collect_ghi(la, lo):
                api_key = 'BUnBQIpFlpJZcCcqO2VeYuUMXjX7zCSGiVBNIIdH'
                attributes = 'ghi'
                year = '2019'
                lat, lon = la, lo
                leap_year = 'false'
                interval = '60'
                utc = 'false'
                name = 'Misha+Kollontai'
                reason= 'school_project'
                affiliation = 'CUNY+SPS'
                email = 'mkollontai@gmail.com'
                mailing_list = 'false'
                
                #combine all of the relevant information into the API-specified URL
                url = 'https://developer.nrel.gov/api/solar/nsrdb_psm3_download.csv?wkt=POINT({lon}%20{lat})&names={year}&leap_day={leap}&interval={interval}&utc={utc}&full_name={name}&email={email}&affiliation={affiliation}&mailing_list={mailing_list}&reason={reason}&api_key={api}&attributes={attr}'.format(year=year, lat=lat, lon=lon, leap=leap_year, interval=interval, utc=utc, name=name, email=email, mailing_list=mailing_list, affiliation=affiliation, reason=reason, api=api_key, attr=attributes)
                
                GHI_raw = pd.read_csv(url,skiprows = 2)
                #Set the index to the proper timestamps
                GHI_raw = GHI_raw.set_index(pd.date_range('1/1/{yr}'.format(yr=year), freq=interval+'Min', periods=525600/int(interval)))
                temp = GHI_raw[['Month','Day','GHI']]
                daily = temp.groupby(['Month','Day']).sum()
                monthly_mean = daily.groupby(['Month']).mean()
                monthly_sd = daily.groupby(['Month']).std()
                monthly_ghi = pd.DataFrame(monthly_mean)
                monthly_ghi['STD'] = monthly_sd['GHI']
                
                print(monthly_ghi.to_json())


            #############################################################################################
            ### If necessary (daily_bool = False), pull data from NSRDB
            #############################################################################################

            def define_system(A=80,PR=0.8,lat=29.42412,long=-98.49363, azim = 1):
                '''Create a system object defining our solar panel system
                '''
                start = State(P = 0, C = 0, Y=0)
                t0 = 0
                '''15 years worth of operation'''
                t_end = sim_years*12

                return System(start=start, t0=t0, t_end=t_end, A=A, PR=PR, lat=lat, long=long, azim = azim)


            #############################################################################################
            ####   We must calculate the amount of power generated on on a given day by the panels. 
            ####   This number is influenced by the surface area of the panels, their efficiency, 
            ####   performance ratio and amount of exposure to sun they receive on that day. In our 
            ####   estimation of GHI on a given day, we will assume a normal distribution given the 
            ####   mean and stDev from the table we pulled from the NSRDB. The formula used below to 
            ####   calculate the actual yield is taken from 
            ####   (https://photovoltaic-software.com/principle-resources/how-calculate-solar-energy-power-pv-systems) 
            ####   with the 'Annual average' value replaced with the GHI per day value calculated from the NSRDB data. 
            #############################################################################################
            ####   Function to determine the daily yield of the panels   ################################
            #############################################################################################
            ###      system     - pre-defined system defining the panels
            ###      month      - the month (1-12) for which the GHI is to be estimated
            ###      day        - the day of the month
            ###      daily_bool - whether or not we are using the stock Albany data or 2019 localized (T = stock data)
            #############################################################################################

            def days_yield(system,month,day,daily_bool):
                if daily_bool:
                    ghi_day = np.random.normal(Albany_GHI.at[(month,day),'Mean'],Albany_GHI.at[(month,day),'StDev'])
                else:
                    ghi_day = np.random.normal(monthly_ghi.iloc[month-1]['GHI'],monthly_ghi.iloc[month-1]['STD'])
                ghi_day = float(ghi_day)
                if ghi_day < 0:
                    ghi_day = 0
                return (system.A*ghi_day*system.PR*system.azim)/1000

            def find_ratio(sqft, year_blt):
                #Sqft Lookup
                # should be set to zero if no info is available
                if sqft == 0:
                    sqft_col = 0
                elif sqft > 3499:
                    sqft_col = 6
                else:
                    sqft_col = math.floor((sqft-1000)/500+2)
                sqft_rat = SQFT_Ratio.iloc[0, sqft_col]

                # Year_Built Lookup
                # should be set to zero if no info is available
                if year_blt == 0:
                    year_col = 0
                else: 
                    if year_blt < 1940:
                        year_col = 1
                    else:
                        year_col = math.floor((year_blt-1950)/10+2)
                year_rat = YearBuilt_Ratio.iloc[0,year_col]

                # Household Member
                # should be set to zero if no info is available
                if HHM == 0:
                    hhm_col = 0
                elif HHM > 6:
                    hhm_col = 6
                else:
                    hhm_col = HHM
                hhm_rat = HHM_Ratio.iloc[0,hhm_col]

                ratio = sqft_rat * year_rat * hhm_rat
                return ratio


            def month_demand_norm(month,sqft=0,year=0, hhm=0):

                ratio = find_ratio(sqft, year)               
                demand_month = Albany_Monthly_Use.iloc[month-1,0] * ratio * float(ratio_update)
                return demand_month


            #############################################################################################
            ####    Function calculating the balance at the end of a month ##############################
            #############################################################################################

            def calc_month(system, month):
                #2% yearly increase in electricity rates
                yearly_increase = 1.02
                year = math.floor(month/12)

                month_mod = (month % 12)
                if month_mod == 0:
                    month_mod = 12
                    
                if month_mod in [1,3,5,7,8,10,12]:
                    days = 31
                elif month_mod in [4,6,9,11]:
                    days = 30
                elif month_mod == 2:
                    days = 28
                else:
                    print("Not a valid month number")
                    return None
                
                yld = 0
                gain = 0

                pr_fac = yearly_increase**year * price
                
                #make sure if we don't have year or sqft they are set to proper values for default calc
                loss = month_demand_norm(month_mod,sqft,Year_Blt, HHM) * pr_fac
                
                for day in range(1,days+1):
                    yld  = yld + days_yield(system,month_mod,day,daily_bool)
                
                gain = yld * pr_fac

                this_month = State(P = gain, C = loss, Y = yld)
                return this_month
                
            #############################################################################################


            def update_fxn(state,system,month):
                '''Update the pos/neg/balance model.

                state: State with variables PB, FB, C
                system: System with relevant info
                '''
                p, c, y = state

                month_result = calc_month(system, month)

                p += month_result.P
                c += month_result.C
                y = month_result.Y

                return State(P = p, C = c, Y = y)


            ############################################################################################

            ####   The function below generates three TimeSeries objects over the time interval specified 
            ###    within the provided time interval. The TimeSeries track number of months with a positive 
            ##     balance, number of months with a negative balance and the overall balance throughout 
            #      the intervals
                
            def run_simulation(system,upd_fxn):
                """Take a system as input and unpdate it based on the update function.

                system - system object defining panels
                update_fxn - function describing change to system 

                returns - Timeseries
                """
                P = TimeSeries()
                C = TimeSeries()
                Y = TimeSeries()

                state = system.start
                t0 = system.t0
                P[t0], C[t0], Y[t0] = state

                for t in linrange(system.t0, system.t_end):
                    state = upd_fxn(state,system,t)
                    P[t+1], C[t+1], Y[t+1] = state

                return P, -C, Y
                
            #############################################################################################
            

            #############################################################################################
            ### Depending on the 'daily_bool' variable, use stock Albany solar data or pull from NSRDB
            if daily_bool:
                ## Data from the NSRDB. Daily data for Albany coordinates going back to 1998
                #  To be used as default data instead of querying the API
                Albany_GHI = pd.read_csv('./datafiles/Albany_GHI_Data.csv')
                Albany_GHI = Albany_GHI[['Month','Day','Mean','StDev']]
                Albany_GHI = Albany_GHI.set_index(['Month','Day'])
            else:
                ## Use the function above to pull data on the coordinates in question
                monthly_ghi = pd.read_json(collect_ghi(la,lo))


            ### Data we pull locally
            Albany_Monthly_Use = pd.read_csv('./datafiles/Albany Monthly Average Use.csv')
            Albany_Monthly_Use = Albany_Monthly_Use.set_index(['Month'])
            HHM_Ratio = pd.read_csv('./datafiles/Northeast_HHM_Ratios.csv')
            YearBuilt_Ratio = pd.read_csv('./datafiles/Northeast_Year_Ratios.csv')
            SQFT_Ratio = pd.read_csv('./datafiles/Northeast_SQFT_Ratios.csv')


            #%%timeit
            #convert sq ft to sq m
            roof_A = float(roof_sqft) * 0.092903
            sim_years = 15
            #############################################################################################
            ### equation for azimuth_factor below explained at:
            ##  https://docs.google.com/spreadsheets/d/13UL_QRR396G7L1IOa9wtQAjv24xCWA5So69pHfMEGI0/edit?usp=sharing
            #   Equation of form: a + bx + cx^2 + dx^3 + ex^4
            a = 0.995
            b = 0
            c = -2.69e-5
            d = 0
            e = 3.24e-10
            azimuth_factor = a + (b*roof_azimuth) + (c*roof_azimuth**2) + (d*roof_azimuth**3) + (e*roof_azimuth**4)
            #############################################################################################

            low_r_bound = 0.15
            high_r_bound = 0.19
            low_initial_cost = 12000
            high_initial_cost = 20000

            cap_1 = "I=$" + str(int(high_initial_cost/1000)) + "k, r="+ str(low_r_bound)
            cap_2 = "I=$" + str(int(high_initial_cost/1000)) + "k, r="+ str(high_r_bound)
            cap_3 = "I=$" + str(int(low_initial_cost/1000)) + "k, r="+ str(low_r_bound)
            cap_4 = "I=$" + str(int(low_initial_cost/1000)) + "k, r="+ str(high_r_bound)

            #############################################################################################
            ### 4 systems below cover the range of initial costs (15k & 25k) as well as efficiency ranges (17.5% & 20%)
            ##  Can be adjusted to plot desired systems

            system = define_system(A=roof_A, lat=la, long=lo, azim= azimuth_factor)
            P, C, Y = run_simulation(system,update_fxn)
            FB = (P*low_r_bound - high_initial_cost) + C
            FB2 = (P*high_r_bound - high_initial_cost) + C
            FB3 = (P*low_r_bound - low_initial_cost) + C
            FB4 = (P*high_r_bound - low_initial_cost) + C

            ### Combining the data from four systems above
            projection = pd.concat([FB,FB2,FB3,FB4,C], axis =1)
            #############################################################################################
  
            #############################################################################################
            ### Column names below need to be either adjusted to match or automated to cover plotted systems

            #!#!#!#! Need to deal with these names potentially changing along with the systems #!#!#!#

            projection.columns = [cap_1,cap_2,cap_3,cap_4,'Regular Grid Service']
            year = [i/12 for i in range(12*sim_years+1)]
            projection['year'] = list(year)
            projection.set_index('year', inplace = False)
            projection[cap_1 + '_value'] = projection[cap_1] - projection['Regular Grid Service']
            projection[cap_2 + '_value'] = projection[cap_2] - projection['Regular Grid Service']
            projection[cap_3 + '_value'] = projection[cap_3] - projection['Regular Grid Service']
            projection[cap_4 + '_value'] = projection[cap_4] - projection['Regular Grid Service']

            value = projection[::12]
            #############################################################################################


            #############################################################################################
            #### Finding the intersection of each of the 4 systems with the 'Regular Grid Service'
            ###  'intersect' list contains 4 entries - the month at which each system intersects
            ##   Even_pt_hi/lo rounds the lowest and highest intersection points to years
            #    Series names need to match column names above
            intersect = []
            find_60 = []
            test1 = 1
            test2 = 1
            test3 = 1
            test4 = 1
            test60_1 = 1
            test60_2 = 1
            test60_3 = 1
            test60_4 = 1
            for i,r in projection.iterrows():
                if r[cap_1] > r['Regular Grid Service'] and test1:
                    intersect.append(i)
                    test1 = 0
                if r[cap_2] > r['Regular Grid Service'] and test2:
                    intersect.append(i)
                    test2 = 0
                if r[cap_3] > r['Regular Grid Service'] and test3:
                    intersect.append(i)
                    test3 = 0
                if r[cap_4] > r['Regular Grid Service'] and test4:
                    intersect.append(i)
                    test4 = 0
                if (r['Regular Grid Service']-r[cap_1])/high_initial_cost < 0.4 and test60_1:
                    find_60.append(i)
                    test60_1 = 0
                if (r['Regular Grid Service']-r[cap_2])/high_initial_cost < 0.4 and test60_2:
                    find_60.append(i)
                    test60_2 = 0
                if (r['Regular Grid Service']-r[cap_3])/low_initial_cost < 0.4 and test60_3:
                    find_60.append(i)
                    test60_3 = 0
                if (r['Regular Grid Service']-r[cap_4])/low_initial_cost < 0.4 and test60_4:
                    find_60.append(i)
                    test60_4 = 0

            if (intersect == []):
                break_even_range = 0
                even_pt_hi = None
                even_pt_lo = None
            else:
                break_even_range = 1
                even_pt_lo = math.ceil(min(intersect)/12)
                even_pt_hi = math.ceil(max(intersect)/12)

        
            low_yearly_yield = []
            high_yearly_yield = []
            Y_monthly = pd.DataFrame(Y, columns = ['Yield'])
            Y_monthly = Y_monthly.iloc[1:, :]
            month_idx = [1,2,3,4,5,6,7,8,9,10,11,12]
            months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            Y_monthly = Y_monthly.assign(Month = month_idx * sim_years)

            for i in range(0, Y.shape[0]):
                if (i%12 == 0) & (i != 0):
                    low_yearly_yield.append(sum(Y[i-12:i]) * low_r_bound)
                    high_yearly_yield.append(sum(Y[i-12:i]) * high_r_bound)
            Y_monthly = Y_monthly.groupby(['Month']).mean()

            Y_monthly= Y_monthly.groupby(['Month']).mean()
            Y_monthlyL = Y_monthly.copy()
            Y_monthlyL['Yield'] = Y_monthlyL['Yield'] * low_r_bound
            Y_monthlyL['Efficiency'] = 'Low'
            Y_monthlyH = Y_monthly.copy()
            Y_monthlyH['Yield'] = Y_monthlyH['Yield'] * high_r_bound
            Y_monthlyH['Efficiency'] = 'High'
            Y_month = Y_monthlyL.append(Y_monthlyH)
            Y_month = Y_month.sort_values(by=['Month'])
            Y_month = Y_month.reset_index()
            Y_month = Y_month.pivot_table(index=["Month"], columns='Efficiency', values='Yield')

            ratio = find_ratio(sqft, Year_Blt)
            energy_usage = Albany_Monthly_Use['Usage'] * ratio * float(ratio_update)
            energy_usage = pd.DataFrame({'usage': energy_usage})
            energy_usage = energy_usage.reset_index()

            tot_energy = pd.merge(energy_usage, Y_month, how="left", on=["Month"])
            # tot_energy = tot_energy.pivot(index='Month',columns='usage')[['Yield','Efficiency']]

            display = projection.to_dict(orient="records")
            value_display = value.to_dict(orient="records")
            tot_energy = tot_energy.to_dict(orient="records")

            print('model successfully ran!')
            #############################################################################################
              
        ##### FINAL RETURN JSON #####

        # response = jsonify(display)

        payload = {
            'model_data': display,
            'high': even_pt_hi,
            'low': even_pt_lo,
            'value_data': value_display,
            'energy_data': tot_energy
        }

        response = jsonify(payload)
        response.headers.add('Access-Control-Allow-Origin', '*')

        return response
        
    except (Exception, ValueError, KeyError, TypeError, IndexError) as ex:
        print(ex)
        response = jsonify('an error occurred while running the model!')
    return response


@app.route('/coords', methods=['POST'])
def selenium_check():
    if request.method == "POST":
        coordinates = request.get_json()
        jsonify(coordinates)

        coords_json = [
            {
                "latitude": coordinates['latitude'],
                "longitude": coordinates['longitude'],
                "address": coordinates['address']
            }
        ]

        json.dumps(coords_json)

        # if db.session.query(SunRoof).filter(SunRoof.address == coords_json[0]['address']).count() == 0:
        #     print('not in sunroof db!')

        #     CHROMEDRIVER_PATH = "/app/.chromedriver/bin/chromedriver"
        #     chrome_bin = os.environ.get('GOOGLE_CHROME_BIN', None)

        #     options = webdriver.ChromeOptions()
        #     options.binary_location = chrome_bin
        #     options.add_argument("--disable-gpu")
        #     options.add_argument("--no-sandbox")
        #     options.add_argument("--headless")
        #     options.add_argument('--disable-dev-shm-usage')
        #     options.add_argument('--remote-debugging-port=9222')
        #     options.add_argument('--disable-infobars')

        #     try: 

        #         # FOR PROD
        #         driver = webdriver.Chrome(executable_path=os.environ.get('CHROMEDRIVER_PATH'), chrome_options=options)
                
        #         # # FOR DEV
        #         # driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
                
        #         driver.set_window_size(800,1000)

        #         # chrome_options = Options()
        #         # chrome_options.add_argument("headless")
         

        #         driver.get('https://www.google.com/get/sunroof/building/' + str(coords_json[0]['latitude']) + '/' + str(coords_json[0]['longitude']) + '/#?f=buy')
                
        #         # square_footage_available = [e.text for e in driver.find_elements_by_css_selector('.recommended-area')]
        #         square_footage_available = [e.text for e in driver.find_elements_by_css_selector('.panel-fact-text')]

        #         if square_footage_available:
                    
        #             square_footage_available = square_footage_available[1]
        #             square_footage_available = square_footage_available.split(' ')
        #             square_footage_available = square_footage_available[0]
        #             square_footage_available = ''.join(e for e in square_footage_available if e.isdigit() or e == '.')
        #             square_footage_available = int(square_footage_available) / 2

        #             js_string = "let element = document.body.getElementsByClassName(\"main-content\")[0].getElementsByClassName(\"section-map\")[0].getElementsByClassName(\"address-map-panel\")[0].remove();document.body.getElementsByClassName(\"header-wrap\")[0].style.visibility = 'hidden';document.body.getElementsByClassName(\"main-content-wrapper\")[0].style['margin'] = '0px';document.body.getElementsByClassName(\"section-inner\")[0].style.visibility = 'hidden';"
        #             driver.execute_script(js_string)
        #             driver.execute_script("document.body.style.zoom='450%'")
        #             time.sleep(2)

        #             image_filename = "map_test.png"
        #             driver.save_screenshot(image_filename)
        #             driver.quit()

        #             if square_footage_available != "":
        #                 with open("map_test.png", "rb") as image:
        #                     f = image.read()
        #                     b = bytearray(f)

        #                     if (db.session.query(SunRoof).filter(SunRoof.address == coords_json[0]['address']).count() == 0):
        #                         sunroof_estimate = SunRoof(coords_json[0]['address'], square_footage_available, b)
        #                         db.session.add(sunroof_estimate)
        #                         db.session.commit()
        #                     else:
        #                         sunroof_estimate = db.session.query(SunRoof).filter(SunRoof.address == coords_json[0]['address']).first()
        #                         setattr(sunroof_estimate, square_footage_available, b)
        #                         db.session.commit()
        #                     print('sunroof data successfully in db!')
        #             else:
        #                 print('cannot locate project sunroof data!')
        #         else:
        #             print('cannot locate project sunroof data!')

        #     except (TimeoutException, SessionNotCreatedException) as ex:
        #         print('Timeout or Session Not Created Error!')

        #     # now check realtor db
        #     if db.session.query(Realtor).filter(Realtor.address == coords_json[0]['address']).count() == 0:
        #         print('not in realtor db!')
        #         realtor_add_list = coords_json[0]['address'].split(', ')

        #         address = realtor_add_list[0]
        #         city = realtor_add_list[1]
        #         state = "NY"

        #         searches = []
        #         query = address +" "+city +", "+state+" Realtor.com"
        #         for j in gsearch(query):
        #             result = j
        #             searches.append(result)
                
        #         headers = Headers(os="mac", headers=True).generate()

        #         response=requests.get(searches[0],headers=headers)

        #         soup=BeautifulSoup(response.content,'lxml')

        #         if (soup.find('li',attrs = {'data-label': 'property-meta-beds'}) == None and soup.select_one('li[data-label="pc-meta-beds"]') != None):
        #             home_bed = int(soup.find('li', attrs={'data-label': 'pc-meta-beds'}).find('span',attrs={'data-label': 'meta-value'}).contents[0])
        #             home_bath = float(soup.find('li', attrs={'data-label': 'pc-meta-baths'}).find('span',attrs={'data-label': 'meta-value'}).contents[0])
        #             sqft_info = soup.find('li', attrs={'data-label': 'pc-meta-sqft'}).find('span',attrs={'data-label': 'meta-value'}).contents[0]
        #             home_sqft = int(sqft_info.replace(',',''))

        #             if (soup.find_all('li', attrs={'class': 'jsx-488154125 col-xs-6 col-md-4 indicator'}) != None):
        #                 child_soup = soup.find_all('li', attrs={'class': 'jsx-488154125 col-xs-6 col-md-4 indicator'})
        #                 text = 'Year Built'
        #                 for i in child_soup:
        #                     if(i.find('span', attrs={'class': 'jsx-488154125 key'}).string == text):
        #                         year_built = int(i.find('span', attrs={'class': 'jsx-488154125 value ellipsis'}).string)
        #             else:
        #                 print('cannot locate year built info!')
                        
        #             if (home_sqft != None and year_built != None and home_bed != None and home_bath != None):
        #                 realtor_estimate = Realtor(coords_json[0]['address'], home_sqft, year_built, home_bed, home_bath)
        #                 db.session.add(realtor_estimate)
        #                 db.session.commit()
        #                 print('successfully saved realtor data!')

        #         elif (soup.select_one('li[data-label="property-meta-beds"]') != None):
        #             home_bed = int(soup.select_one('li[data-label="property-meta-beds"]').find_all("span", class_="data-value")[0].contents[0])
        #             home_bath = float(soup.select_one('li[data-label="property-meta-bath"]').find_all("span", class_="data-value")[0].contents[0])
        #             sqft_info= soup.select_one('li[data-label="property-meta-sqft"]').find_all("span", class_="data-value")[0].contents[0]
        #             home_sqft = int(sqft_info.replace(',',''))

        #             if soup.select_one('li[data-label="property-year"]') == None:
        #                 child_soup = soup.find_all('li', attrs={'class': 'jsx-488154125 col-xs-6 col-md-4 indicator'})
        #                 text = 'Year Built'
        #                 for i in child_soup:
        #                     if(i.find('span', attrs={'class': 'jsx-488154125 key'}).string == text):
        #                         year_built = int(i.find('span', attrs={'class': 'jsx-488154125 value ellipsis'}).string)

        #                         if (home_sqft != None and year_built != None and home_bed != None and home_bath != None):
        #                             realtor_estimate = Realtor(coords_json[0]['address'], home_sqft, year_built, home_bed, home_bath)
        #                             db.session.add(realtor_estimate)
        #                             db.session.commit()
        #                             print('successfully saved realtor data!')
        #             else:
        #                 year_built = int(soup.select_one('li[data-label="property-year"]').find_all("div", class_="key-fact-data ellipsis")[0].contents[0])

        #             if (home_sqft != None and year_built != None and home_bed != None and home_bath != None):
        #                 realtor_estimate = Realtor(coords_json[0]['address'], home_sqft, year_built, home_bed, home_bath)
        #                 db.session.add(realtor_estimate)
        #                 db.session.commit()
        #                 print('successfully saved realtor data!')
                
        #         else:
        #             print('cannot locate realtor data!')
        #             pass
        #     else:
        #         print('already in realtor but not sunroof!')
        # else:
        #     print('already in sunroof!')
        #     if db.session.query(Realtor).filter(Realtor.address == coords_json[0]['address']).count() == 0:
        #         print('already in sunroof but not realtor!')
        #         realtor_add_list = coords_json[0]['address'].split(', ')

        #         address = realtor_add_list[0]
        #         city = realtor_add_list[1]
        #         state = "NY"

        #         searches = []
        #         query = address +" "+city +", "+state+" Realtor.com"
        #         for j in gsearch(query):
        #             result = j
        #             searches.append(result)

        #         headers = Headers(os="mac", headers=True).generate()   
        #         response=requests.get(searches[0], headers=headers)

        #         soup=BeautifulSoup(response.content,'lxml')
        #         # house_data = soup.find(id="ldp-property-meta")

        #         if (soup.find('li',attrs = {'data-label': 'property-meta-beds'}) == None and soup.select_one('li[data-label="pc-meta-beds"]') != None):
        #             home_bed = int(soup.find('li', attrs={'data-label': 'pc-meta-beds'}).find('span',attrs={'data-label': 'meta-value'}).contents[0])
        #             home_bath = float(soup.find('li', attrs={'data-label': 'pc-meta-baths'}).find('span',attrs={'data-label': 'meta-value'}).contents[0])
        #             sqft_info = soup.find('li', attrs={'data-label': 'pc-meta-sqft'}).find('span',attrs={'data-label': 'meta-value'}).contents[0]
        #             home_sqft = int(sqft_info.replace(',',''))

        #             if (soup.find_all('li', attrs={'class': 'jsx-488154125 col-xs-6 col-md-4 indicator'}) != None):
        #                 child_soup = soup.find_all('li', attrs={'class': 'jsx-488154125 col-xs-6 col-md-4 indicator'})
        #                 text = 'Year Built'
        #                 for i in child_soup:
        #                     if(i.find('span', attrs={'class': 'jsx-488154125 key'}).string == text):
        #                         year_built = int(i.find('span', attrs={'class': 'jsx-488154125 value ellipsis'}).string)
        #             else:
        #                 print('cannot locate year built info!')
                        
        #             if (home_sqft != None and year_built != None and home_bed != None and home_bath != None):
        #                 realtor_estimate = Realtor(coords_json[0]['address'], home_sqft, year_built, home_bed, home_bath)
        #                 db.session.add(realtor_estimate)
        #                 db.session.commit()
        #                 print('successfully saved realtor data!')

        #         elif (soup.select_one('li[data-label="property-meta-beds"]') != None):
        #             home_bed = int(soup.select_one('li[data-label="property-meta-beds"]').find_all("span", class_="data-value")[0].contents[0])
        #             home_bath = float(soup.select_one('li[data-label="property-meta-bath"]').find_all("span", class_="data-value")[0].contents[0])
        #             sqft_info= soup.select_one('li[data-label="property-meta-sqft"]').find_all("span", class_="data-value")[0].contents[0]
        #             home_sqft = int(sqft_info.replace(',',''))

        #             if soup.select_one('li[data-label="property-year"]') == None:
        #                 child_soup = soup.find_all('li', attrs={'class': 'jsx-488154125 col-xs-6 col-md-4 indicator'})
        #                 text = 'Year Built'
        #                 for i in child_soup:
        #                     if(i.find('span', attrs={'class': 'jsx-488154125 key'}).string == text):
        #                         year_built = int(i.find('span', attrs={'class': 'jsx-488154125 value ellipsis'}).string)

        #                         if (home_sqft != None and year_built != None and home_bed != None and home_bath != None):
        #                             realtor_estimate = Realtor(coords_json[0]['address'], home_sqft, year_built, home_bed, home_bath)
        #                             db.session.add(realtor_estimate)
        #                             db.session.commit()
        #                             print('successfully saved realtor data!')
        #             else:
        #                 year_built = int(soup.select_one('li[data-label="property-year"]').find_all("div", class_="key-fact-data ellipsis")[0].contents[0])

        #             if (home_sqft != None and year_built != None and home_bed != None and home_bath != None):
        #                 realtor_estimate = Realtor(coords_json[0]['address'], home_sqft, year_built, home_bed, home_bath)
        #                 db.session.add(realtor_estimate)
        #                 db.session.commit()
        #                 print('successfully saved realtor data!')
        #         else:
        #             print('cannot locate realtor data!')
        #     else:
        #         print('already in realtor!')
        #         print('address found in both databases!')
            
    response = jsonify('success')
    return response

@app.route('/posts', methods=['POST'])
def post_input():
    if request.method == 'POST':

        frontend_input = request.get_json()
        jsonify(frontend_input)

        if db.session.query(User).filter(User.address == frontend_input['address']).count() == 0:
            user = User(frontend_input['address'], frontend_input['house_footage'], frontend_input['panel_area'], frontend_input['azimuth'], frontend_input['year_built'], frontend_input['household_members'], frontend_input['ratio'])
            db.session.add(user)
            db.session.commit()
        else:
            user = db.session.query(User).filter(User.address == frontend_input['address']).first()
            setattr(user, 'sqr_footage', frontend_input['house_footage'])
            setattr(user, 'panel_area', frontend_input['panel_area'])
            setattr(user, 'azimuth', frontend_input['azimuth'])
            setattr(user, 'year_built', frontend_input['year_built'])
            setattr(user, 'household_members', frontend_input['household_members'])
            setattr(user, 'ratio', frontend_input['ratio'])
            db.session.commit()

    response = jsonify('success')
    response.headers.add('Access-Control-Allow-Origin', '*')

    return response

@app.route('/scraped-data/<address>', methods=['GET'])
def getSunroof_data(address):
    final_response = None
    if request.method == 'GET':
        if db.session.query(SunRoof).filter(SunRoof.address == address).count() == 0:
            if db.session.query(Realtor).filter(Realtor.address == address).count() == 0:
                response = jsonify(
                    {
                        'estimate': None,
                        'screenshot': None, 
                        'square_footage': None,
                        'year_built': None,
                        'bedrooms': None,
                        'bathrooms': None,
                        'status': 'could not locate sunroof or realtor data!'
                    }
                )
                response.headers.add('Access-Control-Allow-Origin', '*')
                final_response = response
            else:
                realtor_data = db.session.query(Realtor).filter(Realtor.address == address).first()

                response = jsonify(
                    {
                        'estimate': None, 
                        'screenshot': None, 
                        'square_footage': realtor_data.square_footage_house,
                        'year_built': realtor_data.year_built,
                        'bedrooms': realtor_data.bedrooms,
                        'bathrooms': realtor_data.bathrooms,
                        'status': 'could not locate sunroof or realtor data!'
                    }
                )
                response.headers.add('Access-Control-Allow-Origin', '*')
                final_response = response
        else:
            estimate = db.session.query(SunRoof).filter(SunRoof.address == address).first()

            byte_image = estimate.screenshot
            base64EncodedStr = base64.b64encode(byte_image)
            final_str = 'data:image/jpeg;base64,' + base64EncodedStr.decode('utf-8')

            if db.session.query(Realtor).filter(Realtor.address == address).count() == 0:
                response = jsonify(
                    {
                        'estimate': estimate.estimate,
                        'screenshot': final_str, 
                        'square_footage': None,
                        'year_built': None,
                        'bedrooms': None,
                        'bathrooms': None,
                        'status': 'could not locate sunroof or realtor data!'
                    }
                )
                response.headers.add('Access-Control-Allow-Origin', '*')
                final_response = response
            else:
                realtor_data = db.session.query(Realtor).filter(Realtor.address == address).first()

                response = jsonify(
                    {
                        'estimate': estimate.estimate, 
                        'screenshot': final_str, 
                        'square_footage': realtor_data.square_footage_house,
                        'year_built': realtor_data.year_built,
                        'bedrooms': realtor_data.bedrooms,
                        'bathrooms': realtor_data.bathrooms,
                        'status': 'found both sunroof and realtor data!'
                    }
                )
                response.headers.add('Access-Control-Allow-Origin', '*')
                final_response = response
    return final_response

if __name__ == '__main__':
    app.run(debug=True)