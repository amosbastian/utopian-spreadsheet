from datetime import date, timedelta
import constants
import gspread


def main():
    # Date stuff
    today = date.today()
    this_week = today - timedelta(days=constants.OFFSET)
    last_week = this_week - timedelta(days=7)
    next_week = this_week + timedelta(days=7)
    title_last = f"Unreviewed - {last_week:%b %-d} - {this_week:%b %-d}"
    title_unreviewed = f"Unreviewed - {this_week:%b %-d} - {next_week:%b %-d}"
    title_reviewed = f"Reviewed - {this_week:%b %-d} - {next_week:%b %-d}"

    # Get sheet and some variables
    reviews = constants.SHEET.worksheet(title_last)
    header = reviews.row_values(1)
    reviews.update_title(title_unreviewed)

    worksheet = constants.SHEET.add_worksheet(
        title=title_reviewed, rows="999", cols="12")
    worksheet.append_row(header)

if __name__ == '__main__':
    main()
