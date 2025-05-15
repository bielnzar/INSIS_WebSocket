import random
import string
import ssl
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, join_room, emit
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

# Inisialisasi Flask + SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'RahasiaHati'
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='gevent')

# In-memory store
rooms = {}

def gen_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def check_win(board):
    wins = [(0,1,2),(3,4,5),(6,7,8),
            (0,3,6),(1,4,7),(2,5,8),
            (0,4,8),(2,4,6)]
    for a,b,c in wins:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    if all(board):
        return 'Seri'
    return None

def timestamp():
    return datetime.now().strftime('%H:%M:%S')

@socketio.on('connect')
def on_connect():
    print(f"[{timestamp()}] Client connected: {request.sid}")

@socketio.on('disconnect')
def on_disconnect():
    print(f"[{timestamp()}] Client disconnected: {request.sid}")

@app.route('/admin')
def admin_ui():
    return render_template('admin.html')

@app.route('/generate', methods=['POST'])
def generate_codes():
    room_id = gen_code(8)
    k1, k2 = gen_code(), gen_code()
    rooms[room_id] = {
        'codes': [k1, k2],
        'players': {},
        'board': [''] * 9,
        'turn': 'X',
        'started': False
    }
    return jsonify(room=room_id, codes=[k1, k2])

@app.route('/admin/message', methods=['POST'])
def admin_message():
    msg = request.json.get('msg', '')
    socketio.emit('admin_message', {'msg': msg})
    return jsonify(success=True)

@app.route('/client')
def client_ui():
    return render_template('client.html')

@socketio.on('join')
def on_join(data):
    room_id, kode, sid = data.get('room'), data.get('code'), request.sid
    room = rooms.get(room_id)
    if not room:
        emit('error', {'msg': 'Room tidak ditemukan'}); return
    if kode not in room['codes']:
        emit('error', {'msg': 'Kode tidak valid atau sudah digunakan'}); return
    if len(room['players']) >= 2:
        emit('error', {'msg': 'Room sudah penuh'}); return

    room['codes'].remove(kode)
    simbol = 'X' if 'X' not in room['players'].values() else 'O'
    room['players'][sid] = simbol
    join_room(room_id)
    emit('joined', {'symbol': simbol})

    if len(room['players']) == 2:
        room['started'] = True
        emit('start', {'turn': room['turn']}, room=room_id)

@socketio.on('move')
def on_move(data):
    room_id, idx, sid = data.get('room'), data.get('index'), request.sid
    room = rooms.get(room_id)
    if not room or not room['started']:
        emit('error', {'msg': 'Permainan belum dimulai'}); return

    simbol = room['players'].get(sid)
    if simbol != room['turn']:
        emit('error', {'msg': 'Bukan giliran Anda'}); return
    if room['board'][idx] != '':
        emit('error', {'msg': 'Petak sudah terisi'}); return

    room['board'][idx] = simbol
    hasil = check_win(room['board'])
    if hasil:
        emit('end', {
            'result': f'{hasil} (Memenangkan Pertandingan!), Hamdalah',
            'board': room['board']
        }, room=room_id)
        return

    room['turn'] = 'O' if room['turn'] == 'X' else 'X'
    emit('update', {'board': room['board'], 'turn': room['turn']}, room=room_id)

@socketio.on('surrender')
def on_surrender(data):
    room_id, sid = data.get('room'), request.sid
    room = rooms.get(room_id)
    if room and sid in room['players']:
        opp_sid = next(s for s in room['players'] if s != sid)
        opp_symbol = room['players'][opp_sid]
        emit('end', {
            'result': f'{opp_symbol} Surrender, Kamu Menang!',
            'board': room['board']
        }, room=room_id)

@socketio.on('ping_client')
def on_ping(data):
    emit('pong_server', {'ts': data.get('ts')})

@socketio.on('chat')
def on_chat(data):
    room_id, sid, msg = data.get('room'), request.sid, data.get('msg', '')
    symbol = rooms[room_id]['players'].get(sid, '?')
    emit('chat', {'sender': symbol, 'msg': msg}, room=room_id)



if __name__ == '__main__':
    # Load SSL context untuk WSS
    context = ('certs/cert.pem', 'certs/key.pem')
    
    server = pywsgi.WSGIServer(
        ('0.0.0.0', 5000),
        app,
        handler_class=WebSocketHandler,
        keyfile=context[1],
        certfile=context[0]
    )
    
    print(f"[{timestamp()}] Server running on https://localhost:5000")
    server.serve_forever()
