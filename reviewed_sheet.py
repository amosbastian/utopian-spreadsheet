from beem.account import Account
from beem.comment import Comment
from contribution import Contribution
from datetime import datetime, timedelta
import constants
import os


def exponential_vote(score, category):
    """
    Calculates the exponential vote for the bot.
    """
    status = ""

    try:
        max_vote = constants.MAX_VOTE[category]
    except:
        max_vote = constants.MAX_TASK_REQUEST

    if score < constants.MINIMUM_SCORE:
        weight = 0.0
    else:
        status = "Pending"
        power = constants.EXP_POWER
        weight = pow(
            score / 100.0,
            power - (score / 100.0 * (power - 1.0))) * max_vote

    return status, f"{weight:.2f}"


def vote_contribution(contribution):
    """
    Votes on the contribution with a scaled weight (dependent on the
    contribution's category and weight).
    """
    if "@amosbastian" in contribution.url:
        return

    weight = (float(contribution.weight) /
              max(constants.MAX_VOTE.values()) * 100.0)
    contribution = Comment(contribution.url)
    voters = [vote.voter for vote in contribution.get_votes()]
    if "amosbastian" not in voters:
        contribution.vote(weight, "amosbastian")


def add_comment(contribution):
    """
    Adds the authorperm of the moderator's comment to the database.
    """
    if contribution.moderator == "amosbastian":
        return

    post = Comment(contribution.url)

    for comment in post.get_replies():
        if comment.author == contribution.moderator:
            age = comment.time_elapsed()
            collection = constants.DB.comments
            collection.insert({
                "url": comment.authorperm,
                "upvote_time": datetime.now() + timedelta(minutes=30) - age,
                "inserted": datetime.now(),
                "upvoted": False,
                "category": contribution.category
            })


def move_to_reviewed(contribution):
    """Move contribution to the reviewed worksheet."""
    post = Comment(contribution.url)
    tags = post.json_metadata["tags"]

    if "iamutopian" in tags:
        contribution.category = "iamutopian"
        contribution.vote_status = ""

    constants.REVIEWED.append_row(list(contribution.__dict__.values()))


def main():
    result = constants.UNREVIEWED.get_all_values()
    for row in result[1:]:
        contribution = Contribution(row)
        moderator = contribution.moderator
        date = contribution.review_date
        score = contribution.score

        if moderator != "" and date != "" and score != "":
            # Calculate voting %
            category = contribution.category.strip()
            contribution.vote_status, contribution.weight = exponential_vote(
                float(score), category)

            if not moderator.upper() in ["BANNED", "IGNORED", "IRRELEVANT"]:
                contribution.review_status = "Pending"

            constants.LOGGER.info(
                f"Moving {contribution.url} to reviewed sheet with voting % "
                f"{contribution.weight} and score {score}")

            constants.UNREVIEWED.delete_row(result.index(row) + 1)
            move_to_reviewed(contribution)

            if float(score) > constants.MINIMUM_SCORE:
                vote_contribution(contribution)
                add_comment(contribution)
            return

if __name__ == '__main__':
    main()