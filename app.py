import json
import secrets
import random
import time
import sqlite3

import pyjs8call

from flask import Flask, render_template, request, session
from flask_socketio import SocketIO

app = Flask(__name__)
app.secret_key = secrets.token_hex()
socketio = SocketIO(app)

#TODO stop js8call app when socketio closed



### flask routes and template handling

@app.route('/')
@app.route('/stations', methods=['GET', 'POST'])
@app.route('/stations.html', methods=['GET', 'POST'])
def stations():
    if request.method == 'POST':
        session['active_chat_username'] = request.form.get('user')
        return ''
    else:
        return render_template('stations.html')

@app.route('/chat')
@app.route('/chat.html')
def chat():
    username = session.get('active_chat_username')

    chat_data = {
        'username': username,
        #'history': user_chat_history(username)
        'history': build_test_msgs(10)
    }

    return render_template('chat.html', chat_data = chat_data)

@app.route('/settings')
@app.route('/settings.html')
def settings():
    return render_template('settings.html')



### socket.io functions

@socketio.on('user')
def set_user(data):
    #session['username'] = data['user']
    #print(session['username'])
    pass

@socketio.on('msg')
def tx_msg(data):
    msg = construct_tx_msg(data['user'], data['text'], time.time())
    js8call.send_directed_message(msg['to'], msg['text'])
    
# directed message callback
def rx_msg(msg):
    msg = construct_rx_msg(msg['from'], msg['value'], msg['time'])
    if msg['from'] == session.get('active_chat_username'):
        socketio.emit('msg', msg)

@socketio.on('log')
def log(data):
    print('\tlog: ' + str(data['msg']))

@socketio.on('heard-user')
def heard_user(data):
    last_heard = user_last_heard_timestamp(data['user'])
    if last_heard != None:
        socketio.emit('heard-user', last_heard)

@socketio.on('spot')
def update_spots():
    #TODO
    spots = [
        {'username': 'A4GOULD', 'last_heard': user_last_heard_timestamp(''), 'unread': False},
        {'username': 'BKG14', 'last_heard': user_last_heard_timestamp(''), 'unread': False},
        {'username': 'DRWNICK87', 'last_heard': user_last_heard_timestamp(''), 'unread': False}
    ]
    socketio.emit('spot', spots)

@socketio.on('pin')
def pin_user(data):
    pass

@socketio.on('unpin')
def unpin_user(data):
    pass



### helper functions

def local_time_str(timestamp):
    return time.strftime('%I:%M%p', time.localtime(timestamp)).lower()

def last_heard_minutes(timestamp):
    return int((time.time() - timestamp) / 60)


def user_last_heard_timestamp(username):
    #TODO
    return time.time() - random.randint(0, 60 * 60)

    spots = js8call.get_station_spots(station = username)

    if len(spots) > 0:
        spots.sort(key = lambda spot: spot['time'])
        return spots[-1]
    else:
        return None

#TODO
def user_chat_history(from_user, to_user):
    global db
    query_data = {'from_user': from_user, 'to_user': to_user}
    # select both sides of the conversation for the given users
    messages = db.execute('SELECT * FROM messages WHERE (from = :from_user AND to = :to_user) OR (from = :to_user AND to = :from_user)', query_data)

    msgs = []
    for message in list(messages):
        msg = {
            'id': message[0],
            'from': message[1],
            'to': message[2],
            'type': message[3],
            'time': message[4],
            'text': message[5],
            'unread': message[6],
            'sent': message[7]
        }
        msgs.append(msg)

    return msgs.sort(key = lambda msg: msg['time'])
    

#TODO
def build_test_msgs(count):
    active_chat_username = session.get('active_chat_username')
    logged_in_username = 'KC3KVT'
    msgs = []
    last_from = logged_in_username

    for i in range(count):
        if last_from == logged_in_username:
            from_user = active_chat_username
        else:
            from_user = logged_in_username;

        last_from = from_user

        if from_user == active_chat_username:
            to_user = logged_in_username
        else:
            to_user = active_chat_username

        if from_user == logged_in_username:
            msg_type = 'tx'
        else:
            msg_type = 'rx'

        if msg_type == 'rx':
            unread = random.choice([True, False])
        else:
            unread = None

        messages = [
            'Hello there neighbor!',
            'Hey there, how are you doing?',
            'Doing good here, how about you?',
            'Doing well, thanks for asking',
            'Hope to see you all soon! Tell everyone there hello.'
        ]

        msg = {
            'id': secrets.token_urlsafe(16),
            'from': from_user,
            'to': to_user,
            'type': msg_type,
            'time': local_time_str(time.time() - random.randint(0, 60 * 60)),
            'text': random.choice(messages),
            'unread': unread,
            'sent': None
        }

        msgs.append(msg)

    return msgs


def heard(spots):
    global db

    # only unique spots with the latest timestamp
    heard_data = {}
    for spot in spots:
        if spot['from'] not in heard_data.keys():
            heard_data[spot['from']] = spot['time']
        elif spot['time'] > heard_data[spot['from']]:
            heard_data[spot['from']] = spot['time']

    for username, timestamp in heard_data.items():
        heard = {
            'username': username, 
            'last_heard': last_heard_minutes(timestamp)
            }

    #socketio.emit('heard-list', heard)
    db.executemany()

def construct_rx_msg(callsign, text, time):
    global db
    msg = {
        'id': secrets.token_urlsafe(16),
        'from': callsign,
        'to': session.get('logged_in_user'),
        'type': 'rx',
        'time': time,
        'text': text,
        'unread': True,
        'sent': None
    }
    
    db.execute('INSERT INTO messages VALUES (:id, :from, :to, :type, :time, :text, :unread, :sent)', msg)
    db.commit()
    return msg

def construct_tx_msg(callsign, text, time):
    global db
    msg = {
        'id': secrets.token_urlsafe(16),
        'from': session.get('logged_in_user'),
        'to': callsign,
        'type': 'tx',
        'time': time,
        'text': text,
        'unread': None,
        'sent': 'Sending...'
    }
    
    db.execute('INSERT INTO messages VALUES (:id, :from, :to, :type, :time, :text, :unread, :sent)', msg)
    db.commit()
    return msg


### database functions

def configure_db(db):
    table_names = db.execute('SELECT name FROM sqlite_master').fetchall()
    #TODO
    print(table_names)

    if 'settings' not in table_names:
        db.execute('CREATE TABLE settings(name, value)')
        #TODO initialize settings

    if 'messages' not in table_names:
        db.execute('CREATE TABLE messages(id, from, to, type, time, text, unread, sent)')
    
    if 'spots' not in table_names:
        db.execute('CREATE TABLE spots(callsign, time)')






### initialize js8call client

#js8call = pyjs8call.Client()
#if 'Portal' not in js8call.config.get_profile_list():
#    js8call.config.create_new_profile('Portal')
#
#js8call.set_config_profile('Portal')
#js8call.register_rx_callback(rx_msg, pyjs8call.Message.RX_DIRECTED)
#js8call.start()



if __name__ == 'main':
    # initialize socket io
    socketio.run(app, debug=True)

    # initialize database
    db_con = sqlite3.connect('portal.db', detect_types=sqlite3.PARSE_DECLTYPES)
    sqlite3.register_adapter(bool, int)
    sqlite3.register_converter('BOOLEAN', lambda v: v != '0')
    db = db_con.cursor()
    configure_db(db)

