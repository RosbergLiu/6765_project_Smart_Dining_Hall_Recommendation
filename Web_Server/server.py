#!/usr/bin/env python2.7

import boto3
from flask import Flask, request, jsonify, session, render_template
import csv

import json,time,sys
from collections import OrderedDict
from threading import Thread

from boto3.dynamodb.conditions import Key,Attr

import recommend
sys.path.append('./utils')
import aws

app = Flask(__name__)

app.config['SECRET_KEY'] = 'Idontknow'

USERS_TABLE = "USERS_TABLE"
Ferris_Menu = "Ferris_Menu"
JJ_Menu = "JJ_Menu"
Johnjay_Menu = "JohnJay_Menu"
TableAvailability = "TableAvailability"
Ferris_entry = "EntryCount_FerrisBooth"
JJ_entry = "EntryCount_JJPlace"
JohnJay_entry = "EntryCount_JohnJay"

dynamodb = aws.getResource('dynamodb', 'us-east-1')

table1 = dynamodb.Table(USERS_TABLE)
table2 = dynamodb.Table(Johnjay_Menu)
table3 = dynamodb.Table(JJ_Menu)
table4 = dynamodb.Table(Ferris_Menu)
table_Availability = dynamodb.Table(TableAvailability)
table_Ferris_entry = dynamodb.Table(Ferris_entry)
table_JJ_entry = dynamodb.Table(JJ_entry)
table_JohnJay_entry = dynamodb.Table(JohnJay_entry)


@app.route('/')
def index():
    context = 'All OKAY!'
    return render_template('index.html', context = context)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        # print request.json
        email = request.json.get('email')
        password = request.json.get('password')

        # query from db if email already exist
        scan_res = table1.scan(FilterExpression=Attr('email').eq(email))
        result = scan_res['Items']

        if len(result):
            user = result[0]['name']
        else:
            user = None

        if not user:
            print 'error: User does not exist'
            return jsonify({'error': 'User does not exist'}), 404
        elif result[0]['password'] != password:
            print 'error: Incorrect password'
            return jsonify({'error': 'Incorrect password'}), 400

        else:
            print 'login successfully'
            session['logged_in'] = True
            session['user_id'] = result[0]['email']

    return jsonify({'email' : email}), 200

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.json.get('name')
        email = request.json.get('email')
        password = request.json.get('password')

        # same as login
        scan_res = table1.scan(FilterExpression=Attr('email').eq(email))
        result = scan_res['Items']

        if len(result):
            user = result[0]['name']
        else:
            user = None
            
        if user:
            print 'error: User already exist'
            return jsonify({'error': 'User already exist'}), 400

        try:
            response = table1.put_item(
                Item = {
                        'email': email,
                        'name': username,
                        'password': password
                }
            )
            # print response

        except Exception as e:
            error = e
        print 'register successfully'
    return jsonify({'username' : username}), 200


@app.route('/logout')
def logout():
    session['user_id'] = None
    session['logged_in'] = False
    return jsonify({'success' : 'logout successful'}), 200


@app.route('/JohnJay', methods=(['GET']))
def display_johnjay():
   
    Table_Availability = table_availability('johnjay')

    Item = []
    menu = (table2.scan())['Items']
    
    for items in menu:
        Item.append(items.values()[0])

    total_num = entry(table_JohnJay_entry)
    

    if len(Table_Availability):
        return jsonify({'table_availability' : Table_Availability, 'menu' : Item, 'flow_rate' : str(total_num)}), 200
    else:
        return jsonify({'table_availability' : 'None is available', 'menu' : Item, 'flow_rate' : str(total_num)}), 200

@app.route('/JJ', methods=(['GET']))
def dispaly_jj():
    
    Table_Availability = table_availability('jj')

    Item = []
    menu = (table3.scan())['Items']
    
    for items in menu:
        Item.append(items.values()[0])

    total_num = entry(table_JJ_entry)
    print total_num
    
    if len(Table_Availability):
        return jsonify({'table_availability' : Table_Availability, 'menu' : Item, 'flow_rate' : str(total_num)}), 200
    else:
        return jsonify({'table_availability' : 'None is available', 'menu' : Item, 'flow_rate' : str(total_num)}), 200


