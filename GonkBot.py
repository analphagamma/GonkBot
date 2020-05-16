import praw
from time import sleep

KEYWORD = 'gonk'
SUBREDDITS = ['StarWars', 'OTMemes', 'PrequelMemes', 'SequelMemes',
              'EquelMemes', 'legostarwars', 'Gonk', 'CultOfGonk', 
              'StarWarsBattlefront', 'starwarsmemes', 'EmpireDidNothingWrong']

TESTSUBREDDITS = ['NoVowelBotTest']

LOGFILE = 'replied_to.txt'
            
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

def main(sub_list):
    # initialising Reddit instance
    r = praw.Reddit('GonkBot')
    # getting Subreddit object from list
    subreddit = r.subreddit('+'.join(sub_list))
    for comment in subreddit.comments():
        # if the KEYWORD is in the comment and it wasn't made by us
        # reply to comment
        if KEYWORD in comment.body.lower() and \
                comment.author.name != 'Gonk-Bot' and \
                not already_replied(comment.id):
            make_comment(comment)    

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

    while True:
        main(SUBREDDITS)