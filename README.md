# utopian-spreadsheet
Code for managing the spreadsheet used in the current moderation process.

# Installing

The code for the spreadsheet was made using Python3.6. For a quick and easy way to install it is recommended you install the [Anaconda Distribution](https://www.anaconda.com/what-is-anaconda/). 

## Python packages
Once Python is installed you can install the required packages in your virtual environment like so

```bash
$ python -m venv venv
$ . venv/bin/active
$ (venv) pip install -r requirements.txt
```

If you encounter any problems while installing the Python packages you might be missing some other required packages. On Ubuntu you can solve this by installing the following packages

```
sudo apt-get install build-essential libssl-dev python-dev
```

## Sheet API
Since the bot also works with Google sheets you will need create a project in [Google's API manager](https://console.cloud.google.com/apis/dashboard) and add the Google sheet API to the project. Once created you will also need to add credentials to the project and make it so application data is accessible by selecting that option.

Next you will need to create a service account with the project editor role. Clicking continue will generate a JSON file that you should add to the project's folder and rename `client_secret.json`. In this file there should be a key called "client_email" - you should share the spreadsheet with this email address.

# Usage

Basically there are three Python files that perform separate tasks. 

* spreadsheet.py

The main program. This uses `beem` to iterate over recent contributions, checks if they are already in the main sheet, and if they are not it adds them to it. While doing this it performs some checks, like if the category is valid and/or the user is banned or not. Once everything is confirmed it adds a row containing the URL of the post, the linked repository and its category. It is also used to calculate each moderator's points for the week and saves them to a file, allowing it to be displayed on e.g. https://utopian.rocks/json/2018-05-17.

* reviewed_sheet.py

This checks if contributions in the main worksheet have been reviewed or not. It determines this by checking the mdoderator, date and score column. If they are all filled the row is deleted and moved to the current week's "reviewed" sheet, so the bot can vote on it for example.

* new_sheet.py

This is used to create a new worksheet and update the name of the main worksheet where unreviewed contributions come in. Moderators get upvoted every Thursday at midnight, hence why each date starts with a Thursday.

---

That's it! If you have any questions you can contact me on Discord at Amos#4622.
