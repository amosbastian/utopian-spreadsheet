from datetime import date, timedelta
from oauth2client.service_account import ServiceAccountCredentials
import gspread

# Everything outside because I can't be bothered doing this properly
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    "/home/amos/utopian-spreadsheet/client_secret.json", scope)
client = gspread.authorize(credentials)
sheet = client.open("Utopian Reviews")


def main():
    # Date stuff
    today = date.today()
    offset = (today.weekday() - 3) % 7
    this_week = today - timedelta(days=offset)
    next_week = this_week + timedelta(days=7)
    title_unreviewed = f"Unreviewed - {this_week:%b %-d} - {next_week:%b %-d}"
    title_reviewed = f"Reviewed - {this_week:%b %-d} - {next_week:%b %-d}"
    # Get sheet and some variables
    reviews = sheet.worksheet(title_unreviewed)
    header = reviews.row_values(1)
    reviews.update_title(title_unreviewed)

    worksheet = sheet.add_worksheet(
        title=title_reviewed, rows="999", cols="11")
    worksheet.append_row(header)

if __name__ == '__main__':
    main()
