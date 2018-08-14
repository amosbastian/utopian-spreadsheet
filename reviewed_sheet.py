from beem.account import Account
from beem.comment import Comment
from contribution import Contribution
from datetime import datetime
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
    contribution.vote(weight, "amosbastian")


def points_to_weight(points):
    """
    Returns the voting weight needed for a vote worth the points equivalence
    in SBD.
    """
    account = Account("utopian-io")
    max_SBD = account.get_voting_value_SBD()
    return 100 * points / max_SBD


def vote_comment(contribution):
    """
    Votes on the contribution's moderator's comment.
    """
    if contribution.moderator == "amosbastian":
        return

    try:
        points = constants.CATEGORY_POINTS[contribution.category]
    except KeyError:
        points = constants.TASK_REQUEST

    category_weight = points_to_weight(points)
    weight = category_weight / max(constants.MAX_VOTE.values()) * 100.0
    post = Comment(contribution.url)

    for comment in post.get_replies():
        if comment.author == contribution.moderator:
            collection = constants.DB.comments
            collection.insert({
                "url": comment.authorperm,
                "updated": datetime.now()
            })


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

            if not contribution.moderator == "BANNED":
                contribution.review_status = "Pending"

            constants.LOGGER.info(
                f"Moving {contribution.url} to reviewed sheet with voting % "
                f"{contribution.weight} and score {score}")

            constants.UNREVIEWED.delete_row(result.index(row) + 1)
            constants.REVIEWED.append_row(list(contribution.__dict__.values()))

            if float(score) > constants.MINIMUM_SCORE:
                vote_contribution(contribution)
                vote_comment(contribution)
            return

if __name__ == '__main__':
    main()
