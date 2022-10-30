#Import Modules
import json, praw, sys, os
import datetime as datetime


def load_reddit_cred_file():
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

if __name__ == "__main__":
    sys.exit(main())
