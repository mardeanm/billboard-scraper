import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import spotipy

# Load environment variables from .env file
load_dotenv()
# Spotify API Credentials
CLIENT_ID = os.getenv("SPOTIFY_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_SECRET")
redirect_URL = "https://www.google.com/"
URL = "https://www.billboard.com/charts/hot-100/"
scope = (
    "playlist-modify-public "
    "playlist-modify-private "
    "playlist-read-private "
    "playlist-read-collaborative "
    "user-read-private"
)
sp = spotipy.Spotify(auth_manager=spotipy.SpotifyOAuth(client_id=CLIENT_ID,
                                                       client_secret=CLIENT_SECRET,
                                                       redirect_uri=redirect_URL,
                                                       scope=scope))
user_id = sp.me()['id']


# Clean up artist name by separating the artist name from any features
# for ease of searching up songs
def clean_artist_name(artist_name):
    artist_name = artist_name.split(" Featuring")[0]
    artist_name = artist_name.split(" &")[0]
    artist_name = artist_name.split(" With")[0]
    return artist_name


# Function to search for songs using the title and the artist
def song_search(song_titles_and_artists):
    for index, song in enumerate(song_titles_and_artists):
        song_title = song[0]
        artist_name = clean_artist_name(song[1])

        # Search using both title and artist name
        query = f"track:{song_title} artist:{artist_name}"
        result = sp.search(q=query, limit=1, type="track")

        # If not found, try with only song title
        if not result['tracks']['items']:
            query = f"track:{song_title}"
            result = sp.search(q=query, limit=1, type="track")

        # If found, save the URI
        if result['tracks']['items']:
            track = result['tracks']['items'][0]['uri']
            song_titles_and_artists[index] = track
    return song_titles_and_artists


# Create a playlist using the API's format
def create_playlist(year):
    playlist_name = f"{year} Billboard Top 100's"
    # name for the playlist, setting it to private, and giving it this description
    playlist = sp.user_playlist_create(user_id, name=playlist_name, public=False,
                                       description="This was created using python")
    return playlist['id']


# Adding songs to the new playlist using the previously searched up song URI's by passing the list of all found songs
def add_to_playlist(song_uris, playlist_id):
    sp.playlist_add_items(playlist_id=playlist_id, items=song_uris)


# Asks user for a year to scrap the Billboard 100 website using beautiful soup
def start():
    print("Choose a year to scrap the Billboard 100 songs from?")
    year = input("Type the year in the format YYYY (1958 - 2023): ")
    while int(year) < 1958 or int(year) > 2023:
        year = input("Invalid Input Try Again: ")
    new_url = URL + year + "-12-31"
    response = requests.get(new_url)
    content = response.content
    # Gets content from the site at desired year
    soup = BeautifulSoup(content, "html.parser")
    containers = soup.find_all('div', class_='o-chart-results-list-row-container')
    song_titles_and_artists = []
    # Finds the song titles and authors and saves them to a list by finding their values
    # in the HTML code and extracting them
    for songs in containers:
        title = songs.find('h3', class_='c-title')
        title = title.get_text(strip=True)
        artist = songs.find_all('span', class_='c-label')[1]
        artist = artist.get_text(strip=True)
        artist = artist.split("Featuring")[0]
        song_titles_and_artists.append((title, artist))
    # Use the api to search for the songs
    song_uris = song_search(song_titles_and_artists)
    # Create a new playlist using the year as the name returning its id
    playlist_id = create_playlist(year)
    # Add the songs to the new playlist
    add_to_playlist(song_uris, playlist_id)
    print("Completed, enjoy your music!")


if __name__ == "__main__":
    start()
