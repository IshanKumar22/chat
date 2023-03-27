from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import WSGIServer
from flask import Flask, render_template, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from wtforms import StringField
from wtforms.validators import InputRequired, Length
from flask_wtf import FlaskForm

IP = '192.168.0.108'
PORT = 81

app = Flask(__name__, template_folder="files")
app.config['SECRET_KEY'] = 'mysecretkey'
socketio = SocketIO(app) # , async_mode='gevent')
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username


users = []

# Login form


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
                           InputRequired(), Length(min=4, max=15)])


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))

    form = LoginForm()

    if form.validate_on_submit():
        valid = True
        for user in users:
            if user.username == form.username.data:
                valid = False
                break
        if valid:
            users.append(User(users.__len__(), form.username.data))
            login_user(users[-1])
            return redirect(url_for('chat'))

    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')


@socketio.on('join')
def on_join(data):
    username = data['username']
    ip = data['ip']
    join_room("chatroom")
    print(f"New connection: IP is {ip} and username is {username}")
    emit('message', {'username': 'System',
         'message': username + ' has joined the chat.'}, room="chatroom")


@socketio.on('leave')
def on_leave(data):
    username = data['username']
    leave_room("chatroom")
    for idx, user in enumerate(users):
        if user.username == username:
            users.pop(idx)
    emit('message', {'username': 'System',
         'message': username + ' has left the chat.'}, room="chatroom")


@socketio.on('message')
def on_message(data):
    username = data['username']
    message = data['message']
    emit('message', {'username': username,
         'message': message}, room="chatroom")


@login_manager.user_loader
def load_user(user_id):
    return next((u for u in users if u.id == int(user_id)), None)

http_server = WSGIServer((IP, PORT), app.wsgi_app, handler_class=WebSocketHandler)

if __name__ == '__main__':
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
