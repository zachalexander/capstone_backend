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
import pandas as pd
import modsim
from modsim import *
import math

load_dotenv()
app = Flask(__name__)

ENV = 'dev'

LOCAL_DB_URL = 'postgresql://postgres:NewYork512@localhost:5432/capstone'
REMOTE_DB_URL = os.getenv("REMOTE_DB_URL")

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

    def __init__(self, address, sqr_footage, panel_area, azimuth, year_built):
        self.address = address
        self.sqr_footage = sqr_footage
        self.panel_area = panel_area
        self.azimuth = azimuth
        self.year_built = year_built

class SunRoof(db.Model):
    __tablename__ = 'sunroof'
    address = db.Column(db.String(200), primary_key=True)
    estimate = db.Column(db.Integer)

    def __init__(self, address, estimate):
        self.address = address
        self.estimate = estimate

def user_id(address):
    if db.session.query(User).filter(User.address == address).count() == 0:
        pass
    else:
        idquery = db.session.query(User).filter(User.address == address).first()
        idquery_old = idquery.id
        return idquery_old


@app.route('/calc/<address>', methods=['GET'])
def model(address):

    if (db.session.query(User).filter(User.address == address).count() == 0):
        return jsonify('we could not locate the input data')
    else:
        user_inputs = db.session.query(User).filter(User.address == address).first()
        
       
        ##### START OF MISHAS CODE #####
    
        #############################################################################################
        ### Inputs we will need to get from the front-end:
        # sqft = 2400
        sqft = user_inputs.sqr_footage
        # roof_sqft = 850
        roof_sqft = user_inputs.panel_area

        #roof_azimuth angle needs to be from due South
        # roof_azimuth = 40
        roof_azimuth = user_inputs.azimuth
        roof_m = float(roof_sqft) * 0.092903

        # print(sqft)
        # print(roof_sqft)
        # print(roof_azimuth)
        # print(roof_m)

        #Daily_bool below directs whether to use stock Albany data or pull from NSRDB API (True = stock)
        daily_bool = True

        Year_Blt = user_inputs.year_built
        # Year_Blt = 1973
        price = 0.1827

        #coordinates of Albany, NY (29.42412, -98.49363)
        la=29.42412
        lo=-98.49363


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

        def define_system(A=80,r=0.175,PR=0.8,lat=29.42412,long=-98.49363,initial_cost=20000,azim=1):
            '''Create a system object defining our solar panel system'''
            start = State(MP = -initial_cost, C = 0)
            t0 = 0
            '''15 years worth of operation'''
            t_end = 15*12

            return System(start=start, t0=t0, t_end=t_end, A=A, r=r, PR=PR, lat=lat, long=long, azim = azim)


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
            return (system.A*system.r*ghi_day*system.PR*system.azim)/1000


        def month_demand_norm(month,sqft=0,year=0):
            #Sqft Lookup
            if sqft == 0:
                sqft_col = 0
            else:
                sqft_col = math.floor((sqft-1000)/500+2)
            sqft_month = SQFT_Ratios.iloc[month-1,sqft_col]
            
            #Year_Built Lookup
            if year == 0:
                year_col = 0
            else:
                year_col = math.floor((year-1950)/10+2)
            built_month = YearBuilt_Ratios.iloc[month-1,year_col]
            #std_d = tot_monthly * 0.15
            demand_month = (sqft_month+built_month)/2
            #if demand_month < 0:
            #    demand_month = 0
            return demand_month


        #############################################################################################
        ####    Function calculating the balance at the end of a month ##############################
        #############################################################################################

        def calc_month(system, month):
            #2% yearly increase in electricity rates
            yearly_increase = 1.02
            year = math.floor(month % 12)

            month_mod = (month % 12)+1
            if month_mod in [1,3,5,7,8,10,12]:
                days = 31
            elif month_mod in [4,6,9,11]:
                days = 30
            elif month_mod == 2:
                if year % 4 == 0:
                    days = 29
                else:
                    days = 28
            else:
                print("Not a valid month number")
                return None

            loss = month_demand_norm(month_mod,sqft,Year_Blt)
            #p = 0
            #n = 0
            balance = 0
            gain = 0

            pr = price * yearly_increase**year
            for day in range(1,days+1):
                gain  = gain + days_yield(system,month_mod, day,daily_bool)
            
            balance = (gain-loss)*pr 

            #if balance >= 0:
            #    p = 1
            #else:
            #    n = 1

            this_month = State(B = balance, C = loss*pr)
            return this_month
            
        #############################################################################################


        def update_fxn(state,system,month):
                '''Update the pos/neg/balance model. 
                state: State with variables PB, FB, C 
                system: System with relevant info
                '''
                b, c = state

                month_result = calc_month(system, month)

                #p += month_result.P
                #n += month_result.N
                #pb += month_result.B
                b += month_result.B
                c += month_result.C

                return State(B = b, C = c)


        ############################################################################################

        ####   The function below generates three TimeSeries objects over the time interval specified 
        ###    within the provided time interval. The TimeSeries track number of months with a positive 
        ##     balance, number of months with a negative balance and the overall balance throughout 
        #      the interval
            
        def run_simulation(system,upd_fxn):
            """Take a system as input and unpdate it based on the update function.

            system - system object defining panels
            update_fxn - function describing change to system 

            returns - Timeseries
            """
            #P = TimeSeries()
            #N = TimeSeries()
            #PB = TimeSeries()
            B = TimeSeries()
            C = TimeSeries()

            state = system.start
            t0 = system.t0
            B[t0], C[t0] = state

            for t in linrange(system.t0, system.t_end):
                state = upd_fxn(state,system,t)
                B[t+1], C[t+1] = state

            #return P, N, PB, FB, -C
            return B, -C
            
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
        HHM_Ratios = pd.read_csv('./datafiles/Albany Monthly Average Use - HHM.csv')
        YearBuilt_Ratios = pd.read_csv('./datafiles/Albany Monthly Average Use - YearBuilt.csv')
        SQFT_Ratios = pd.read_csv('./datafiles/Albany Monthly Average Use - Sqft.csv')

        HHM_Ratios = HHM_Ratios.set_index(['Month'])
        YearBuilt_Ratios = YearBuilt_Ratios.set_index(['Month'])
        SQFT_Ratios = SQFT_Ratios.set_index(['Month'])

        # print(HHM_Ratios)
        # print(YearBuilt_Ratios)
        # print(SQFT_Ratios)

        # convert sq ft to sq m
        roof_A = float(roof_sqft) * 0.092903

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

        print('google_azimuth', roof_azimuth)
        print('azimuth_factor', azimuth_factor)

        #############################################################################################


        #############################################################################################
        ### 4 systems below cover the range of initial costs (15k & 20k) as well as efficiency ranges (17.5% & 20%)
        ##  Can be adjusted to plot desired systems
        system = define_system(A=roof_A, lat=la, long=lo, initial_cost = 25000, r =.175, azim= azimuth_factor)
        FB, C = run_simulation(system,update_fxn)

        system2 = define_system(A=roof_A, lat=la, long=lo, initial_cost = 25000, r =.2, azim= azimuth_factor)
        FB2, C2 = run_simulation(system2,update_fxn) 

        system3 = define_system(A=roof_A, lat=la, long=lo, initial_cost = 15000, r =.175, azim= azimuth_factor)
        FB3, C3 = run_simulation(system3,update_fxn) 

        system4 = define_system(A=roof_A, lat=la, long=lo, initial_cost = 15000, r =.2, azim= azimuth_factor)
        FB4, C4 = run_simulation(system4,update_fxn) 

        ### Combining the data from four systems above
        projection = pd.concat([FB,FB2,FB3,FB4,C], axis =1)
        #############################################################################################

        #############################################################################################
        ### Column names below need to be either adjusted to match or automated to cover plotted systems

        #!#!#!#! Need to deal with these names potentially changing along with the systems #!#!#!#

        projection.columns = ['I=$25k, r=.175','I=$25k, r=.2','I=$15k, r=.175','I=$15k, r=.2','Regular Grid Service']
        #############################################################################################


        #############################################################################################
        #### Finding the intersection of each of the 4 systems with the 'Regular Grid Service'
        ###  'intersect' list contains 4 entries - the month at which each system intersects
        ##   Even_pt_hi/lo rounds the lowest and highest intersection points to years
        #    Series names need to match column names above
        intersect = []
        test1 = 1
        test2 = 1
        test3 = 1
        test4 = 1
        for i,r in projection.iterrows():
            if r['I=$25k, r=.175'] > r['Regular Grid Service'] and test1:
                intersect.append(i)
                test1 = 0
            if r['I=$25k, r=.2'] > r['Regular Grid Service'] and test2:
                intersect.append(i)
                test2 = 0
            if r['I=$15k, r=.175'] > r['Regular Grid Service'] and test3:
                intersect.append(i)
                test3 = 0
            if r['I=$15k, r=.2'] > r['Regular Grid Service'] and test4:
                intersect.append(i)
                test4 = 0
        even_pt_lo = math.ceil(min(intersect)/12)
        even_pt_hi = math.ceil(max(intersect)/12)

        # print(projection)
        print('break even low', even_pt_lo)
        print('break even high', even_pt_hi)

        display = projection.to_json()
        # parsed = json.loads(display)
        # json.dumps(parsed, indent=4)
        #############################################################################################

                    
    ##### FINAL RETURN JSON #####
    return jsonify(display)







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
        chrome_options = Options()
        chrome_options.add_argument("headless")
        driver = webdriver.Chrome(ChromeDriverManager(version="89.0.4389.23").install(), options=chrome_options)
        driver.set_window_size(800,1000)
        driver.get('https://www.google.com/get/sunroof/building/' + str(coords_json[0]['latitude']) + '/' + str(coords_json[0]['longitude']) + '/#?f=buy')
        
        
        square_footage_available = [e.text for e in driver.find_elements_by_css_selector('.panel-fact-text')]

        # js_string = "let element = document.body.getElementsByClassName(\"main-content\")[0].getElementsByClassName(\"section-map\")[0].getElementsByClassName(\"address-map-panel\")[0].remove();document.body.getElementsByClassName(\"header-wrap\")[0].style.visibility = 'hidden';document.body.getElementsByClassName(\"main-content-wrapper\")[0].style['margin'] = '0px';document.body.getElementsByClassName(\"gmnoprint\")[0].style.visibility = 'hidden';"
        # driver.execute_script(js_string)
        # driver.execute_script("document.body.style.zoom='175%'")
        # time.sleep(2)
        # driver.save_screenshot("map_test.png")
        # driver.close()

        square_footage_available = square_footage_available[1]
        square_footage_available = square_footage_available.split(' ')
        square_footage_available = square_footage_available[0]
        square_footage_available = ''.join(e for e in square_footage_available if e.isdigit() or e == '.')

        if (db.session.query(SunRoof).filter(SunRoof.address == coords_json[0]['address']).count() == 0):
            sunroof_estimate = SunRoof(coords_json[0]['address'], square_footage_available)
            db.session.add(sunroof_estimate)
            db.session.commit()
        else:
            sunroof_estimate = db.session.query(SunRoof).filter(SunRoof.address == coords_json[0]['address']).first()
            setattr(sunroof_estimate, 'estimate', square_footage_available)
            db.session.commit()

    return jsonify('success')


