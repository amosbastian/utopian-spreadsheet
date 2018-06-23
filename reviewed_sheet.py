from datetime import date, timedelta
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import logging
import pprint
import time
import os

# Get path of current folder
DIR_PATH = os.path.dirname(os.path.realpath(__file__))

# Minimum score
MINIMUM_SCORE = 10

# Logging
logger = logging.getLogger("utopian-io")
logger.setLevel(logging.INFO)
fh = logging.FileHandler(f"{DIR_PATH}/reviewed.log")
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
logger.addHandler(fh)

# Everything outside because I can't be bothered doing this properly
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    f"{DIR_PATH}/client_secret.json", scope)
client = gspread.authorize(credentials)
sheet = client.open("Utopian Reviews")

today = date.today()
offset = (today.weekday() - 3) % 7
this_week = today - timedelta(days=offset)
next_week = this_week + timedelta(days=7)
title_unreviewed = f"Unreviewed - {this_week:%b %-d} - {next_week:%b %-d}"
title_reviewed = f"Reviewed - {this_week:%b %-d} - {next_week:%b %-d}"

unreviewed = sheet.worksheet(title_unreviewed)
reviewed = sheet.worksheet(title_reviewed)

MAX_VOTE = {
    "ideas": 20.0,
    "development": 55.0,
    "bug-hunting": 13.0,
    "translations": 35.0,
    "graphics": 40.0,
    "analysis": 45.0,
    "social": 30.0,
    "documentation": 30.0,
    "tutorials": 30.0,
    "video-tutorials": 35.0,
    "copywriting": 30.0,
    "blog": 30.0,
}
MAX_TASK_REQUEST = 6.0

# Exponential vote
EXP_POWER = 2.1


def exponential_vote(score, category):
    """
    Calculates the exponential vote for the bot.
    """
    status = ""

    try:
        max_vote = MAX_VOTE[category]
    except:
        max_vote = MAX_TASK_REQUEST

    if score < MINIMUM_SCORE:
        vote_pct = 0.0
    else:
        status = "Pending"
        vote_pct = pow(
            score / 100.0,
            EXP_POWER - (score / 100.0 * (EXP_POWER - 1.0))) * max_vote

    return status, f"{vote_pct:.2f}"


def main():
    time.sleep(1)
    result = unreviewed.get_all_values()
    for row in result[1:]:
        moderator = row[0]
        date = row[1]
        score = row[5]
        if moderator != "" and date != "" and score != "":
            # Calculate voting %
            category = row[4]
            row[-2], row[-1] = exponential_vote(float(score), category)

            logger.info(f"Moving {row[2]} to reviewed sheet with voting %: "
                        f"{row[-1]}")
            unreviewed.delete_row(result.index(row) + 1)
            reviewed.append_row(row)
            return

if __name__ == '__main__':
    main()
