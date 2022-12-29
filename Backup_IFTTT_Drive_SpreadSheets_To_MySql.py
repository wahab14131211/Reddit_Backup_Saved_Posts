from oauth2client.service_account import ServiceAccountCredentials
import gspread, re, sys, pprint, praw, json, mysql.connector
from Reddit_Backup_Saved_Posts import load_cred_file, parse_submission_type_post, upload_posts_to_db

def get_spreadsheet_number(name):
    num = 0
    if match := re.search(r'\((\d+)\)$', name):
        num = int(match.group(1))
    return num

def main():
    #load the main cred file to connect to reddit and sql APIs
    reddit_sql_creds = load_cred_file('creds.ini')

    #connect to google sheets APIs
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    google_creds = ServiceAccountCredentials.from_json_keyfile_name("Misc/Google_Creds.json", scope)
    client = gspread.authorize(google_creds)
    spreadsheet_files = client.list_spreadsheet_files()
    spreadsheet_files = [spreadsheet_file["name"] for spreadsheet_file in spreadsheet_files]
    spreadsheet_files.sort(key=get_spreadsheet_number)

    #connect to reddit API
    reddit = praw.Reddit(
        client_id = reddit_sql_creds['reddit']['client_id'],
        client_secret = reddit_sql_creds['reddit']['client_secret'],
        user_agent = reddit_sql_creds['reddit']['user_agent'],
        refresh_token = reddit_sql_creds['reddit']['refresh_token']
    )
    try:
        reddit_user = reddit.user.me()
    except:
        print("Not able to connect to reddit. Please make sure your API credentials are correct.")
        return 1
    print(f"Reddit username is {reddit_user.name}\n", file=sys.stderr)

    #get a list of all saved posts from the google sheets
    reddit_urls=list()
    for spreadsheet_file_name in spreadsheet_files:
        print (f"Processing {spreadsheet_file_name} file")
        sheet = client.open(spreadsheet_file_name).sheet1
        for row in sheet.get_all_values():
            url = row[6]
            url = url.replace(r'/?utm_source=ifttt','')
            reddit_urls.append(url)

    saved_post_dict = dict()
    total_saved_posts = len(reddit_urls)
    counter = 0
    for reddit_url in reddit_urls:
        counter += 1
        print (f"current url is {reddit_url}")
        post = reddit.submission(url=reddit_url)
        parse_submission_type_post(saved_post_dict, post)
        print(f"Done parsing {counter} out of {total_saved_posts} posts\n")

    with open('saved_post_dict.json','w') as fp:
        json.dump(saved_post_dict,fp,indent=4)

    #If something went wrong in the upload step, comment out all lines in the main above this, and uncomment the 3 lines below this to reload the saved_post_dict backup cred_filename
    #reddit_sql_creds = load_cred_file('creds.ini')
    #with open('saved_post_dict.json','r') as fp:
    #    saved_post_dict = json.load(fp)

    #connect to mysql database
    mydb = mysql.connector.connect(
        host = reddit_sql_creds['sql']['host'],
        user = reddit_sql_creds['sql']['username'],
        password = reddit_sql_creds['sql']['password']
    )
    cursor = mydb.cursor()
    upload_posts_to_db(mydb, cursor, saved_post_dict)
    cursor.close()
    mydb.close()

if __name__ == "__main__":
    sys.exit(main())
