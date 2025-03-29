
from flask import Flask, render_template, request, url_for, session, redirect, jsonify
import json
import random
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

with open('data.json', 'r') as file:
    data = json.load(file)

WINNING_POINTS = 1000


class Player:
    def __init__(self,
                 id: int,
                 name: str,
                 points: int = 0):
        self.id = id
        self.name = name
        self.points = points

    def update_points(self, points):
        self.points += points

    def __repr__(self):
        return f'{self.name} - {self.points}'

    def __gt__(self, other):
        if self.id > other.id:
            return True
        return False

    def __lt__(self, other):
        if self.id < other.id:
            return True
        return False

    def __eq__(self, other):
        if self.id == other.id:
            return True
        return False

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'points': self.points,
        }

    @classmethod
    def from_dict(cls, cls_data):
        return cls(id=cls_data['id'], name=cls_data['name'], points=cls_data['points'])


game = {
    'winner': None,
    'current_card': random.choice(data[1:]),
}


def select_next_player():
    current_player_index = game.get('current_player_index', 0)
    players = game.get('players', [])

    current_player_index = (current_player_index + 1) % len(players)
    game['current_player'] = players[current_player_index]
    game['current_player_index'] = current_player_index


def select_next_card():
    game['current_card'] = random.choice(data[1:])


def check_winner():
    players = game.get('players', [])
    for player in players:
        if player['points'] >= WINNING_POINTS:
            game['winner'] = player


def reset_game():
    game = {
        'winner': None,
        'current_card': random.choice(data[1:]),
    }

    session['game'] = game


def update_game_state():
    current_card = game.get('current_card', {})
    current_player_index = game.get('current_player_index', 0)
    players = game.get('players', [])
    points = current_card.get('points', 0)

    current_player = Player.from_dict(players[current_player_index])
    current_player.update_points(points)
    current_player_dict = current_player.to_dict()

    game['current_player'] = current_player_dict
    game['players'][current_player_index] = current_player_dict


def initialize_game_state(players):
    players = [Player(i, player) for i, player in enumerate(players) if player]
    game['players'] = [player.to_dict() for player in players]

    current_player_index = random.randrange(len(players))
    game['current_player'] = game['players'][current_player_index]
    game['current_player_index'] = current_player_index


def play_round():
    select_next_card()
    update_game_state()
    check_winner()

    if not game['winner']:
        select_next_player()

    session['game'] = game


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        all_players = [request.form.get('player0'), request.form.get('player1'), request.form.get('player2'), request.form.get('player3')]
        initialize_game_state(all_players)
        session['game'] = game

        return redirect(url_for('play_game'))

    return render_template('index.html')

@app.route('/game_over', methods=['GET', 'POST'])
def game_over():
    winner = session['game']['winner']
    if request.method == 'POST':
        reset_game()
        return redirect(url_for('index'))
    
    return render_template('game_over.html', winner=winner)


@app.route('/play_game', methods=['GET', 'POST'])
def play_game():
    json_game = session.get('game', None)

    if request.method == 'POST':
        if session['game']['winner']:
            return redirect(url_for('game_over'))
        
        play_round()
    return render_template('play_game.html', game=json_game)


if __name__ == '__main__':
    app.run(debug=True)