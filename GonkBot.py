import praw
from time import sleep
import os
import json

class LoginFileNotFound(Exception):
    '''
    Custom exception to be raised when the json file with the
    login info is not found.
    '''
    pass

class NotJSONFileError(Exception):
    '''
    Custom exception to be raised when the credentials file
    isn't a valid json
    '''
    pass

class IncompleteLoginDetailsError(Exception):
    '''
    Custom exception for incorrect credentials file structure
    '''
    pass

def get_login_details(login_file):
    '''
    Return the login info as a dictionary.
    It contains the following keys:
    client_id
    client_secret
    user_agent
    user_name
    password
    '''

    # test if file is present
    if os.path.isfile(login_file):
        # if the bot is run locally we get the login details from the JSON file
        f = open(login_file, 'r')
        # test if JSON file is valid
        try:
            login = json.load(f)
        except json.decoder.JSONDecodeError:
            f.close() # close the file before panicking
            raise NotJSONFileError
        f.close() # we don't need the file open anymore

        # test for empty values or missing keys
        if '' in login.values() or \
            None in [login.get('client_id'),
                    login.get('client_secret'),
                    login.get('user_agent'),
                    login.get('username'),
                    login.get('password')]:
            raise IncompleteLoginDetailsError

        return login
    else:
        # if run on Heroku we need to use the config vars
        login = {
            'username'      : os.environ.get('username'),
            'password'      : os.environ.get('password'),
            'client_id'     : os.environ.get('client_id'),
            'client_secret' : os.environ.get('client_secret'),
            'user_agent'    : os.environ.get('user_agent')
        }
        # test for empty values or missing keys
        if '' in login.values() or \
            None in [login.get('client_id'),
                    login.get('client_secret'),
                    login.get('user_agent'),
                    login.get('username'),
                    login.get('password')]:
            raise IncompleteLoginDetailsError
        else:
            return login

def init_bot(login):
    # initialize Reddit object
    return praw.Reddit(client_id     = login.get('client_id'),
                        client_secret = login.get('client_secret'),
                        user_agent    = login.get('user_agent'),
                        username     = login.get('username'),
                        password      = login.get('password')
                        )
            
def make_comment(target):
    '''
    target should be a valid Submission or Comment object
    '''
    print('Replying to comment:\n\t{}: {}'.format(target.author.name, target.body))
    
    try:
        target.reply('GONK!')
    except praw.exceptions.RedditAPIException:
        print('ERROR: Doing it too often.')
        for i in range(1,11):
            print('Waiting {} more minutes...'.format(11-i))
            sleep(60)
    else:
        print('Comment posted.')
        update_log(target.id)

def update_log(comment_id):
    '''
    Adds a comment id to the log file
    '''
    with open(LOGFILE, 'a') as f:
        f.write(comment_id + '\n')
    print('Comment {} added to used list.'.format(comment_id))

def already_replied(comment_id):
    '''
    Returns True if the comment has already been replied to
    Returns False if not.
    '''
    with open(LOGFILE, 'r') as f:
        used = f.read().split()
        if comment_id in used:
            return True
        else:
            return False

def main(reddit, sub_list):

    # getting Subreddit object from list
    subreddit = reddit.subreddit('+'.join(sub_list))
    for comment in subreddit.comments():
        # if the KEYWORD is in the comment and it wasn't made by us
        # reply to comment
        if KEYWORD in comment.body.lower() and \
                comment.author.name != 'Gonk-Bot' and \
                not already_replied(comment.id):
            make_comment(comment)

if __name__ == '__main__':
    # defining constants
    KEYWORD = 'gonk'
    SUBREDDITS = ['StarWars', 'OTMemes', 'PrequelMemes', 'SequelMemes',
                'EquelMemes', 'Gonk', 'CultOfGonk', 
                'StarWarsBattlefront', 'battlefront', 'EmpireDidNothingWrong',
                'FallenOrder', 'saltierthancrait', 'Gonkwild',
                'KOTORmemes', 'starwarsmemes', 'memes',
                'StarWarsTelevision', 'TheMandalorianTV', 'SWResistance',
                'starwarsrebels', 'TheCloneWars', 'prequelappreciation',
                'StarWarsSpeculation', 'kotor', 'swtor',
                'darthjarjar', 'starwarscanon', 'starwarstattoo',
                'starwarscollecting', 'starwarscollectibles',
                'movies', 'scifi']

    LOGFILE = 'replied_to.txt'

    # checking if a log file exists
    try:
        f = open(LOGFILE, 'r')
    except FileNotFoundError:
        f = open(LOGFILE, 'w')
        f.close()
        print('Log file created')
    else:
        print('Log file found')
    # initialising Reddit instance
    r = init_bot(get_login_details('login.json'))
    print('Bot initialised. Login successful.')
    while True:
        main(r, SUBREDDITS)