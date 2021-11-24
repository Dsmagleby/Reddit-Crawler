import praw
from prawcore import NotFound
import pandas as pd
import sys
sys.path.append("/credentials")
import credentials as cred
import argparse


# parse comandline arguments
parser = argparse.ArgumentParser(description='Search configurations')
parser.add_argument('--sub', dest='subreddit', type=str, help='Name of the subreddit(s) seperate with +')
parser.add_argument('--cat', dest='category', type=str, help='Post category: hot, new or top')
parser.add_argument('--num', dest='amount', type=int, help='Number of posts to crawl (1 - 1000)')
parser.add_argument('--o', dest='output', type=str, help='Name of output .csv file')
args = parser.parse_args()


# check if valid amount
if (args.amount < 0 or args.amount > 1001):
    print("Number of posts must be between 1 and 1000\n")
    sys.exit()

if (cred.client_id == "my_client_id"):
    print("In order to use the crawler, please paste your client_id and client_secret\n")
    print("into the file credentials.py, these are gotten from:\n")
    print("https://www.reddit.com/prefs/apps, navigate to create application\n")
    print("give app a name and choose \'script\', then create app\n")
    print("copy client_id and client_secret into credentials.py\n")
    sys.exit()


# request api access
reddit = praw.Reddit(client_id=cred.client_id,
                     client_secret=cred.client_secret,
                     user_agent=cred.user_agent)


def sub_exists(sub):
    exists = True
    try:
        reddit.subreddits.search_by_name(sub, exact=True)
    except NotFound:
        exists = False
    return exists

# check if subreddit exists
if (args.subreddit == None):
    print("No subreddit defined\n") 
    sys.exit()

sub_list = args.subreddit.split('+')
for sub in sub_list:
    if sub_exists(sub):
        continue
    else:
        print("Subreddit %s does not exist or is private\n" % sub)
        sys.exit()


# check if category is valid
if (args.category == "hot" ):
    subreddit = reddit.subreddit(args.subreddit).hot(limit=args.amount)
elif (args.category == "new"):
    subreddit = reddit.subreddit(args.subreddit).new(limit=args.amount)
elif (args.category == "top"):
    subreddit = reddit.subreddit(args.subreddit).top(limit=args.amount)
else:
    print("Invalid category %s, valid categories are: hot, new and top\n" % args.category)
    sys.exit()


# crawl posts
posts = []
for post in subreddit:
    posts.append([post.title, "post", post.author, post.score, post.id, post.subreddit, post.url, post.num_comments, post.selftext, post.created])
posts = pd.DataFrame(posts,columns=['title', 'type', 'author', 'score', 'id', 'subreddit', 'url', 'num_comments', 'body', 'created'])
print(posts)


# crawl post comments
print("Now showing %d posts being processed:" % len(posts.index))
result = posts
for id in posts["id"]:
    comments = []
    submission = reddit.submission(id=id)
    print(posts.loc[posts['id'] == id]['title'].item())
    submission.comments.replace_more(limit=None)
    for comment in submission.comments.list():
        comments.append([None, "comment", comment.author, comment.score, comment.id, comment.subreddit, None, None, comment.body, comment.created])
    comments = pd.DataFrame(comments,columns=['title', 'type', 'author', 'score', 'id', 'subreddit', 'url', 'num_comments', 'body', 'created'])
    result = result.append(comments).reset_index(drop=True)
print(result)


# save posts + comments to .csv
# check if output name contains .csv and handle
if (args.output[-4:] == ".csv"):
    result.to_csv(args.output)
else:
    result.to_csv(args.output + '.csv')
