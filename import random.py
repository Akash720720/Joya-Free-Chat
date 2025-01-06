from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, send, emit
from markupsafe import escape

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

users = []  # Logged-in users
messages = []  # Chat messages history

@app.route('/')
def login_page():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - Joya Chat Room</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(to bottom right, #ffecd2, #fcb69f);
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .login-container {
                background: #ffffff;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
                text-align: center;
                width: 350px;
            }
            .login-container h1 {
                margin-bottom: 10px;
                font-size: 26px;
                color: #ff5722;
            }
            .login-container input {
                width: 100%;
                padding: 12px;
                margin-bottom: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            .login-container button {
                width: 100%;
                padding: 12px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                transition: background-color 0.3s;
            }
            .login-container button:hover {
                background-color: #0056b3;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h1>Welcome to Joya Chat Room!</h1>
            <form method="POST" action="/login">
                <input type="text" name="username" placeholder="Enter username" required>
                <button type="submit">Login</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    if username and username not in users:
        users.append(username)
        return redirect(url_for('chat_page', username=username))
    else:
        return '<h1>Enter a valid username.</h1><a href="/">Try Again</a>'

@app.route('/chat')
def chat_page():
    username = request.args.get('username', 'Guest')
    welcome_message = "Welcome!" if username != 'Joya' else "Welcome, dear Joya!"

    user_list_html = ''.join([f'<div>{escape(user)}</div>' for user in users]) if users else '<div>No users online</div>'
    message_history_html = ''.join([f'<div>{escape(msg)}</div>' for msg in messages])

    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Joya Chat Room</title>
        <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
        <style>
            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background-color: #1e1e2f;
                color: #f0f0f0;
                display: flex;
                height: 100vh;
                overflow: hidden;
            }}
            .sidebar {{
                width: 300px;
                background-color: #27293d;
                padding: 10px;
                display: flex;
                flex-direction: column;
            }}
            .sidebar h2 {{
                color: #ff5722;
                text-align: center;
                margin-bottom: 15px;
            }}
            .user-list {{
                flex-grow: 1;
                overflow-y: auto;
            }}
            .user-list div {{
                padding: 10px;
                border-bottom: 1px solid #3a3b4f;
                cursor: pointer;
            }}
            .chat-area {{
                flex-grow: 1;
                display: flex;
                flex-direction: column;
                background: #1e1e2f;
            }}
            .chat-header {{
                background-color: #27293d;
                padding: 10px;
                text-align: center;
                font-size: 20px;
                color: #ff5722;
            }}
            .messages {{
                flex-grow: 1;
                padding: 10px;
                overflow-y: auto;
            }}
            .chat-input {{
                display: flex;
                padding: 10px;
                background-color: #27293d;
            }}
            .chat-input input {{
                flex-grow: 1;
                padding: 10px;
                margin-right: 10px;
                border: none;
                border-radius: 5px;
            }}
            .chat-input button {{
                padding: 10px 20px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h2>Joya Chat Room</h2>
            <div class="user-list">
                {user_list_html}
            </div>
        </div>
        <div class="chat-area">
            <div class="chat-header">{welcome_message}</div>
            <div class="messages" id="messages">
                {message_history_html}
            </div>
            <div class="chat-input">
                <input id="message" type="text" placeholder="Type your message...">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
        <script>
            var username = "{username}";
            var socket = io();

            socket.on('connect', function() {{
                socket.emit('join', username);
            }});

            socket.on('message', function(data) {{
                const messageDiv = document.createElement('div');
                messageDiv.textContent = data;
                document.getElementById('messages').appendChild(messageDiv);
                document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
            }});

            socket.on('update_users', function(userList) {{
                const userContainer = document.querySelector('.user-list');
                userContainer.innerHTML = '';
                userList.forEach(user => {{
                    const userDiv = document.createElement('div');
                    userDiv.textContent = user;
                    userContainer.appendChild(userDiv);
                }});
            }});

            function sendMessage() {{
                const message = document.getElementById('message').value.trim();
                if (message) {{
                    socket.emit('message', {{username: username, message: message}});
                    document.getElementById('message').value = '';
                }}
            }}
        </script>
    </body>
    </html>
    '''

@socketio.on('join')
def handle_join(username):
    if username not in users:
        users.append(username)
    send(f"{username} has joined the chat!", broadcast=True)
    emit('update_users', users, broadcast=True)

@socketio.on('message')
def handle_message(data):
    username = data.get('username', 'Unknown')
    msg = data.get('message', '')
    formatted_message = f"{username}: {msg}"
    messages.append(formatted_message)
    send(formatted_message, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)



















