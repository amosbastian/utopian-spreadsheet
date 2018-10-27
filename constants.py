from beem import Steem
from datetime import date, datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials
from pymongo import MongoClient
import gspread
import logging
import os

# Get path of current folder
DIR_PATH = os.path.dirname(os.path.realpath(__file__))

# Logging
LOGGER = logging.getLogger("utopian-io")
LOGGER.setLevel(logging.INFO)
FILE_HANDLER = logging.FileHandler(f"{DIR_PATH}/spreadsheet.log")
FILE_HANDLER.setLevel(logging.DEBUG)
FORMATTER = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
FILE_HANDLER.setFormatter(FORMATTER)
LOGGER.addHandler(FILE_HANDLER)

# Spreadsheet variables
SCOPE = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
CREDENTIALS = ServiceAccountCredentials.from_json_keyfile_name(
    f"{DIR_PATH}/client_secret.json", SCOPE)
CLIENT = gspread.authorize(CREDENTIALS)
SHEET = CLIENT.open("Utopian Reviews")

# Get date of current, next and previous Thursday
TODAY = date.today()
OFFSET = (TODAY.weekday() - 3) % 7
THIS_WEEK = TODAY - timedelta(days=OFFSET)
LAST_WEEK = THIS_WEEK - timedelta(days=7)
NEXT_WEEK = THIS_WEEK + timedelta(days=7)
TWO_WEEK = THIS_WEEK - timedelta(days=14)

# Get title's of most recent two worksheets
TITLE_REVIEWED_EDGE = f"Reviewed - {TWO_WEEK:%b %-d} - {LAST_WEEK:%b %-d}"
TITLE_UNREVIEWED_EDGE = f"Unreviewed - {LAST_WEEK:%b %-d} - {THIS_WEEK:%b %-d}"
TITLE_PREVIOUS = f"Reviewed - {LAST_WEEK:%b %-d} - {THIS_WEEK:%b %-d}"
TITLE_CURRENT = f"Reviewed - {THIS_WEEK:%b %-d} - {NEXT_WEEK:%b %-d}"
TITLE_UNREVIEWED = f"Unreviewed - {THIS_WEEK:%b %-d} - {NEXT_WEEK:%b %-d}"
TITLE_REVIEWED = f"Reviewed - {THIS_WEEK:%b %-d} - {NEXT_WEEK:%b %-d}"
TITLE_LAST = f"Reviewed - {LAST_WEEK:%b %-d} - {THIS_WEEK:%b %-d}"

try:
    # Get all relevant worksheets
    UNREVIEWED = SHEET.worksheet(TITLE_UNREVIEWED)
    REVIEWED = SHEET.worksheet(TITLE_REVIEWED)
    LAST = SHEET.worksheet(TITLE_LAST)
    UTOPIAN_FEST = SHEET.worksheet("Utopian Fest")
    PREVIOUS_REVIEWED = SHEET.worksheet(TITLE_PREVIOUS)
    CURRENT_REVIEWED = SHEET.worksheet(TITLE_CURRENT)
    UNREVIEWED = SHEET.worksheet(TITLE_UNREVIEWED)
except:
    PREVIOUS_REVIEWED = SHEET.worksheet(TITLE_REVIEWED_EDGE)
    CURRENT_REVIEWED = SHEET.worksheet(TITLE_PREVIOUS)
    UNREVIEWED = SHEET.worksheet(TITLE_UNREVIEWED_EDGE)

# Get all relevant URLs
BANNED_SHEET = SHEET.worksheet("Banned users")
BANNED_USERS = zip(BANNED_SHEET.col_values(1), BANNED_SHEET.col_values(4))

# VIPO sheet
VIPO_SHEET = SHEET.worksheet("VIPO")
VIPO = [vipo.strip() for vipo in VIPO_SHEET.col_values(1)[1:]]

# Get all translators
TRANSLATOR_SHEET = SHEET.worksheet("Translators")
UTOPIAN_TRANSLATORS = [translator.strip() for
                       translator in TRANSLATOR_SHEET.col_values(1)[1:]]

# URL
STEEMIT_URL = "https://steemit.com/"

# MongoDB
CLIENT = MongoClient()
DB = CLIENT.utopian
DB_UTEMPIAN = CLIENT.utempian

# Points per category
CATEGORY_POINTS = {
    "ideas": 6.0,
    "development": 10.0,
    "graphics": 8.0,
    "bug-hunting": 7.0,
    "analysis": 8.0,
    "social": 5.0,
    "video-tutorials": 8.0,
    "tutorials": 8.0,
    "copywriting": 5.0,
    "documentation": 5.0,
    "blog": 6.0,
    "translations": 8.0,
    "anti-abuse": 6.0,
}
TASK_REQUEST = 2.5

# Text
COMMENT_BANNED = (
    "Hi, @{}. Your account has been excluded from Utopian rewards "
    "and therefore this contribution post will not be reviewed. You can "
    "contact us at https://support.utopian.io/ if you have any further "
    "questions.")

# Max vote
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
    "anti-abuse": 50.0,
}
MAX_TASK_REQUEST = 6.0

# Minimum score
MINIMUM_SCORE = 10

# Exponential vote
EXP_POWER = 2.1

# GitHub
REPOSITORY_REGEX = "http(s)?://github.com/[^\r\n\t\f\v/ ]*/[^\r\n\t\f\v/ ]*"

# Anti abuse
ANTI_ABUSE_SHEET = SHEET.worksheet("Antiabuse")
UTOPIAN_ANTI_ABUSE = [antiabuse.strip() for
                      antiabuse in ANTI_ABUSE_SHEET.col_values(1)[1:]]

# Scaling my personal voting weight
SCALER = 1.5
