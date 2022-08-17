from flask import Flask, request, url_for, session, redirect, jsonify
from flask_cors import CORS
import requests
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os 

app = Flask(__name__)
CORS(app, supports_credentials=True)

#disables OAuthlib's HTTPS verification when running locally
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


#assigns session cookie
app.secret_key = "8hskwSneiwoh32h"
app.config['SESSION_COOKIE_NAME'] = 'Cookie Tester'


@app.route("/copy_playlist_into_new_playlist")
def copy_playlist_into_new_playlist():
    playlist_link = "https://www.youtube.com/playlist?list=PLrVfyimyec-SH0S-m7GcBwJudhOQEhd6o"
    return copy_playlist(playlist_link, True)

@app.route("/copy_playlist_into_existing_playlist")
def copy_playlist_into_existing_playlist():
    playlist_link = "https://www.youtube.com/playlist?list=PLrVfyimyec-SUzLg8AzANBBNWTn2uqVUA"
    existing_playlist_link = "https://www.youtube.com/playlist?list=PLrVfyimyec-RlaCLfuusV3Ns5zI4YQ27P"
    return copy_playlist(playlist_link, False, existing_playlist_link)

@app.route("/copy_playlist_into_existing_playlist_dont_copy_duplicates")
def copy_playlist_into_existing_playlist_dont_copy_duplicates():
    playlist_link = "https://www.youtube.com/playlist?list=PLbTkpy4DiE7gODKZJcdVi8NVVpUFeF8Wm"
    existing_playlist_link = "https://www.youtube.com/playlist?list=PLbTkpy4DiE7hw9ojfH0MFKdssqDPQDgK1"
    return copy_playlist(playlist_link, False, existing_playlist_link, True)


#default route to log in
@app.route("/")
def login():
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", scopes=["https://www.googleapis.com/auth/youtube"])
    flow.redirect_uri = url_for('callback', _external=True)
    auth_url, state = flow.authorization_url(prompt='consent')
    return redirect(auth_url)

#callback route
#note: credentials.to_json converts credentials to str, must use json.loads to convert str to dict, extract token and other info through dict
@app.route("/callback")
def callback():
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", scopes=["https://www.googleapis.com/auth/youtube"])
    flow.redirect_uri = url_for('callback', _external=True)
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    session["credentials"] = credentials.to_json()
    return "successfuly completed authorization, go to desired route (/copy_playlist_into_new_playlist, /copy_playlist_into_existing_playlist, /copy_playlist_into_existing_playlist_dont_copy_duplicates) to copy playlists"


#method to copy playlist, handles all 3 cases for copying
def copy_playlist(link, new_playlist_or_not, existing_link = None, dont_copy_duplicates = None):
    youtube = create_youtube_object()
    
    if new_playlist_or_not:
        new_playlist_id = create_new_playlist(link)
    else:
        new_playlist_id = existing_link.split('=')[1]

    # gets playlist items from link, saves all public video ids to a list (since private videos can't be copied)
    playlist_items = get_playlist_items(link)

    list_of_public_video_ids = []
    for video in playlist_items:
        if video["status"]["privacyStatus"] == "public":
            list_of_public_video_ids.append(video["contentDetails"]["videoId"])

    #manages case for when copying to existing playlist and user doesn't want duplicate videos to be copied
    if not new_playlist_or_not and dont_copy_duplicates:
        existing_playlist_items = get_playlist_items(existing_link)
        list_of_public_video_ids_existing = []
        for video in existing_playlist_items:
            if video["status"]["privacyStatus"] == "public":
                list_of_public_video_ids_existing.append(video["contentDetails"]["videoId"])
        res = [i for i in list_of_public_video_ids if i not in list_of_public_video_ids_existing]
        list_of_public_video_ids = res

    
    list_of_public_video_ids.reverse()

    #adds all public videos to destination playlist
    for video_id in list_of_public_video_ids:
        request = youtube.playlistItems().insert(
            part="snippet",
            body={
            "snippet": {
                "playlistId": new_playlist_id,
                "position": 0,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
              }
            }
        )
        response = request.execute()

    link_of_playlist_with_copied_vid = "https://www.youtube.com/playlist?list=" + new_playlist_id
    return "copy playlist success, the link to the playlist with the copied videos is " + link_of_playlist_with_copied_vid

#helper method to create a new playlist
def create_new_playlist(link):
    youtube = create_youtube_object()

    request = youtube.playlists().insert(
        part="snippet,status,id",
        body={
          "snippet": {
            "title": "Playlist Copy",
            "description": f"This is a copy of {link}",
            "defaultLanguage": "en"
          },
          "status": {
            "privacyStatus": "private"
          }
        }
    )
    response = request.execute()
    new_playlist_id = response["id"]
    return new_playlist_id


#helper method for copy_playlist(), returns playlist items of a link in a list
def get_playlist_items(link):
    youtube = create_youtube_object()

    #extract playlist id from playlist link
    parsed = link.split('=')[1]

    #store all videos in a video list, note: response is a dict type
    playlist_items = []
    request = youtube.playlistItems().list(
        part="contentDetails, status",
        maxResults=5,
        playlistId= parsed
    )
    response = request.execute()
    
    playlist_items.extend(response.get("items"))
    next_page_token = response.get("nextPageToken")

    while next_page_token:
        request = youtube.playlistItems().list(
            part="contentDetails, status",
            maxResults=5,
            playlistId= parsed,
            pageToken= next_page_token
        )
        response = request.execute()
        playlist_items.extend(response.get("items"))
        next_page_token = response.get("nextPageToken")

    return playlist_items


#helper method to create youtube object
def create_youtube_object():
    try:
        credentials_info = get_credentials()
    except:
        print("user is not logged in")
        return redirect(url_for('login', _external=False))
    
    credentials = Credentials.from_authorized_user_info(json.loads(credentials_info))
    youtube = build("youtube", "v3", credentials=credentials)
    return youtube


#helper method to get credentials
#note: not sure if the refresh token thing works, since the credentials.json for the recreated credential is in the wrong format, think the from_authorized_user_info doesn't work properly
def get_credentials():
    credentials_info = session.get("credentials", None)
    if not credentials_info:
        raise "exception"
    credentials = Credentials.from_authorized_user_info(json.loads(credentials_info))
    # the if should have "and credentials.refresh_token" added, but not sure
    if credentials and credentials.expired and credentials.refresh_token:
        print("Refreshing Access Token")
        # i think the line below simply refreshes the access token for the specific credentials instance
        credentials.refresh(Request())
        credentials_info = credentials.to_json()
        session["credentials"] = credentials_info
    return credentials_info
