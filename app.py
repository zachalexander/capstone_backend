from flask import Flask, Blueprint, flash, g, session, request, jsonify, render_template, redirect, url_for, make_response
from flask_cors import CORS, cross_origin
from flask import jsonify
from flask_session import Session
import math
import random
import requests
import json
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import os
from markupsafe import escape

app = Flask(__name__)
CORS(app)
app.secret_key = '331@s35/adde2'
SESSION_COOKIE_DOMAIN = '127.0.0.1'

def check(sqr_ft):
    session['sqrft'] = sqr_ft
    test = session['sqrft']
    return test

@app.route('/', methods=['GET'])
def talking():

    test_calculations = 345 * random.randrange(1, 100)
    test_data = [
        {
            "area": 2342,
            "azimuth": -45,
            "test_calc": test_calculations
        }
    ]
    return jsonify(test_data)

@app.route('/calc')
def model():
    print(session)

    area_data = [
        {
        "area": session.get('calc')
        }
    ]
    return jsonify(area_data)


@app.route('/posts', methods=['POST'])
def chatting():
    session.clear()
    if request.method == 'POST':
        test = request.get_json()
        jsonify(test)

        calc = int(test['area']) * 25



        final_json = [
            {
                "area": test['area'],
                "address": test['address']
            }
        ]
        session['calc'] = calc
        print('first_func', session.get('calc'))
        print(session)

    return redirect(url_for('model'))



@app.route('/square-feet')
def square_feet():
    print(session)
    test = session.get('sqrft')

    final_json = [
        {
            "sqr_ft": '850'
        }
    ]

    return jsonify(final_json)
    # print('second_func', test)
    # if 'sqrft' in session:
    #     return jsonify(final_json)
    # if 'sqrft' not in session:
    #     return 'Square footage is %s' % None




@app.route('/coords', methods=['GET', 'POST'])
def selenium_check():
    
    session.clear()
    ### dummy variables
    session['sqrft'] = "850"


    # if request.method == "POST":
    # coordinates = request.get_json()
    # jsonify(coordinates)

    # coords_json = [
    #     {
    #         "latitude": coordinates['latitude'],
    #         "longitude": coordinates['longitude']
    #     }
    # ]

    # json.dumps(coords_json)

    # chrome_options = Options()
    # chrome_options.add_argument("headless")

    # driver = webdriver.Chrome(ChromeDriverManager(version="87.0.4280.88").install(), options=chrome_options)
    # driver.set_window_size(800,1000)
    # driver.get('https://www.google.com/get/sunroof/building/' + str(coords_json[0]['latitude']) + '/' + str(coords_json[0]['longitude']) + '/#?f=buy')
    # square_footage_available = [e.text for e in driver.find_elements_by_css_selector('.panel-fact-text')]
    # # print(square_footage_available[1])
    # # # js_string = "let element = document.body.getElementsByClassName(\"main-content\")[0].getElementsByClassName(\"section-map\")[0].getElementsByClassName(\"address-map-panel\")[0].remove();document.body.getElementsByClassName(\"header-wrap\")[0].style.visibility = 'hidden';document.body.getElementsByClassName(\"main-content-wrapper\")[0].style['margin'] = '0px';document.body.getElementsByClassName(\"gmnoprint\")[0].style.visibility = 'hidden';"
    # # # driver.execute_script(js_string)
    # # # driver.execute_script("document.body.style.zoom='175%'")
    # # # time.sleep(2)
    # # # driver.save_screenshot("map_test.png")
    # driver.close()

    # print(session)
    # square_footage_available = square_footage_available[1]
    # square_footage_available = square_footage_available.split(' ')
    # session['sqrft'] = square_footage_available[0]

    print('first_func', session.get('sqrft'))
    print(session)
    return redirect(url_for('square_feet'))
    # final_json = jsonify(final_json)
   


if __name__ == '__main__':
    app.run(debug=True)