@app.route('/Ferris', methods=(['GET']))
def dispaly_ferris():
    
    Table_Availability = table_availability('ferris')

    Item = []
    menu = (table4.scan())['Items']
  
    for items in menu:
        Item.append(items.values()[0])

    total_num = entry(table_Ferris_entry)
    
    if len(Table_Availability):
        return jsonify({'table_availability' : Table_Availability, 'menu' : Item, 'flow_rate' : str(total_num)}), 200
    else:
        return jsonify({'table_availability' : 'None is available', 'menu' : Item, 'flow_rate' : str(total_num)}), 200

@app.route('/rating', methods=(['GET', 'POST']))
def rating():
    if request.method == 'POST':
        dish_name = request.json.get('dishname')
        email = request.json.get('email')
        grade = request.json.get('rating')
        dining_hall = request.json.get('diningHall')

        userid = int(email[2:6])

        # write rating info into dataset for recommendation
        with open("Data/rating.csv", "a") as csvfile:
            filewriter = csv.writer(csvfile, delimiter=',', lineterminator='\n')
            filewriter.writerow([userid, dish_name, grade])
        

        if dining_hall == 'JohnJay':
            menu = table1.scan(FilterExpression=Attr('email').eq(email))
            result = menu['Items'][0]
            if 'JohnJay' not in result.keys():
                table1.update_item(
                        Key = {'email': email},
                        UpdateExpression = "set JohnJay = :JohnJay",
                        ExpressionAttributeValues = {
                            ':JohnJay': [{'dishname': dish_name, 'rating': str(grade)}]
                        }
                )
            else:
                result['JohnJay'].append({'dishname': dish_name, 'rating': str(grade)})
                table1.update_item(
                        Key = {'email': email},
                        UpdateExpression = "set JohnJay = :JohnJay",
                        ExpressionAttributeValues = {
                            ':JohnJay': result['JohnJay']
                        }
                )
        elif dining_hall == 'JJ':
            menu = table1.scan(FilterExpression=Attr('email').eq(email))
            result = menu['Items'][0]
            if 'JJ' not in result.keys():
                table1.update_item(
                        Key = {'email': email},
                        UpdateExpression = "set JJ = :JJ",
                        ExpressionAttributeValues = {
                            ':JJ': [{'dishname': dish_name, 'rating': str(grade)}]
                        }
                )
            else:
                result['JJ'].append({'dishname': dish_name, 'rating': str(grade)})
                table1.update_item(
                        Key = {'email': email},
                        UpdateExpression = "set JJ = :JJ",
                        ExpressionAttributeValues = {
                            ':JJ': result['JJ']
                        }
                )

        else:
            menu = table1.scan(FilterExpression=Attr('email').eq(email))
            result = menu['Items'][0]
            if 'Ferris' not in result.keys():
                table1.update_item(
                        Key = {'email': email},
                        UpdateExpression = "set Ferris = :Ferris",
                        ExpressionAttributeValues = {
                            ':Ferris': [{'dishname': dish_name, 'rating': str(grade)}]
                        }
                )
            else:
                result['Ferris'].append({'dishname': dish_name, 'rating': str(grade)})
                table1.update_item(
                        Key = {'email': email},
                        UpdateExpression = "set Ferris = :Ferris",
                        ExpressionAttributeValues = {
                            ':Ferris': result['Ferris']
                        }
                )

    menu = table1.scan(FilterExpression=Attr('email').eq(email))
    result = menu['Items']
    print 'result: ', result

    return jsonify({'dish_name' : dish_name, 'grade' : grade}), 200


