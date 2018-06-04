from beem.discussions import Query, Discussions_by_created
from beem.comment import Comment
from datetime import date, timedelta
from oauth2client.service_account import ServiceAccountCredentials
from pymongo import MongoClient
from urllib.parse import urlparse

import gspread
import json
import logging
import os

# Get path of current folder
DIR_PATH = os.path.dirname(os.path.realpath(__file__))

# Logging
logger = logging.getLogger("utopian-io")
logger.setLevel(logging.INFO)
fh = logging.FileHandler(f"{DIR_PATH}/spreadsheet.log")
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
logger.addHandler(fh)

# Spreadsheet
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    f"{DIR_PATH}/client_secret.json", scope)
client = gspread.authorize(credentials)
sheet = client.open("Utopian Reviews")

# Dates
today = date.today()
offset = (today.weekday() - 3) % 7
this_week = today - timedelta(days=offset)
next_week = this_week + timedelta(days=7)
last_week = this_week - timedelta(days=7)

# Use title to select worksheet
title_unreviewed = f"Unreviewed - {this_week:%b %-d} - {next_week:%b %-d}"
title_reviewed = f"Reviewed - {this_week:%b %-d} - {next_week:%b %-d}"
title_last = f"Reviewed - {last_week:%b %-d} - {this_week:%b %-d}"

# Get all relevant worksheets
unreviewed = sheet.worksheet(title_unreviewed)
reviewed = sheet.worksheet(title_reviewed)
last = sheet.worksheet(title_last)

# Get all relevant URLs
banned_sheet = sheet.worksheet("Banned users")
banned_users = zip(banned_sheet.col_values(1), banned_sheet.col_values(4))

# URL
URL = "https://steemit.com/utopian-io/"

# MongoDB
CLIENT = MongoClient()
DB = CLIENT.utopian

# Points per category
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
    if "blog" in category or "task" in category:
        if "bug" in category:
            return True, "task-bug-hunting"
        return True, category
    elif "idea" in category or "suggestion" in category:
        return True, "ideas"
    elif "develop" in category:
        return True, "development"
    elif "graphic" in category:
        return True, "graphics"
    elif "bug" in category or "hunt" in category:
        return True, "bug-hunting"
    elif "anal" in category:
        return True, "analysis"
    elif "visibility" in category or "social" in category:
        return True, "social"
    elif "video" in category:
        return True, "video-tutorials"
    elif category == "tutorial" or category == "tutorials":
        return True, "tutorials"
    elif "copy" in category:
        return True, "copywriting"
    elif "docu" in category:
        return True, "documentation"
    else:
        return False, ""


def get_repository(post):
    """Returns the first repository found in the given post."""
    url = "github.com/"
    try:
        for link in post.json_metadata["links"]:
            if url in link:
                if link.startswith("/exit?url="):
                    link = link[len("/exit?url="):]
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
        try:
            moderator = moderator.lower()
        except Exception:
            pass
        if moderator in ("", "moderator", "banned"):
            continue
        moderators.setdefault(moderator, 0)
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
    with open(
            f"/home/amos/utopian/utopian/static/{this_week}.json",
            "w") as fp:
        json.dump(moderators, fp, indent=4)


def get_urls():
    return (unreviewed.col_values(3) +
            reviewed.col_values(3) +
            last.col_values(3))


def main():
    """
    Iterates over the most recently created contributions and adds them to the
    spreadsheet if not already in there.
    """
    query = Query(limit=100, tag="utopian-io")
    result = get_urls()
    for post in Discussions_by_created(query):
        steemit_url = f"{URL}{post.authorperm}"
        if steemit_url not in result:

            tags = post.json_metadata["tags"]

            # Checking if valid post
            if (post.category != "utopian-io" or
                    len(tags) < 2 or
                    post["created"].date() < this_week):
                continue
            else:
                category = tags[1]
                is_valid, category = valid_category(category)
                if not is_valid:
                    logger.error(f"{steemit_url} has tags: {tags} and was not "
                                 "added")
                    continue
            repository = get_repository(post)

            # If user banned, set moderator as BANNED and score to 0
            if (post.author, "Yes") not in banned_users:
                row = ["", "", steemit_url, repository, category]
            else:
                row = ["BANNED", str(today), steemit_url, repository, category,
                       "0", "", "", "", 0]
            unreviewed.append_row(row)
            result = get_urls()
            logger.info(f"Adding {steemit_url} to the spreadsheet.")

    moderator_points()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        logger.error(error)
