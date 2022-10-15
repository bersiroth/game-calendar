from __future__ import print_function

import datetime
import os.path
import click

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_google_credentials():
    credentials = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        credentials = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(credentials.to_json())
    return credentials


def get_google_calendar_service():
    try:
        credentials = get_google_credentials()
        return build('calendar', 'v3', credentials=credentials)
    except HttpError as error:
        click.secho(f"An error occurred: '{error}'", err=True, fg='red')


calendar = get_google_calendar_service()


def get_calendar_by_name(name):
    calendar_list = calendar.calendarList().list().execute()
    calendar_id = None
    for calendar_list_entry in calendar_list['items']:
        if calendar_list_entry['summary'] == name:
            return calendar_list_entry['id']

    if not calendar_id:
        click.secho(f"Calendar '{name}' not found", err=True, fg='red')
        exit()


@click.group()
def cli():
    """Calendar cli for game and anniversary."""


@cli.group('game', short_help='Find game release date, add new game, etc ...')
def game():
    """Cli for game calendar."""


@cli.group('anniversary', short_help='Find anniversary date, add new date, etc ...')
def anniversary():
    """Cli for anniversary calendar."""


@anniversary.command('list', short_help='list next game anniversary date')
@click.option('--count', default=10, help='Number of date.')
def list(count):
    """List next game release date."""
    calendar_id = get_calendar_by_name("Anniversary calendar")
    list_date(calendar_id, count, 'Anniversary')


def list_date(calendar_id, max_result, event_name='Event'):
    event_name = event_name[0].upper() + event_name[1:]
    try:
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = calendar.events().list(calendarId=calendar_id, timeMin=now,
                                               maxResults=max_result, singleEvents=True,
                                               orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            click.secho("No date found.", err=True, fg='yellow')
            return
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            game_title = click.style(event['summary'], fg='green')
            game_release_date = click.style(start, fg='green')
            click.echo(f"{event_name} {game_title} date {game_release_date}")

    except HttpError as error:
        click.secho(f"An error occurred: '{error}'", err=True, fg='red')


@game.command('list', short_help='list next game release date')
@click.option('--count', default=10, help='Number of date.')
def list(count):
    """List next game release date."""
    calendar_id = get_calendar_by_name("Game calendar")
    list_date(calendar_id, count, 'Game')


if __name__ == '__main__':
    cli()
