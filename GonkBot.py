import praw
from time import sleep
import os, sys
import json
import argparse
import hashlib, time

# processing arguments
parser = argparse.ArgumentParser()
parser.add_argument('--debug', action='store_true',
                    help='Enables debug mode')

args = parser.parse_args()
if args.debug:
    print('INTERACTIVE MODE')

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
# subreddits to scan
SUBREDDITS = ['OTMemes', 'PrequelMemes', 'SequelMemes',
            'EquelMemes', 'Gonk', 'CultOfGonk', 
            'StarWarsBattlefront', 'battlefront', 'EmpireDidNothingWrong',
            'FallenOrder', 'saltierthancrait', 'Gonkwild',
            'KOTORmemes', 'starwarsmemes', 'memes',
            'StarWarsTelevision', 'TheMandalorianTV', 'SWResistance',
            'starwarsrebels', 'TheCloneWars', 'prequelappreciation',
            'StarWarsSpeculation', 'swtor',
            'darthjarjar', 'starwarscanon', 'starwarstattoo',
            'starwarscollecting', 'starwarscollectibles',
            'movies', 'scifi']
# file with the list of comments already been replied to
LOGFILE = 'debug.log' if args.debug else 'replied_to.txt'
# list of trigger words
TRIGGERS = [
    'gonk',
    'g o n k'
]
# possible replies
REPLIES = {
    'gonk': '**GONK!**',
    'mention': '**GONK!** *<<whrrrr>>* **GONK!**   \n   \n*<<all your batteries are recharged now>>*',
    'special': "**GONK! GONK!**   \n*<<bzzzzz>> <<whrrrr>>*   \n**GONK!**   \n*<<busy gonk noises>>*   \n**GONK!**    \n    \n*|Gonk supercharged your batteries. They're on 200% for a day!|*",
    'pushed': '**thud**    \n*falls over*    \nGONK GONK GONK',
    'fallen': '*GONK has fallen and cannot gonk. To help him up, reply "help gonk"',
    'helped': '❤️**GONK**❤️    \n*<<thankful gonk noises>>*'
}

class GonkBot:

    def __init__(self):       
        # global that controls if the bot will reply
        self.inactive = False

    def init_bot(self, login_file):
        '''
        Return the login info as a dictionary.
        It contains the following keys:
        client_id
        client_secret
        user_agent
        user_name
        password
        '''

        if args.debug:
            return None

        login = {}
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
            f.close()
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
            return praw.Reddit( client_id     = login.get('client_id'),
                                client_secret = login.get('client_secret'),
                                user_agent    = login.get('user_agent'),
                                username      = login.get('username'),
                                password      = login.get('password')
                                )

    def check_trigger_word(self, comment):
        '''
        Checks if any of the trigger words is in the comment body.
        '''
        if any(trigger_word in comment.body.lower() for trigger_word in TRIGGERS):
            return True
        else:
            return False
    
    def check_pushed(self, comment):
        '''
        GONK can be pushed.
        '''
        return ('push' in comment.body.lower() \
            and 'gonk' in comment.body.lower())

    def check_helped(self, comment):
        '''
        if GONK is helped up it's no longer inactive
        '''
        return 'help gonk' in comment.body.lower()

    def check_mention(self, comment):
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

    def check_special(self, comment):
        '''
        Checks if the special trigger sentence was called.
        '''
        special = "Help me, Gonky-Wan Kenobi. You're my only hope."
        return special == comment.body

    def make_comment(self, target, message):
        '''
        target  - a valid Submission or Comment object
        message - the string the bot will post
        '''
        print('Replying to comment:\n\t{}: {}'.format(target.author.name, target.body))
        
        try:
            if args.debug:
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
            self.update_log(target.id)

    def update_log(self, comment_id):
        '''
        Adds a comment id to the log file
        '''
        with open(LOGFILE, 'a') as f:
            f.write(comment_id + '\n')
        print('Comment {} added to used list.'.format(comment_id))

    def already_replied(self, comment_id):
        '''
        Returns True if the comment has already been replied to
        Returns False if not.
        '''
        with open(LOGFILE, 'r') as f:
            used = f.read().split()
            return comment_id in used

def debug_comment_stream():
    comment = input('>')
    if comment == 'exit':
        print('Exiting interactive mode.')
        sys.exit(0)

    class DummyComment: pass
    class Author: pass
    Author.name = 'interactive'
    DummyComment.id = hashlib.md5(str(time.time()).encode('utf-8')).hexdigest()
    DummyComment.body = comment
    DummyComment.parent = lambda: 'parent comment'
    DummyComment.author = Author 

    return [ DummyComment ]

def main(bot, reddit, sub_list):

    # getting Subreddit object from list
    if reddit:
        subreddit = reddit.subreddit('+'.join(sub_list))
        comment_stream = subreddit.comments()
    else:
        # interactive mode if in debug
        comment_stream =  debug_comment_stream()

    # scan the comment stream
    for comment in comment_stream:
        if comment.author.name == 'Gonk-Bot' or \
            comment.author.name == 'clone_trooper_bot' or \
            bot.already_replied(comment.id):
            next
        elif bot.inactive and bot.check_helped(comment):
            bot.make_comment(comment, REPLIES['helped'])
            bot.inactive = False
            next
        elif bot.inactive and bot.check_mention(comment):
            bot.make_comment(comment, REPLIES['fallen'])
            next
        # check for special call
        elif bot.check_special(comment):
            bot.make_comment(comment, REPLIES['special'])
            next
        elif bot.check_pushed(comment):
            bot.make_comment(comment, REPLIES['pushed'])
            bot.inactive = True
            next
        # bot was talked to
        elif bot.check_mention(comment):
            bot.make_comment(comment, REPLIES['mention'])
            next      
        # comment was made to submission and it's 'gonk'
        elif bot.check_trigger_word(comment):
            bot.make_comment(comment, REPLIES['gonk'])
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
    bot = GonkBot()
    r = bot.init_bot('login.json')
    print('Bot initialised. Login successful.')
    
    while True:
        main(bot, r, SUBREDDITS)
