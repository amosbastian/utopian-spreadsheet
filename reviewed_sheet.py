from datetime import date, timedelta
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import pprint
import time

# Everything outside because I can't be bothered doing this properly
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    "/home/amos/utopian-spreadsheet/client_secret.json", scope)
client = gspread.authorize(credentials)
sheet = client.open("Utopian Reviews")
reviews = sheet.get_worksheet(0)
reviewed = sheet.get_worksheet(-1)


def main():
    time.sleep(10)
    result = reviews.get_all_values()
    for row in result[1:]:
        moderator = row[0]
        score = row[5]
        if moderator != "" and score != "":
            print("Deleting row {} at index {}".format(row,
                                                       result.index(row) + 1))
            reviews.delete_row(result.index(row) + 1)
            reviewed.append_row(row)
            return

if __name__ == '__main__':
    main()
