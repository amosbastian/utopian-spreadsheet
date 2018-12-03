import json
import logging
import os
import re
from datetime import date, datetime, timedelta
from urllib.parse import urlparse

import gspread
from beem.comment import Comment
from beem.discussions import Discussions_by_created, Query
from oauth2client.service_account import ServiceAccountCredentials

import constants


def valid_category(tags):
    """
    Returns True if category is valid, otherwise False
    """
    for category in tags:
        if "task-" in category:
            if "bug" in category:
                return True, "task-bug-hunting"
            return True, category
        if category == "blog" or category == "blogs":
            return True, "blog"
        elif category == "iamutopian":
            return True, "iamutopian"
        elif "idea" in category or "suggestion" in category:
            return True, "ideas"
        elif category == "development":
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
        elif category == "antiabuse" or category == "anti-abuse":
            return True, "anti-abuse"
    return False, ""


def get_repository(post):
    """
    Returns the first repository found in the given post.
    """
    pattern = re.compile(constants.REPOSITORY_REGEX)
    if "links" in post.json_metadata.keys():
        for link in post.json_metadata["links"]:
            if link.startswith("/exit?url="):
                link = link[len("/exit?url="):]

            try:
                result = pattern.search(link).group(0)
                return result
            except AttributeError:
                continue
    else:
        for line in post.body.split():
            try:
                result = pattern.search(line).group(0)
                return result
            except AttributeError:
                continue

    return ""


def get_urls():
    """
    Returns all the URLs of the currently relevant worksheets.
    """
    return (constants.UNREVIEWED.col_values(3) +
            constants.REVIEWED.col_values(3) +
            constants.LAST.col_values(3))


def exponential_vote(score, category):
    """Calculates the exponential vote for the bot."""
    status = ""

    try:
        max_vote = constants.MAX_VOTE[category]
    except:
        max_vote = constants.MAX_TASK_REQUEST

    else:
        power = constants.EXP_POWER
        weight = pow(
            score / 100.0,
            power - (score / 100.0 * (power - 1.0))) * max_vote

    return float(weight)


def percentage(part, whole):
    return 100 * float(part) / float(whole)


def main():
    """Iterates over the most recently created contributions and adds them to
    the spreadsheet if not already in there.
    """
    query = Query(limit=100, tag="utopian-io")
    result = get_urls()
    moderators = [moderator["account"] for moderator
                  in constants.DB_UTEMPIAN.moderators.find()]
    for post in Discussions_by_created(query):
        steemit_url = (
            f"{constants.STEEMIT_URL}{post.category}/{post.authorperm}")
        if steemit_url not in result:

            tags = post.json_metadata["tags"]

            # Checking if valid post
            if (len(tags) < 2 or post["created"].date() < constants.THIS_WEEK):
                continue
            else:
                is_valid, category = valid_category(tags)
                if not is_valid:
                    continue
                elif (category == "translations" and
                      post.author not in constants.UTOPIAN_TRANSLATORS):
                    continue
                elif (category == "anti-abuse" and
                      post.author not in constants.UTOPIAN_ANTI_ABUSE):
                    continue
                elif (category == "iamutopian" and
                      post.author not in moderators):
                    continue
            repository = get_repository(post)

            # If user banned, set moderator as BANNED and score to 0
            if (post.author, "Yes") not in constants.BANNED_USERS:
                row = ["", "", steemit_url, repository, category]
            else:
                today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                row = ["BANNED", str(today), steemit_url, repository, category,
                       "0", "", "", "", "", 0]

            constants.UNREVIEWED.append_row(row)
            result = get_urls()


if __name__ == '__main__':
    main()
