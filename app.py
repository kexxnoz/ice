from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Подключение к MongoDB
cluster = MongoClient(
    "mongodb+srv://user:lox123@cluster0.lmxjciy.mongodb.net/?retryWrites=true&w=majority"
)
db = cluster["icedrevive"]
collection = db["icedcoll"]

# Очередь для поиска игры
game_queue = []

# Список карт для выбора
maps = ["фортис", "криментис", "замки", "актуон", "зеленс"]
banned_maps = []


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username')
        action = request.form.get('action')

        if username:
            if action == 'start_search':
                if username not in game_queue:
                    game_queue.append(username)
            elif action == 'leave_search':
                if username in game_queue:
                    game_queue.remove(username)

        if len(game_queue) == 1:
            return redirect(url_for('prepare_game'))

    try:
        documents = list(collection.find({}, {'_id': 0, 'nickname': 1, 'rating': 1}).sort('rating', -1))
        return render_template('index.html', documents=documents, queue=game_queue)
    except Exception as e:
        return f"Ошибка при получении данных: {e}"


@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        token = request.form.get('token')
        if token:
            try:
                response = requests.get(f"https://api.vimeworld.ru/misc/token/{token}")
                data = response.json()
                username = data['owner']['username']
                return redirect(url_for('profile', username=username))
            except Exception as e:
                return f"Ошибка при проверке токена: {e}"

    return render_template('auth.html')


@app.route('/profile/<username>')
def profile(username):
    try:
        user = collection.find_one({'nickname': username}, {'_id': 0, 'nickname': 1, 'rating': 1})
        if user:
            return render_template('profile.html', username=user['nickname'], rating=user['rating'])
        else:
            return f"Пользователь с ником {username} не найден."
    except Exception as e:
        return f"Ошибка при получении данных пользователя: {e}"


@app.route('/prepare_game', methods=['GET', 'POST'])
def prepare_game():
    global banned_maps

    if request.method == 'POST':
        selected_map = request.form.get('selected_map')
        if selected_map and selected_map not in banned_maps:
            banned_maps.append(selected_map)

        if len(banned_maps) == len(maps) - 1:
            remaining_map = list(set(maps) - set(banned_maps))[0]
            return render_template('prepare_game.html', players=game_queue, maps=[], chosen_map=remaining_map)

    available_maps = [m for m in maps if m not in banned_maps]
    return render_template('prepare_game.html', players=game_queue, maps=available_maps, chosen_map=None)


@app.route('/clear_banned_maps', methods=['POST'])
def clear_banned_maps():
    global banned_maps
    banned_maps = []
    return jsonify({'status': 'success'})


@app.route('/queue_status')
def queue_status():
    return render_template('queue_status.html', queue=game_queue)


if __name__ == '__main__':
    app.run(debug=True)
