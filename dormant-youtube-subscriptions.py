import math
import os
import sys
import httplib2

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

BASE_URL = "https://www.youtube.com/channel/"
CLIENT_SECRETS_FILE = "client_secrets.json"
YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   {}

with information from the Developers Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""".format(os.path.abspath(os.path.join(os.path.dirname(__file__), CLIENT_SECRETS_FILE)))


def retrieve_youtube_subscriptions():
    try:
        next_page_token = ''
        subs_iteration = 0

        while True:
            subscriptions_response = youtube_subscriptions(next_page_token)
            subs_iteration += 1
            total_results = subscriptions_response['pageInfo']['totalResults']
            results_per_page = subscriptions_response['pageInfo']['resultsPerPage']
            total_iterations = math.ceil(total_results / results_per_page)

            print('Subscriptions iteration: {} of {} ({}%)'.format(subs_iteration,
                                                                   total_iterations,
                                                                   round(subs_iteration / total_iterations * 100),
                                                                   0))

            next_page_token = get_next_page(subscriptions_response)
            channels = parse_youtube_subscriptions(subscriptions_response)
            all_channels.extend(channels)

            if not next_page_token:
                break

        all_channels.sort()

        return all_channels

    except HttpError as err:
        print("An HTTP error {} occurred:\n{}".format(err.resp.status, err.content))


def get_authenticated_service():
    storage = Storage("{}-oauth2.json".format(sys.argv[0]))
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
                                       scope=YOUTUBE_READ_WRITE_SCOPE,
                                       message=MISSING_CLIENT_SECRETS_MESSAGE)
        args = argparser.parse_args()
        credentials = run_flow(flow, storage, args)

    return build(YOUTUBE_API_SERVICE_NAME,
                 YOUTUBE_API_VERSION,
                 http=credentials.authorize(httplib2.Http()))


def youtube_subscriptions(next_page_token):
    subscriptions_response = youtube.subscriptions().list(
        part='snippet,contentDetails',
        mine=True,
        maxResults=50,
        order='alphabetical',
        pageToken=next_page_token).execute()
    return subscriptions_response


def get_next_page(subscriptions_response):
    if 'nextPageToken' in subscriptions_response:
        next_page_token = subscriptions_response['nextPageToken']
    else:
        next_page_token = ''
    return next_page_token


def parse_youtube_subscriptions(subscriptions_response):
    channels = []

    for subscriptions_result in subscriptions_response.get("items", []):
        if subscriptions_result["snippet"]["resourceId"]["kind"] == "youtube#channel":
            title = subscriptions_result["snippet"]["title"]
            channel_id = subscriptions_result["snippet"]["resourceId"]["channelId"]

            results = youtube.channels().list(
                part="contentDetails",
                id=channel_id
            ).execute()

            if(len(results["items"]) > 0):
                uploads_playlist_id = results["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

                results = youtube.playlistItems().list(
                    part="snippet",
                    playlistId=uploads_playlist_id
                ).execute()

                if(len(results["items"]) > 0):
                    last_upload_date = results["items"][0]["snippet"]["publishedAt"]
                    channels.append("<tr><td>{}</td><td><a href=\"{}{}\">{}</a></td></tr>".format(last_upload_date, BASE_URL, channel_id, title))

    return channels


if __name__ == "__main__":
    all_channels = []
    youtube = get_authenticated_service()

    print('<html>')
    print('<head>')
    print('<title>Dormant YouTube Subscriptions</title>')
    print('<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">')
    print('<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"></script>')
    print('</head>')
    print('<body>')
    print('<pre>')
    print('Retrieving subscriptions:')

    all_channels = retrieve_youtube_subscriptions()

    print('Retrieval complete')
    print('Subscriptions found: {}'.format(len(all_channels)))
    print('</pre>')
    print('<table class="table">')
    print('<thead><tr><th>Last Upload Date</th><th>Channel</th></tr></thead>')
    print('<tbody>')

    [print(channel) for channel in all_channels]

    print('</tbody>')
    print('</table>')
    print('</body>')
    print('</html>')
