# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""


import logging
import endpoints
import utils
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Score, Move
from models import StringMessage, NewGameForm, GameForm, GameMessageForm, MakeMoveForm,\
    GuessAnswerForm, ScoreForms, GameForms, RankingForms, MoveForms

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
GUESS_ANSWER_REQUEST = endpoints.ResourceContainer(
    GuessAnswerForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2),)
GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1),)
HIGH_SCORES_REQUEST = endpoints.ResourceContainer(
    number_of_results=messages.IntegerField(1),)

MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'

@endpoints.api(name='hangman', version='v1')
class HangmanApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameMessageForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')

        game = Game.new_game(user, request.attempts)

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Good luck playing Hangman!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameMessageForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = utils.get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Time to make a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameMessageForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = utils.get_by_urlsafe(request.urlsafe_game_key, Game)
        if game.game_over:
            return game.to_form('Game already over!')

        if not utils.valid_letter_guess(request.letter_guess, game.guessed_letters):
            return game.to_form('Sorry, %s is an invalid guess!' % request.letter_guess)

        game.attempts_remaining -= 1
        game.guessed_letters = game.guessed_letters + request.letter_guess

        move = Move(game=game.key, move=request.letter_guess, move_index=game.attempts_allowed - game.attempts_remaining)
        move.put()

        if utils.guessed_letters_are_correct(game.guessed_letters, game.target):
            game.end_game(True)
            return game.to_form('You win!')

        if request.letter_guess in game.target:
            msg = 'That letter is in the word! Remaining %s' % utils.show_hyphenated_progress(game.guessed_letters, game.target)
        else:
            msg = 'Oops! That letter is not in the word! Remaining %s' % utils.show_hyphenated_progress(game.guessed_letters, game.target)

        if game.attempts_remaining < 1:
            game.end_game(False)
            return game.to_form(msg + ' Game over!')
        else:
            game.put()
            return game.to_form(msg)

    @endpoints.method(request_message=GUESS_ANSWER_REQUEST,
                      response_message=GameMessageForm,
                      path='game_guess/{urlsafe_game_key}',
                      name='guess_answer',
                      http_method='PUT')
    def guess_answer(self, request):
        """Guesses the answer. Returns a game state with message"""
        game = utils.get_by_urlsafe(request.urlsafe_game_key, Game)
        if game.game_over:
            return game.to_form('Game already over!')

        if not utils.valid_word_guess(request.word_guess):
            return game.to_form('Sorry, %s is an invalid guess!' % request.guess)

        game.attempts_remaining -= 1
        move = Move(game=game.key, move=request.word_guess, move_index=game.attempts_allowed - game.attempts_remaining)
        move.put()

        if request.word_guess == game.target:
            game.end_game(True)
            return game.to_form('You win!')
        else:
            msg = 'Oops! That is not the word! Remaining %s' % utils.show_hyphenated_progress(game.guessed_letters, game.target)

        if game.attempts_remaining < 1:
            game.end_game(False)
            return game.to_form(msg + ' Game over!')
        else:
            game.put()
            return game.to_form(msg)

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(response_message=RankingForms,
                      path='rankings',
                      name='get_rankings',
                      http_method='GET')
    def get_rankings(self, request):
        """Return all rankings"""
        return RankingForms(items=[user.to_ranking_form() for user in User.query()])

    @endpoints.method(request_message=HIGH_SCORES_REQUEST,
                      response_message=ScoreForms,
                      path='highscores',
                      name='get_highscores',
                      http_method='GET')
    def get_highscores(self, request):
        """Return highest scores, limited by the number of results requested"""
        highscores = Score.query().order(Score.guesses).fetch(request.number_of_results)
        return ScoreForms(items=[score.to_form() for score in highscores])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='games/user/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns all of an individual User's active games"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        games = Game.query(Game.user == user.key)
        return GameForms(items=[game.to_form() for game in games])

    @endpoints.method(request_message=GAME_REQUEST,
                      response_message=StringMessage,
                      path='games/cancel/{urlsafe_game_key}',
                      name='cancel_game',
                      http_method='POST')
    def cancel_game(self, request):
        """Cancels an active game"""
        game = utils.get_by_urlsafe(request.urlsafe_game_key, Game)

        if game.game_over:
            return StringMessage(message='Game already over!')

        user = game.user.get()
        user.active_games = user.active_games - 1
        user.put()

        game.delete()

        return StringMessage(message='Game deleted!')

    @endpoints.method(request_message=GAME_REQUEST,
                      response_message=MoveForms,
                      path='games/history/{urlsafe_game_key}',
                      name='show_game_history',
                      http_method='GET')
    def show_game_history(self, request):
        """Shows the history of a particular game"""
        game = utils.get_by_urlsafe(request.urlsafe_game_key, Game)
        moves = Move.query(Move.game == game.key).order(Move.move_index)
        return MoveForms(items=[move.to_form() for move in moves])

    @endpoints.method(response_message=StringMessage,
                      path='games/average_attempts',
                      name='get_average_attempts_remaining',
                      http_method='GET')
    def get_average_attempts(self, request):
        """Get the cached average moves remaining"""
        return StringMessage(message=memcache.get(MEMCACHE_MOVES_REMAINING) or '')

    @staticmethod
    def _cache_average_attempts():
        """Populates memcache with the average moves remaining of Games"""
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            total_attempts_remaining = sum([game.attempts_remaining
                                        for game in games])
            average = float(total_attempts_remaining)/count
            memcache.set(MEMCACHE_MOVES_REMAINING,
                         'The average moves remaining is {:.2f}'.format(average))


api = endpoints.api_server([HangmanApi])
