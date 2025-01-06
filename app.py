from flask import Flask, render_template
from flask_socketio import SocketIO, emit


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('chat.html')

@socketio.on('send_message')
def handle_message(data):
    """Broadcast message to all connected clients."""
    emit('receive_message', data, broadcast=True)

"""if __name__ == '__main__':
    socketio.run(app, debug=True)
    """
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)