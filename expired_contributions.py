from constants import SHEET, TITLE_PREVIOUS, TITLE_CURRENT, DB_UTEMPIAN


def update_sheet(url):
    """Updates the status of a contribution to "Expired" if it's in the last
    12 hours before payout.
    """
    column = 11
    status = "Expired"

    previous_reviewed = SHEET.worksheet(TITLE_PREVIOUS)
    current_reviewed = SHEET.worksheet(TITLE_CURRENT)

    try:
        if url in previous_reviewed.col_values(3):
            row_index = previous_reviewed.col_values(3).index(url) + 1
            previous_reviewed.update_cell(row_index, column, status)
        else:
            row_index = current_reviewed.col_values(3).index(url) + 1
            current_reviewed.update_cell(row_index, column, status)
    except Exception as error:
        pass


def main():
    """Iterates over all posts that will reach 12 hours before payout by the
    time the next voting round starts and updates them in the sheet.
    """
    contributions = DB_UTEMPIAN.contributions.find({
        "valid_age": False, "status": "pending",
    })
    for contribution in contributions:
        update_sheet(contribution["url"])

if __name__ == '__main__':
    main()
