from beem.discussions import Query, Discussions_by_created
from datetime import date, timedelta
from oauth2client.service_account import ServiceAccountCredentials
from pymongo import MongoClient
from urllib.parse import urlparse

import gspread
import json
import pprint

# Everything outside because I can't be bothered doing this properly
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    "/home/amos/utopian-spreadsheet/client_secret.json", scope)
client = gspread.authorize(credentials)
sheet = client.open("Utopian Reviews")
pp = pprint.PrettyPrinter()
reviews = sheet.get_worksheet(0)
reviewed = sheet.get_worksheet(-1)
result = reviews.col_values(3) + reviewed.col_values(3)

banned_sheet = sheet.get_worksheet(1)
banned_users = zip(banned_sheet.col_values(1), banned_sheet.col_values(4))
URL = "https://steemit.com/utopian-io/"

# MongoDB
CLIENT = MongoClient()
DB = CLIENT.utopian

CATEGORIES = {
    "ideas": 2.0,
    "development": 4.25,
    "graphics": 3.0,
    "bug-hunting": 3.25,
    "analysis": 3.25,
    "social": 2.0,
    "video-tutorials": 4.0,
    "tutorials": 4.0,
    "copywriting": 2.0,
    "documentation": 2.25,
    "blog": 2.25
}


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
    try:
        for link in post.json_metadata["links"]:
            if url in link:
                return link
    except KeyError:
        pass
    return ""


def moderator_points():
    """Return a dict containing a moderator and their points."""
    moderators = {}

    # Include moderators who haven't reviewed anything yet
    collection = DB.moderators
    for moderator in collection.find():
        moderators.setdefault(moderator["account"], 0)

    # Zip moderator's name and category together
    data = zip(reviewed.col_values(1), reviewed.col_values(5))
    for moderator, category in data:
        if moderator in ("", "Moderator", "BANNED"):
            continue

        # Remove whitespace and count points
        moderator = moderator.strip()
        try:
            moderators[moderator] += CATEGORIES[category]
        except:
            moderators[moderator] += 1.25

    # Check if moderator if community manager -> add 100 points
    community_managers = collection.find({"supermoderator": True})
    for manager in community_managers:
        try:
            moderators[manager["account"]] += 100.0
        except:
            continue

    # Save dictionary as JSON with date of last Thursday
    today = date.today()
    offset = (today.weekday() - 3) % 7
    last_thursday = today - timedelta(days=offset)
    with open(
            f"/home/amos/utopian/utopian/static/{last_thursday}.json",
            "w") as fp:
        json.dump(moderators, fp, indent=4)


def main():
    today = date.today()
    offset = (today.weekday() - 3) % 7
    last_thursday = today - timedelta(days=offset)
    query = Query(limit=100, tag="utopian-io")
    for post in Discussions_by_created(query):
        steemit_url = f"{URL}{post.authorperm}"
        if steemit_url not in result:
            tags = post.json_metadata["tags"]
            if (post.category != "utopian-io" or
                    len(tags) < 2 or
                    post["created"].date() < last_thursday):
                continue
            else:
                category = tags[1]
                if not valid_category(category):
                    continue
            repository = get_repository(post)
            if (post.author, "Yes") not in banned_users:
                row = ["", "", steemit_url, repository, category]
            else:
                row = ["BANNED", "", steemit_url, repository, category, "0"]
            reviews.append_row(row)

    moderator_points()


if __name__ == '__main__':
    main()
