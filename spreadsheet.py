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
utopian_fest = sheet.worksheet("Utopian Fest")

# Get all relevant URLs
banned_sheet = sheet.worksheet("Banned users")
banned_users = zip(banned_sheet.col_values(1), banned_sheet.col_values(4))

# Get all translators
translator_sheet = sheet.worksheet("Translators")
UTOPIAN_TRANSLATORS = translator_sheet.col_values(1)[1:]

# URL
URL = "https://steemit.com/"

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
    "blog": 2.25,
    "translations": 4.0
}


def valid_category(tags):
    """Returns True if category is valid, otherwise False"""
    for category in tags:
        if "task" in category:
            if "bug" in category:
                return True, "task-bug-hunting"
            return True, category
        if category == "blog" or category == "blogs":
            return True, "blog"
        elif "idea" in category or "suggestion" in category:
            return True, "ideas"
        elif "develop" in category:
            return True, "development"
        elif category == "graphic" or category == "graphics":
            return True, "graphics"
        elif "bughunt" in category or "bug-hunt" in category:
            return True, "bug-hunting"
        elif "analysis" in category:
            return True, "analysis"
        elif "visibility" in category or "social" in category:
            return True, "social"
        elif "videotut" in category or "video-tut" in category:
            return True, "video-tutorials"
        elif category == "tutorial" or category == "tutorials":
            return True, "tutorials"
        elif "copywrit" in category:
            return True, "copywriting"
        elif "document" in category:
            return True, "documentation"
        elif "translation" in category:
            return True, "translations"
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
        moderators.setdefault(moderator["account"], {
            "points": 0,
            "reviewed": 0
        })

    # Zip moderator's name and category together
    data = zip(reviewed.col_values(1), reviewed.col_values(5))
    for moderator, category in data:
        try:
            moderator = moderator.lower().strip()
        except Exception:
            pass

        if moderator == "banned" or moderator == "moderator":
            continue

        # Moderator not in database!
        if moderator not in moderators.keys():
            moderators[moderator] = {
                "points": 0,
                "reviewed": 0
            }

        try:
            # Normal contribution
            moderators[moderator]["points"] += CATEGORIES[category]
        except:
            # Task request
            moderators[moderator]["points"] += 1.25

        moderators[moderator]["reviewed"] += 1

    # Check if moderator if community manager -> add 100 points
    community_managers = [
        moderator["account"] for moderator in
        collection.find({"supermoderator": True})]

    for moderator, value in moderators.items():
        if moderator in community_managers:
            value["points"] += 100.0

            # Check for BOSSPOEM or TECHSLUT
            if moderator == "espoem" or moderator == "techslut":
                value["points"] = 400.0
        else:
            if value["reviewed"] >= 5:
                value["points"] += 30.0

        # Utopian Fest bonus
        if moderator in utopian_fest.col_values(1):
            value["points"] += 50.0

        moderators[moderator] = value["points"]

    # Save dictionary as JSON with date of last Thursday
    with open(
            f"/home/amos/utopian/utopian/static/{this_week}.json",
            "w") as fp:
        json.dump(moderators, fp, indent=4)


def get_urls():
    return (unreviewed.col_values(3) +
            reviewed.col_values(3) +
            last.col_values(3))


def banned_comment(url):
    """
    Comments on the given contribution letting them know that they are banned.
    """
    post = Comment(url)
    comment = (
        f"Hi, @{post.author}. Your account has been excluded from the Utopian "
        "rewarding system and therefore this contribution post will not be "
        "reviewed. You can contact us at https://support.utopian.io/ if you "
        "have any further questions.")
    post.reply(comment, author="amosbastian")


def main():
    """
    Iterates over the most recently created contributions and adds them to the
    spreadsheet if not already in there.
    """
    query = Query(limit=100, tag="utopian-io")
    result = get_urls()
    for post in Discussions_by_created(query):
        steemit_url = f"{URL}{post.category}/{post.authorperm}"
        if steemit_url not in result:

            tags = post.json_metadata["tags"]

            # Checking if valid post
            if (len(tags) < 2 or post["created"].date() < this_week):
                continue
            else:
                is_valid, category = valid_category(tags)
                if not is_valid:
                    logger.error(f"{steemit_url} has tags: {tags} and was not "
                                 "added")
                    continue
                elif (category == "translations" and
                      post.author not in UTOPIAN_TRANSLATORS):
                    logger.error(f"{steemit_url} not made by accepted "
                                 f"translator!")
                    continue
            repository = get_repository(post)

            # If user banned, set moderator as BANNED and score to 0
            if (post.author, "Yes") not in banned_users:
                row = ["", "", steemit_url, repository, category]
            else:
                row = ["BANNED", str(today), steemit_url, repository, category,
                       "0", "", "", "", 0]
                logger.info(f"Commenting on {steemit_url} letting them know "
                            "that they are banned.")
                banned_comment(steemit_url)
            unreviewed.append_row(row)
            result = get_urls()
            logger.info(f"{steemit_url} has tags: {tags} and was added to the "
                        "spreadsheet.")

    moderator_points()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        logger.error(error)
