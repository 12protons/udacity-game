"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
import json
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb
from google.appengine.ext import db


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    wins = ndb.IntegerProperty(default=0)
    losses = ndb.IntegerProperty(default=0)
    active_games = ndb.IntegerProperty(default=0)

    def to_ranking_form(self):
        form = RankingForm()
        form.user_name = self.name
        form.rank = self.wins - self.losses
        return form

class Game(ndb.Model):
    """Game object"""
    target = ndb.StringProperty(required=True)
    guessed_letters = ndb.StringProperty(required=True)
    attempts_allowed = ndb.IntegerProperty(required=True)
    attempts_remaining = ndb.IntegerProperty(required=True, default=5)
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')

    @classmethod
    def new_game(cls, user, attempts):
        """Creates and returns a new game"""

        with open('words.json') as words_file:    
            word_list = json.load(words_file)

        word = word_list[random.choice(range(1, len(word_list) + 1))]

        game = Game(user=user.key,
                    target=word,
                    guessed_letters='',
                    attempts_allowed=attempts,
                    attempts_remaining=attempts,
                    game_over=False)
        game.put()

        user.active_games = user.active_games + 1
        user.put()

        return game

    def to_form(self, message=''):
        """Returns a GameForm representation of the Game"""
        if message:
            form = GameMessageForm()
            form.message = message
        else:
            form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.attempts_remaining = self.attempts_remaining
        form.game_over = self.game_over
        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()
        # Add the game to the score 'board'
        score = Score(user=self.user, date=date.today(), won=won,
                      guesses=self.attempts_allowed - self.attempts_remaining)
        score.put()

        # Update the user's wins/losses
        user = self.user.get()
        if won:
            user.wins = user.wins + 1
        else:
            user.losses = user.losses + 1
        user.active_games = user.active_games - 1
        user.put()

    def delete(self):
        print("test")
        db.delete(db.Key(self.key.urlsafe()))


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    guesses = ndb.IntegerProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date), guesses=self.guesses)


class Move(ndb.Model):
    """Move object"""
    game = ndb.KeyProperty(required=True, kind='Game')
    move = ndb.StringProperty(required=True)
    move_index = ndb.IntegerProperty(required=True)


    def to_form(self):
        game = self.game.get()
        if len(self.move) > 1:
            #Word guess
            if self.move == game.target:
                message = "Correct!"
            else:
                message = "Incorrect."
        else:
            #Letter guess
            if self.move in game.target:
                message = "Letter is in the word!"
            else:
                message = "Letter is not in the word."
        return MoveForm(move=self.move, message=message)


class MoveForm(messages.Message):
    """MoveForm for showing a particular move in a game"""
    move = messages.StringField(1, required=True)
    message = messages.StringField(2, required=True)


class MoveForms(messages.Message):
    """MoveForms for showing all the moves in a game"""
    items = messages.MessageField(MoveForm, 1, repeated=True)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    attempts_remaining = messages.IntegerField(2, required=True)
    game_over = messages.BooleanField(3, required=True)
    user_name = messages.StringField(4, required=True)


class GameMessageForm(messages.Message):
    """GameForm for outbound game state information, including a message"""
    urlsafe_key = messages.StringField(1, required=True)
    attempts_remaining = messages.IntegerField(2, required=True)
    game_over = messages.BooleanField(3, required=True)
    message = messages.StringField(4, required=True)
    user_name = messages.StringField(5, required=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    attempts = messages.IntegerField(4, default=5)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    letter_guess = messages.StringField(1, required=True)


class GuessAnswerForm(messages.Message):
    """Used to guess an answer in an existing game"""
    word_guess = messages.StringField(1, required=True)


class RankingForm(messages.Message):
    """Used to guess an answer in an existing game"""
    user_name = messages.StringField(1, required=True)
    rank = messages.IntegerField(2, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    guesses = messages.IntegerField(4, required=True)

class GameForms(messages.Message):
    """Return multiple GameForms"""
    items = messages.MessageField(GameForm, 1, repeated=True)

class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)

class RankingForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(RankingForm, 1, repeated=True)

class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
