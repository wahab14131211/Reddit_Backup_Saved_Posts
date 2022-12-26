#Import Modules
import configparser, praw, sys, os
import datetime as datetime
from pprint import pprint


def load_cred_file(): #TODO: Change cred fileformat to python config. Add SQL credentials into this file as well, and create a template file
    cred_filename = "creds.ini"
    expected_creds = {
        "reddit" : ["client_id", "client_secret", "user_agent", "redirect_uri", "refresh_token"],
        "sql" : ["host","username","password"]
    }

    #check if credential file exists
    if not os.path.exists(cred_filename):
        print("The creds.ini file does not exist in this folder. Please create this file and rerun this script.\n")
        print("Please follow the instructions on the following website: https://www.jcchouinard.com/get-reddit-api-credentials-with-praw/ to populate the reddit section of the config file, and use your mySQL user info for the sql section of the config file\n")
        sys.exit(1)

    #read the credential file
    creds = configparser.ConfigParser()
    creds.read(cred_filename)

    #error check credentials to make sure all needed keys exist
    for expected_table in expected_creds.keys():
        if expected_table not in creds.keys():
            print(f"the creds.ini file was expected to have the \"{expected_table}\" table. Please add this table to the file and rerun this script.\n")
        for expected_field in expected_creds[expected_table]:
            if expected_field not in creds[expected_table]:
                print(f"The creds.ini file was expected to have the \"{expected_table}\" table with the \"{expected_field}\" key. Please add this table/key to the file and rerun this script.\n")
                sys.exit(1)

    print("Credential file loaded successfully.\n", file=sys.stderr)
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
    creds = load_cred_file()
    reddit = praw.Reddit(
        client_id = creds['reddit']['client_id'],
        client_secret = creds['reddit']['client_secret'],
        user_agent = creds['reddit']['user_agent'],
        refresh_token = creds['reddit']['refresh_token']
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
