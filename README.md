# Hangman Backend - Full Stack Nanodegree Project

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
 
 
 
##Game Description:
Hangman is a word guessing game. Each game begins with a random english word, and
a maximum number of attempts. Users can make guesses consisting of a single letter.
For each guess, the response displays the target word with all letters that have
not yet been guessed replaced with underscores. Users can also guess the target
word, which will show a response saying if the guess is correct or not.

Many different Hangman games can be played by many different Users at any
given time. Each game can be retrieved or played by using the path parameter
`urlsafe_game_key`.

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.
 - words.json: A list of possible target words.

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, attempts
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not. Increases the number of active games for the given user by 1. Also adds a task to a task queue to update the average moves remaining
    for active games.
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
    
 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, letter_guess
    - Returns: GameForm with new game state.
    - Description: Accepts a 'letter_guess' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created, and the users number of active games will decrease by 1.
    
 - **guess_answer**
    - Path: 'game_guess/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, word_guess
    - Returns: GameForm with new game state.
    - Description: Accepts a 'word_guess' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created, and the users number of active games will decrease by 1.
    
 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
    
 - **get_rankings**
    - Path: 'rankings'
    - Method: GET
    - Parameters: None
    - Returns: RankingForms.
    - Description: Returns the list of users and their corresponding rank. A user's rank is their number of wins minus their number of losses.
    
 - **get_highscores**
    - Path: 'highscores'
    - Method: GET
    - Parameters: number_of_results
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database, ordered by number of guesses, limited by the number_of_results parameter.
    
 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.
    
 - **get_user_games**
    - Path: 'games/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: GameForms. 
    - Description: Returns a list of all of the user's currently active games.
    
 - **cancel_game**
    - Path: 'games/cancel/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key
    - Returns: Message confirming the game has been deleted. 
    - Description: Deletes a game given the urlsafe_game_key. If the game is already over, the game will not be deleted and an error will be displayed.
    
 - **show_game_history**
    - Path: 'games/history/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: MoveForms. 
    - Description: Displays a play-by-play list of move for the given game.
    
 - **get_active_game_count**
    - Path: 'games/active'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets the average number of attempts remaining for all games
    from a previously cached memcache key.

##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.

 - **Move**
    - Stores a particular move in a game. Associated with Games model via KeyProperty.
    
##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, attempts_remaining,
    game_over flag, user_name).
 - **GameMessageForm**
    - Representation of a Game's state, including a string message (urlsafe_key, attempts_remaining, game_over flag, message, user_name).
 - **NewGameForm**
    - Used to create a new game (user_name, min, max, attempts)
 - **MakeMoveForm**
    - Inbound make move form (letter_guess).
 - **GuessAnswerForm**
    - Inbound guess answer form (word_guess).
 - **RankingForm**
    - Used to display a user's rank (user_name, rank)
 - **RankingForms**
    - Multiple RankingForm container.
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag, guesses).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **MoveForm**
    - Used to display a representation of a single move. (move, message)
 - **MoveForms**
    - Multiple MoveForm container.
 - **StringMessage**
    - General purpose String container.