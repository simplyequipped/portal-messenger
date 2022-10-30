import json
import secrets

import pyjs8call

from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex()
socketio = SocketIO(app)

#TODO once user logs in, set callsign to username via config and then start js8call app
#TODO username (callsign) must contain at least (1) number, max length of 9 characters
#TODO stop js8call app when socketio closed

#TODO
def simulate_response(data)
    #TODO
    msg = pyjs8call.Message()
    msg.type = pyjs8call.Message.RX_DIRECTED
    msg.value = data['msg']
    msg.params['FROM'] = data['user']
    msg = msg.data()
    js8call.js8call._rx_queue.append(msg)



@app.route('/')
def index():
    global js8call
    callsign = js8call.config.get('Configuration', 'MyCall')
    return render_template('index.html', username=callsign)

@socketio.on('tx msg')
def tx_msg(data, methods=['GET', 'POST']):
    global js8call
    #print('\tsend msg: ' + str(data['user']) + ' > ' + str(data['msg']))
    js8call.send_directed_message(data['user'], data['msg'])
    #TODO
    #simulate_response(data)
    
#TODO determine how a directed response is received, process accordingly
def rx_msg(msg):
    message = {'from': msg['from'], 'msg': msg['value']}
    #TODO
    print(message)
    socketio.emit('rx msg', message)

@socketio.on('log')
def log(data, methods=['GET', 'POST']):
    print('\tlog: ' + str(data['msg']))

@socketio.on('login')
def login(data, methods=['GET', 'POST']):
    if any(char.isdigit() for char in data['username']):
        valid_username = True
    else:
        valid_username = False
        error = 'Username must contain at least 1 digit [0-9]'

    if len(data['username']) <= 9:
        valid_username = True
    else:
        valid_username = False
        error = 'Username max length is 9 characters'

    if valid_username:
        #TODO
        print('Valid username: ' + data['username'])

        result = {'login': True}
        socketio.emit('login attempt', result)

        global js8call
        js8call.config.set('Configuration', 'MyCall', data['username'].upper())
        js8call.start()
    else:
        #TODO
        print('Invalid username: ' + data['username'])
        print('Error: ' + error)

        result = {'login': False, 'error': error}
        socketio.emit('login attempt', result)

#@socketio.on('disconnect')
#def stop():
#    global js8call
#    js8call.stop()



# initialize js8call client
js8call = pyjs8call.Client()
if 'Portal' not in js8call.config.get_profile_list():
    js8call.config.create_profile('Portal')

js8call.set_config_profile('Portal')
js8call.register_rx_callback(rx_msg, pyjs8call.Message.RX_DIRECTED)



if __name__ == 'main':
    socketio.run(app, debug=True)
