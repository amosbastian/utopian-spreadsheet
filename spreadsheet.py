from beem.discussions import Query, Discussions_by_created
from oauth2client.service_account import ServiceAccountCredentials
from urllib.parse import urlparse
import gspread
import pprint

# Everything outside because I can't be bothered doing this properly
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    "/home/amos/Documents/utopian-sheet/client_secret.json", scope)
client = gspread.authorize(credentials)
sheet = client.open("Utopian Reviews").get_worksheet(0)
pp = pprint.PrettyPrinter()
result = sheet.col_values(3)
banned_sheet = client.open("Utopian Reviews").get_worksheet(1)
banned_users = banned_sheet.col_values(1)
URL = "https://steemit.com/utopian-io/"


def valid_category(category):
    """Returns True if category is valid, otherwise False"""
    if (category in ("ideas", "development", "graphics", "bug-hunting",
                     "analysis", "social", "video-tutorials", "tutorials",
                     "copywriting", "documentation", "blog") or
            "task" in category):
        return True
    else:
        return False


def get_repository(post):
    """Returns the first repository found in the given post."""
    url = "github.com/"
    for link in post.json_metadata["links"]:
        if url in link:
            return link
    return ""


def main():
    query = Query(limit=100, tag="utopian-io")
    for post in Discussions_by_created(query):
        steemit_url = f"{URL}{post.authorperm}"
        if steemit_url not in result:
            tags = post.json_metadata["tags"]
            if post.category != "utopian-io" or len(tags) < 2:
                continue
            else:
                category = tags[1]
                if not valid_category(category):
                    continue
            repository = get_repository(post)
            if post.author not in banned_users:
                row = ["", "", steemit_url, repository, category]
            else:
                row = ["BANNED", "", steemit_url, repository, category, "0"]
            sheet.append_row(row)


if __name__ == '__main__':
    main()
