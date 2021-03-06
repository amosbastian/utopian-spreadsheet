from beem.account import Account
from beem.comment import Comment
from datetime import datetime, timedelta
import constants
import time


def points_to_weight(points):
    """Returns the voting weight needed for a vote worth the points equivalence
    in SBD.
    """
    account = Account("utopian-io")
    max_SBD = account.get_voting_value_SBD()
    return max(1.0, 100.0 * points / max_SBD)


def upvote_comment(comment):
    """Upvotes the contribution's moderator's comment."""
    try:
        points = constants.CATEGORY_POINTS[comment["category"]]
    except KeyError:
        points = constants.TASK_REQUEST

    category_weight = points_to_weight(points)
    weight = (category_weight / max(constants.MAX_VOTE.values()) * 100.0) / constants.SCALER

    comment = Comment(comment["url"])
    voters = [vote.voter for vote in comment.get_votes()]
    if "amosbastian" in voters or "utopian-io" in voters:
        constants.DB.comments.update_one(comment, {"$set": {"upvoted": True}})

    comment.vote(weight, "amosbastian")
    constants.LOGGER.info((f"Upvoting comment {comment['url']} "
                           f"with weight {weight}%"))
    time.sleep(3)


def upvote_contribution(contribution):
    """Upvotes the contribution with a pre-calculated weight."""
    try:
        post = Comment(contribution["url"])
    except Exception:
        constants.DB.pending_contributions.remove({"url": contribution["url"]})
        return

    voters = [vote.voter for vote in post.get_votes()]
    if "amosbastian" in voters or "utopian-io" in voters:
        constants.DB_UTEMPIAN.pending_contributions.update_one(
            contribution, {"$set": {"upvoted": True}})
        return

    post.vote(contribution["weight"], "amosbastian")
    constants.LOGGER.info((f"Upvoting contribution {contribution['url']} "
                           f"with weight {contribution['weight']}%"))
    time.sleep(3)


def check_missed_comments():
    """Adds missed comments to the queue."""
    missed_posts = constants.DB.missed_posts.find()
    for document in missed_posts:
        url = document["url"]
        moderator = document["moderator"]
        category = document["category"]

        post = Comment(url)
        for comment in post.get_replies():
            if comment.author == moderator:
                constants.DB.missed_posts.remove({"url": url})
                age = comment.time_elapsed()
                comments = constants.DB.comments
                now = datetime.now()
                comments.insert({
                    "url": comment.authorperm,
                    "upvote_time": now + timedelta(minutes=10) - age,
                    "inserted": now,
                    "upvoted": False,
                    "category": category
                })


def main():
    """Upvotes all comments and contributions that are older than 30 minutes
    and then removes them.
    """
    comments = constants.DB.comments.find({
        "upvote_time": {
            "$lte": datetime.now()
        },
        "upvoted": False
    })
    for comment in comments:
        upvote_comment(comment)
        constants.DB.comments.update_one(comment, {"$set": {"upvoted": True}})

    check_missed_comments()

    contributions = constants.DB_UTEMPIAN.pending_contributions.find({
        "upvote_time": {
            "$lte": datetime.now()
        },
        "upvoted": False
    })
    for contribution in contributions:
        upvote_contribution(contribution)
        constants.DB_UTEMPIAN.pending_contributions.update_one(
            contribution, {"$set": {"upvoted": True}})

if __name__ == '__main__':
    main()
