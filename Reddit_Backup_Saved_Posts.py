#Import Modules
import json, praw, sys, os
import datetime as datetime
from pprint import pprint


def load_reddit_cred_file(): #TODO: Change cred fileformat to python config. Add SQL credentials into this file as well, and create a template file
    cred_filename = "reddit_creds.json"
    expected_fields = ["client_id", "client_secret", "user_agent", "redirect_uri", "refresh_token"]

    #check if credential file exists
    if not os.path.exists(cred_filename):
        print("The reddit_creds.json file does not exist in this folder. Please create this file and rerun this script.\n")
        print("Please follow the instructions on the following website: https://www.jcchouinard.com/get-reddit-api-credentials-with-praw/\n")
        sys.exit(1)

    #read the credential file
    with open(cred_filename) as file:
        creds = json.load(file)

    #error check credentials to make sure all needed keys exist
    for expected_field in expected_fields:
        if expected_field not in creds:
            print(f"The reddit_creds.json file was expected to have the \"{expected_field}\" key. Please add this key to the file and rerun this script.\n")
            sys.exit(1)

    print("Reddit credential file loaded successfully.\n", file=sys.stderr)
    return creds

def parse_submission_type_post(dict,post):
    if post.id is None or post.title is None or post.url is None:
        print(f"The post {post} does not contain a valid id or url content. Skipping...\n")
        return 1

    if post.selftext == '[deleted]':
        print(f"The post {post} was deleted. Skipping...\n")
        return 1

    if post.id in dict:
        print(f"The id {saved_post.id} already exists in the dict. This id should be unique. Please file a bug on the Github on this issue.\n")
        return 1

    dict[post.id]={}
    dict[post.id]['PostType'] = 'Submission'
    dict[post.id]['DateTime'] = datetime.date.fromtimestamp(post.created_utc).isoformat()
    dict[post.id]['Author'] = "Unknown"
    dict[post.id]['Title'] = post.title
    dict[post.id]['URL'] = post.url
    dict[post.id]['Is_Self'] = post.is_self
    dict[post.id]['Self_Text'] = post.selftext_html
    dict[post.id]['Subreddit'] = post.subreddit.display_name
    dict[post.id]['Permalink'] = post.permalink
    dict[post.id]['Domain'] = post.domain
    if post.author is not None:
        dict[post.id]['Author'] = post.author.name
    return 0

def parse_comment_type_post(dict,comment):
    if comment.id is None:
        print(f"The comment {comment} does not contain a valid id. Skipping...\n")
        return 1

    if comment.id in dict:
        print(f"The id {saved_comment.id} already exists in the dict. This id should be unique. Please file a bug on the Github on this issue.\n")
        return 1

    dict[comment.id] = {}
    dict[comment.id]['PostType'] = 'Comment'
    dict[comment.id]['Body'] = comment.body_html
    dict[comment.id]['DateTime'] = datetime.date.fromtimestamp(comment.created_utc).isoformat()
    dict[comment.id]['Permalink'] = comment.permalink
    dict[comment.id]['LinkTitle'] = comment.link_title
    dict[comment.id]['LinkUrl'] = comment.link_url
    dict[comment.id]['Subreddit'] = comment.subreddit.display_name
    if comment.author is not None:
        dict[comment.id]['Author'] = comment.author.name
    return 0


def main():
    reddit_creds = load_reddit_cred_file()
    reddit = praw.Reddit(
        client_id = reddit_creds['client_id'],
        client_secret = reddit_creds['client_secret'],
        user_agent = reddit_creds['user_agent'],
        refresh_token = reddit_creds['refresh_token']
    )

    try:
        reddit_user = reddit.user.me()
    except:
        print("Not able to connect to reddit. Please make sure your API credentials are correct.\n")
        return 1

    print(f"Reddit username is {reddit_user.name}\n", file=sys.stderr)

    saved_post_dict=dict()
    for saved_post in reddit_user.saved(limit=None):
        if type(saved_post).__name__ == 'Submission':
            parse_submission_type_post(saved_post_dict,saved_post)
        elif type(saved_post).__name__ == 'Comment':
            parse_comment_type_post(saved_post_dict,saved_post)
        else:
            print("The following post type is not supported by this script. Please file a bug on the Github for an update.\n")

    pprint(saved_post_dict)

#        if saved_post.id not in test_list:
#            print(f"NEW: Post ID is: {saved_post.id}\n")
#            test_list.append(saved_post.id)
#        else:
#            print(f"DUPLICATED: post ID is: {saved_post.id}, Post creation datetime is: {datetime.date.fromtimestamp(saved_post.created_utc)}, OP is {saved_post.author.name}, Title is {saved_post.title}\n")

if __name__ == "__main__":
    sys.exit(main())
