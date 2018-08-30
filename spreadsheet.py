from beem.discussions import Query, Discussions_by_created
from beem.comment import Comment
from datetime import date, timedelta
from oauth2client.service_account import ServiceAccountCredentials
from urllib.parse import urlparse

import constants
import gspread
import json
import logging
import os


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
    return False, ""


def get_repository(post):
    """
    Returns the first repository found in the given post.
    """
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
    """
    Return a dictionary containing a moderator and their points.
    """
    moderators = {}
    collection = constants.DB.moderators

    community_managers = [
        moderator["account"] for moderator in
        collection.find({"supermoderator": True})]

    utopian_fest = constants.UTOPIAN_FEST.col_values(1)

    for moderator in set(community_managers + utopian_fest):
        moderators.setdefault(moderator, 0)
        if moderator in community_managers:
            moderators[moderator] += 100.0

            # Check for BOSSPOEM or TECHSLUT
            if moderator == "espoem" or moderator == "techslut":
                moderators[moderator] = 400.0

        # Utopian Fest bonus
        if moderator in utopian_fest:
            moderators[moderator] += 50.0

    # Save dictionary as JSON with date of last Thursday
    with open(
            f"/home/amos/utopian/utopian/static/{constants.THIS_WEEK}.json",
            "w") as fp:
        json.dump(moderators, fp, indent=4)


def get_urls():
    """
    Returns all the URLs of the currently relevant worksheets.
    """
    return (constants.UNREVIEWED.col_values(3) +
            constants.REVIEWED.col_values(3) +
            constants.LAST.col_values(3))


def banned_comment(url):
    """
    Comments on the given contribution letting them know that they are banned.
    """
    post = Comment(url)
    comment = constants.COMMENT_BANNED.format(post.author)
    post.reply(comment, author="amosbastian")


def main():
    """
    Iterates over the most recently created contributions and adds them to the
    spreadsheet if not already in there.
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
                    constants.LOGGER.error(
                        f"{steemit_url} not made by accepted translator!")
                    continue
            repository = get_repository(post)

            # If user banned, set moderator as BANNED and score to 0
            if (post.author, "Yes") not in constants.BANNED_USERS:
                row = ["", "", steemit_url, repository, category]
            else:
                row = ["BANNED", str(today), steemit_url, repository, category,
                       "0", "", "", "", "", 0]
                constants.LOGGER.info(
                    f"Commenting on {steemit_url} - BANNED.")
                banned_comment(steemit_url)

            if "iamutopian" in tags and post.author not in moderators:
                continue

            constants.UNREVIEWED.append_row(row)
            result = get_urls()
            constants.LOGGER.info(
                f"{steemit_url} has tags: {tags} and was added.")

    moderator_points()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        constants.LOGGER.error(error)
