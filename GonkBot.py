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
##############
# defining constants
# if debug is active the comment will not be posted live only to STDOUT
DEBUG = False
# subreddits to scan
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
            'movies', 'scifi', 'SWDroidposting', 'StarWarsMagic',
            'CloneWarsMemes', 'andshewasagoodfriend', 'anakinfucks',
]
# file with the list of comments already been replied to
LOGFILE = 'replied_to.txt'
# list of trigger words
TRIGGERS = [
    'gonk',
    'g o n k'
]
# possible replies
REPLIES = {
    'gonk': '**GONK!**',
    'mention': '**GONK!** *<<whrrrr>>* **GONK!**   \n   \n*<<all your batteries are recharged now>>*',
    'special': "**GONK! GONK!**   \n*<<bzzzzz>> <<whrrrr>>*   \n**GONK!**   \n*<<busy gonk noises>>*   \n**GONK!**    \n    \n*|Gonk supercharged your batteries. They're on 200% for a day!|*"
}

#################

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
        else:
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

###########################

def check_trigger_word(comment):
    '''
    Checks if any of the trigger words is in the comment body.
    '''
    if any(trigger_word in comment.body.lower() for trigger_word in TRIGGERS):
        return True
    else:
        return False

def check_mention(comment):
    '''
    Checks if the comment was made in reply to the bot's comment.
    '''
    parent_comment = comment.parent()
    if not parent_comment \
        or not isinstance(parent_comment, praw.models.Comment) \
        or not parent_comment.author:
        return False
    elif parent_comment.author.name == 'Gonk-Bot':
        return True
    else:
        return False

def check_special(comment):
    '''
    Checks if the special trigger sentence was called.
    '''
    special = "Help me, Gonky-Wan Kenobi. You're my only hope."
    if special == comment.body:
        return True
    else:
        return False

def make_comment(target, message):
    '''
    target  - a valid Submission or Comment object
    message - the string the bot will post
    '''
    print('Replying to comment:\n\t{}: {}'.format(target.author.name, target.body))
    
    try:
        if DEBUG:
            print('Message: {}'.format(message))
        else:
            target.reply(message)
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

    # scan the comment stream
    for comment in subreddit.comments():
        # skip if it's the bot's comment or it has been replied to
        if comment.author.name == 'Gonk-Bot' or \
            already_replied(comment.id):
            next
        # check for special call
        elif check_special(comment):
            make_comment(comment, REPLIES['special'])
            next
        # bot was talked to
        elif check_mention(comment):
            make_comment(comment, REPLIES['mention'])
            next      
        # comment was made to submission and it's 'gonk'
        elif check_trigger_word(comment):
            make_comment(comment, REPLIES['gonk'])
            next

        

if __name__ == '__main__':
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
