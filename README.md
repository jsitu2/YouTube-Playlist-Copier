# FlaskYouTubePlaylistCopier
Web application created with python flask. Copies existing YouTube playlist into a new or existing playlist.

## Installations/Requirements
Python 3 will need to be installed to run this application.
Link to download: https://www.python.org/downloads/

You will need to obtain your own Google OAuth2.0 authorization credentials by going to this link: https://console.developers.google.com/apis/credentials and creating a project. Then, click configure consent screen, choose external for user type, enter required info in steps 1 and 2, add the emails of the google accounts in which you want to copy playlists with in step 3, go to step 4, then go back to dashboard.
Then, go to "Enabled APIs & services" and enable "YouTube Data API v3"
After that, go to "Credentials" to create an OAuth client ID. Select Web application as the application type and add http://127.0.0.1:5000/callback as an Authorized redirect URI.
Click create, then download the client secret file in the popup.


## How to run/use the app
First, clone this repository

Then, move the client secret file into this folder, renaming the file to "client_secret.json"

After that, run virtual environment with the command:
```.venv/Scripts/activate```

Install imports with the command:
```pip install -r requirements.txt```

Then, edit the playlist links/existing playlist links in the desired routes in lines 23-43 of app.py
You have 3 routes/options
- route /copy_playlist_into_new_playlist allows you to copy all items of a playlist into a new playlist
- route /copy_playlist_into_existing_playlist allows you to copy all items of a playlist into an existing playlist
- route /copy_playlist_into_existing_playlist_dont_copy_duplicates allows you to copy all items of a playlist into an existing playlist, without copying over any videos that already exist in the existing playlist

In the case where you accidently copied duplicate videos to a playlist (eg: when you refreshed the request and accidently copy the same playlist 2 times), go to this route:
- /remove_duplicate_videos_in_playlist to remove any duplicate videos in a playlist

NOTE: each time you edit the code to add/change playlist links, you must quit and re-run the server

After that, run the server with the command:
```flask run```

Go to http://127.0.0.1:5000/, which will direct you to give authorization through google.
After authorization is completed successfully, go to the desired route (eg: http://127.0.0.1:5000/copy_playlist_into_new_playlist) to copy playlists

