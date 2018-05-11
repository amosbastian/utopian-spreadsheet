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
    last_thursday = today - timedelta(days=offset)
    next_thursday = last_thursday + timedelta(days=7)
    title_reviews = f"Week {last_thursday:%b %-d} - {next_thursday:%b %-d}"
    title_reviewed = "Reviewed - " + title_reviews
    title_reviews = "Unreviewed - " + title_reviews
    # Get sheet and some variables
    reviews = sheet.get_worksheet(0)
    header = reviews.row_values(1)
    reviews.update_title(title_reviews)

    worksheet = sheet.add_worksheet(
        title=title_reviewed, rows="999", cols="11")
    worksheet.append_row(header)

if __name__ == '__main__':
    main()
