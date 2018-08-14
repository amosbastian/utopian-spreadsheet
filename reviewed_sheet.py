from beem.comment import Comment
from contribution import Contribution
import constants
import os
import time


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
    if contribution.author == "amosbastian":
        return
    weight = (float(contribution.weight) /
              max(constants.MAX_VOTE.values()) * 100.0)
    contribution = Comment(contribution.url)
    contribution.vote(weight, "amosbastian")
    time.sleep(3)


def vote_comment(contribution):
    """
    Votes on the contribution's moderator's comment.
    """
    if contribution.moderator == "amosbastian":
        return
    try:
        category_weight = constants.CATEGORY_POINTS[contribution.category]
    except KeyError:
        category_weight = constants.TASK_REQUEST

    weight = category_weight / max(constants.MAX_VOTE.values()) * 100.0
    post = Comment(contribution.url)

    for comment in post.get_replies():
        if comment.author == contribution.moderator:
            comment.vote(weight, "amosbastian")


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
