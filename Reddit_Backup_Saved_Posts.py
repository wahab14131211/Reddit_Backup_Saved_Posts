#Import Modules
import configparser, praw, sys, os, mysql.connector, prawcore
import datetime as datetime
from pprint import pprint


def load_cred_file(cred_filename):
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
    try:
        if post.id is None or post.title is None or post.url is None:
            print(f"The post {post} does not contain a valid id or url content. Skipping...\n")
            return 1

        if post.selftext == '[deleted]':
            print(f"The post {post} was deleted. Skipping...\n")
            return 1

        if post.id in dict:
            print(f"The id {post.id} already exists in the dict. Skipping...\n")
            return 1
    except (prawcore.exceptions.Forbidden, prawcore.exceptions.NotFound):
        print (f"The post {post} does not exist. Skipping...\n")
        return 1

    dict[post.id]={}
    dict[post.id]['PostType'] = 'Submission'
    dict[post.id]['DateTime'] = datetime.date.fromtimestamp(post.created_utc).isoformat()
    dict[post.id]['Author'] = "Unknown"
    dict[post.id]['Title'] = post.title
    dict[post.id]['URL'] = post.url
    dict[post.id]['Is_Self'] = 1 if post.is_self else 0
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
    dict[comment.id]['Author'] = "Unknown"
    dict[comment.id]['Permalink'] = comment.permalink
    dict[comment.id]['LinkTitle'] = comment.link_title
    dict[comment.id]['LinkUrl'] = comment.link_url
    dict[comment.id]['Subreddit'] = comment.subreddit.display_name
    if comment.author is not None:
        dict[comment.id]['Author'] = comment.author.name
    return 0

def upload_posts_to_db(db,cursor,dict):

    #define lists to pass to the executemany commands
    saved_posts_sql_table_params = list()
    saved_submissions_sql_table_params = list()
    saved_comments_sql_table_params = list()

    #loop through saved_posts and populate the above lists
    for saved_post in dict:
        saved_posts_sql_table_params.append([
            saved_post,
            dict[saved_post]['PostType'],
            dict[saved_post]['Permalink'],
            dict[saved_post]['Author'],
            dict[saved_post]['Subreddit']
        ])
        if dict[saved_post]['PostType'] == 'Submission':
            saved_submissions_sql_table_params.append([
                saved_post,
                dict[saved_post]['Title'],
                dict[saved_post]['URL'],
                dict[saved_post]['Is_Self'],
                dict[saved_post]['Self_Text'],
                dict[saved_post]['Domain']
            ])
        elif dict[saved_post]['PostType'] == 'Comment':
            saved_comments_sql_table_params.append([
                saved_post,
                dict[saved_post]['Body'],
                dict[saved_post]['LinkTitle']
            ])
        else:
            print(f"The following post type is not supported by this script: '{type(saved_post).__name__}'. Please file a bug on the Github for an update.\n")

    saved_posts_sql_string = "INSERT IGNORE INTO RedditBackup.SavedPosts (ID, Type, Permalink, Author, Subreddit) VALUES (%s, %s, %s, %s, %s)"
    cursor.executemany(saved_posts_sql_string, saved_posts_sql_table_params)
    db.commit()

    saved_submissions_sql_string = "INSERT IGNORE INTO RedditBackup.SavedSubmissions (ID, Title, Url, IsSelf, SelfText, Domain) VALUES (%s, %s, %s, %s, %s, %s)"
    cursor.executemany(saved_submissions_sql_string, saved_submissions_sql_table_params)
    db.commit()

    saved_comment_sql_string = "INSERT IGNORE INTO RedditBackup.SavedComments (ID, Body, LinkTitle) VALUES (%s, %s, %s)"
    cursor.executemany(saved_comment_sql_string, saved_comments_sql_table_params)
    db.commit()

    return 0

def check_if_post_in_db (db, cursor, post_id):
    cursor.execute(f"SELECT ID FROM RedditBackup.SavedPosts WHERE ID='{post_id}'")
    if cursor.fetchone():
        return True
    return False

def main():
    creds = load_cred_file('./creds.ini')

    #Connect to Reddit API and test connection
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

    #connect to mysql database
    mydb = mysql.connector.connect(
        host = creds['sql']['host'],
        user = creds['sql']['username'],
        password = creds['sql']['password']
    )

    #find all saved posts (reddit only returns 2000 most recent saved posts) and populate the saved_post_dict dictionary
    saved_post_dict=dict()
    cursor = mydb.cursor()
    for saved_post in reddit_user.saved(limit=None):
        if check_if_post_in_db(mydb, cursor, saved_post.id):
            print(f"Post {saved_post} found in database. Skipping...")
            next
        if type(saved_post).__name__ == 'Submission':
            parse_submission_type_post(saved_post_dict,saved_post)
        elif type(saved_post).__name__ == 'Comment':
            parse_comment_type_post(saved_post_dict,saved_post)
        else:
            print(f"The following post type is not supported by this script: '{type(saved_post).__name__}'. Please file a bug on the Github for an update.\n")

    upload_posts_to_db(mydb, cursor, saved_post_dict)
    cursor.close()
    mydb.close()

if __name__ == "__main__":
    sys.exit(main())
