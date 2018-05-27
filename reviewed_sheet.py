from datetime import date, timedelta
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import pprint
import time
import os

# Get path of current folder
DIR_PATH = os.path.dirname(os.path.realpath(__file__))

# Minimum score
MINIMUM_SCORE = 10

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
    "ideas": 12.0,
    "development": 40.0,
    "bug-hunting": 8.0,
    "translations": 25.0,
    "graphics": 30.0,
    "analysis": 35.0,
    "social": 20.0,
    "documentation": 20.0,
    "tutorials": 20.0,
    "video-tutorials": 25.0,
    "copywriting": 20.0,
    "blog": 20.0,
}


def main():
    time.sleep(1)
    result = unreviewed.get_all_values()
    for row in result[1:]:
        moderator = row[0]
        date = row[1]
        score = row[5]
        if moderator != "" and date != "" and score != "":
            # Calculate voting %
            if float(score) >= MINIMUM_SCORE:
                category = row[4]
                try:
                    max_vote = MAX_VOTE[category]
                except:
                    max_vote = 4.0
                    # Also set to pending
                row[-2] = "Pending"
                row[-1] = float(score) / 100.0 * max_vote
            else:
                row[-1] = 0.0
            unreviewed.delete_row(result.index(row) + 1)
            reviewed.append_row(row)
            return

if __name__ == '__main__':
    main()