@app.route('/recommend', methods=(['GET', 'POST']))
def recommend_dining():
    john_jay_menu = table2.scan(FilterExpression=Attr('dining_hall_id').eq(1))['Items']
    jj_menu = table3.scan(FilterExpression=Attr('dining_hall_id').eq(1))['Items']
    ferris_menu = table4.scan(FilterExpression=Attr('dining_hall_id').eq(1))['Items']
    
    john_jay_dish = 0
    jj_dish = 0
    ferris_dish = 0

    if request.method == 'POST':
        print request.json
        email = request.json.get('email')

        user_id = int(email[2:6])
        dining_recommend = recommend.recommend()
        dining_recommend.get_data()
        recommend_dish = dining_recommend.recommend_n_dishes(user_id, 5)

        # get dish
        for dish in recommend_dish:
            if dish in john_jay_menu:
                john_jay_dish += 1
            elif dish in jj_menu:
                jj_dish += 1
            else:
                ferris_dish += 1

        john_jay_dish /= 5
        jj_dish /= 5
        ferris_dish /= 5

        # get float rate
        john_jay_float = float(entry(table_JohnJay_entry)) / 200.0
        jj_float = float(entry(table_JJ_entry)) / 80.0
        ferris_float = float(entry(table_Ferris_entry)) / 100.0

        # get table availability
        john_jay_table = len(table_availability('johnjay'))/3.0
        jj_table = len(table_availability('jj'))/3.0
        ferris_table = len(table_availability('ferris'))/3.0

        john_jay_score = john_jay_dish + john_jay_table + 1.0/john_jay_float
        jj_score = jj_dish + jj_table + 1.0/jj_float
        ferris_score = ferris_dish + ferris_table + 1.0/ferris_float

        max = john_jay_score
        hall = 'john_jay'
        for (key, value) in {'john_jay':john_jay_score, 'jj':jj_score, 'ferris':ferris_score}.items():
            if value > max:
                hall = key
        recommendation = hall

        
        Menu = []
        if recommend == 'ferris':
            menu = (table4.scan())['Items']
        elif recommend == 'jj':
            menu = (table3.scan())['Items']
        else:
            menu = (table2.scan())['Items']

        for items in menu:
            Menu.append(items.values()[0])

    elif request.method == 'GET':
        user_id = 3347
        dining_recommend = recommend.recommend()
        dining_recommend.get_data()
        recommend_dish = dining_recommend.recommend_n_dishes(user_id, 5)
        
        for dish in recommend_dish:
            if dish in john_jay_menu:
                john_jay_dish += 1
            elif dish in jj_menu:
                jj_dish += 1
            else:
                ferris_dish += 1

        john_jay_dish /= 5
        jj_dish /= 5
        ferris_dish /= 5

        # get float rate
        john_jay_float = entry(table_JohnJay_entry) / 200.0
        jj_float = entry(table_JJ_entry) / 80.0
        ferris_float = entry(table_Ferris_entry) / 100.0

        # print john_jay_float, jj_float, ferris_float

        # get table availability
        john_jay_table = len(table_availability('johnjay'))/3.0
        jj_table = len(table_availability('jj'))/3.0
        ferris_table = len(table_availability('ferris'))/3.0

        # print john_jay_table, jj_table, ferris_table

        john_jay_score = john_jay_dish + john_jay_table + 1.0/john_jay_float
        jj_score = jj_dish + jj_table + 1.0/jj_float
        ferris_score = ferris_dish + ferris_table + 1.0/ferris_float

        # print john_jay_score, jj_score, ferris_score
        max = john_jay_score
        hall = 'john_jay'
        for (key, value) in {'john_jay':john_jay_score, 'jj':jj_score, 'ferris':ferris_score}.items():
            if value > max:
                print value
                hall = key
        recommendation = hall

        
        Menu = []
        if recommendation == 'ferris':
            menu = (table4.scan())['Items']
        elif recommendation == 'jj':
            menu = (table3.scan())['Items']
        else:
            menu = (table2.scan())['Items']

        for items in menu:
            Menu.append(items.values()[0])
    return jsonify({'recommendation' : recommendation, 'menu': Menu}), 200


def table_availability(dining_name):
    index = 0
    if dining_name == 'johnjay':
        index = 1
    elif dining_name == 'jj':
        index = 2
    else:
        index = 3

    Table_Availability = []
    dining_hall = table_Availability.scan(FilterExpression=Attr('dining_hall_id').eq(index))['Items']

    for item in dining_hall:
        if item['occupied'] == False:
            Table_Availability.append('Table'+str(item['table_id']))
    # print Table_Availability
    return Table_Availability

def entry(dining_name):
    default = dining_name.scan(FilterExpression=Attr('headcount').gt(1))['Items'][0]['headcount']
    
    print default
    positive = dining_name.scan(FilterExpression=Attr('headcount').eq(1))['Items']
    pos = len(positive)
    negative = dining_name.scan(FilterExpression=Attr('headcount').eq(-1))['Items']
    neg = len(negative)
    total_num = default+pos-neg
    return total_num

if __name__ == "__main__":
    import click

    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8000, type=int)
    def run(debug, threaded, host, port):
        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)
    
    run()