@app.route('/posts', methods=['POST'])
def post_input():
    if request.method == 'POST':

        frontend_input = request.get_json()
        jsonify(frontend_input)

        if db.session.query(User).filter(User.address == frontend_input['address']).count() == 0:
            user = User(frontend_input['address'], frontend_input['house_footage'], frontend_input['panel_area'], frontend_input['azimuth'], frontend_input['year_built'])
            db.session.add(user)
            db.session.commit()
        else:
            user = db.session.query(User).filter(User.address == frontend_input['address']).first()
            setattr(user, 'sqr_footage', frontend_input['house_footage'])
            setattr(user, 'panel_area', frontend_input['panel_area'])
            setattr(user, 'azimuth', frontend_input['azimuth'])
            setattr(user, 'year_built', frontend_input['year_built'])
            db.session.commit()

    return jsonify('success')

@app.route('/square-feet/<address>', methods=['GET'])
def getSunroof_data(address):
    if request.method == 'GET':
        if db.session.query(SunRoof).filter(SunRoof.address == address).count() == 0:
            return 'cannot find estimate'
        else:
            estimate = db.session.query(SunRoof).filter(SunRoof.address == address).first()
            print(estimate.estimate)


    return jsonify(estimate.estimate)


if __name__ == '__main__':
    app.run(debug=True)