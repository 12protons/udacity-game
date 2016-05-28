"""utils.py - File for collecting general utility functions."""

import re
import logging
from google.appengine.ext import ndb
import endpoints

def get_by_urlsafe(urlsafe, model):
    """Returns an ndb.Model entity that the urlsafe key points to. Checks
        that the type of entity returned is of the correct kind. Raises an
        error if the key String is malformed or the entity is of the incorrect
        kind
    Args:
        urlsafe: A urlsafe key string
        model: The expected entity kind
    Returns:
        The entity that the urlsafe Key string points to or None if no entity
        exists.
    Raises:
        ValueError:"""
    try:
        key = ndb.Key(urlsafe=urlsafe)
    except TypeError:
        raise endpoints.BadRequestException('Invalid Key')
    except Exception, e:
        if e.__class__.__name__ == 'ProtocolBufferDecodeError':
            raise endpoints.BadRequestException('Invalid Key')
        else:
            raise

    entity = key.get()
    if not entity:
        return None
    if not isinstance(entity, model):
        raise ValueError('Incorrect Kind')
    return entity

def valid_letter_guess(guess, guessed_letters):
    """Validates a hangman guess based on the previously guessed letters.
    Args:
        guess: The guess to be validated
        guessed_letters: The letters previously guessed in this game
    Returns:
        True if the guess is an alpha character and is not in the list of 
        guessed_characters. False otherwise.
    """
    if not guess.isalpha():
        return False
    elif len(guess) is not 1:
        return False
    elif guess.lower() in guessed_letters:
        return False
    else:
        return True

def valid_word_guess(guess):
    """Validates a hangman guess based on the previously guessed letters.
    Args:
        guess: The guess to be validated
        guessed_letters: The letters previously guessed in this game
    Returns:
        True if the guess is an alpha character and is not in the list of 
        guessed_characters. False otherwise.
    """
    return guess.isalpha()

def guessed_letters_are_correct(guessed_letters, target):
    """
    """
    for char in target:
        if char not in guessed_letters:
            return False
    return True

def show_hyphenated_progress(guessed_letters, target):
    """
    """
    hyphenated_progress = ''
    for char in target:
        if char in guessed_letters:
            hyphenated_progress = hyphenated_progress + char + ' '
        else:
            hyphenated_progress = hyphenated_progress + '_ '

    return hyphenated_progress