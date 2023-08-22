"""Final Project"""

# TODO imports
import random
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, flash, render_template, request, url_for, redirect

class Song:
    def __init__(self, track_id):
        """
        Construct an instance of the Song class.

        Attributes:
            - self.track_id: str representing the ID of a track

        Args:
            track_id (str): unique ID for the track
        """
        self.track_id = track_id
        if len(self.track_id) != 0:
            self.track = sp.track(self.track_id)

    def get_id(self):
        """
        Returns the track ID of a Song instance.

        Args:
            None
        
        Returns:
            The unique ID associated with the track or Song
        """
        return self.track_id
    
    def get_img(self):
        """
        Returns the url to a medium-sized image of the album that is associated with the Song instance.

        Args:
            None
        
        Returns:
            The url to the album image associated with the track or Song
        """
        return self.track['album']['images'][1]['url']
    
    def get_artist(self):
        """
        Returns the artist of a Song instance.

        Args:
            None
        
        Returns:
            The name of the artist associated with the Song instance.
        """
        return self.track['artists'][0]['name']
        
    def get_title(self):
        """
        Returns the track name of a Song instance.

        Args:
            None
        
        Returns:
            The title of the track associated with the Song instance.
        """
        return self.track['name']
    
    def get_audiolink(self):
        """
        Returns the url to a 30-second preview of a Song instance.

        Args:
            None
        
        Returns:
            The url to a 30-second preview of the Song instance.
        """
        return self.track['preview_url'] 
    
    def __eq__(self, other): 
        """
        Defines the equality relationship between two Song instances.

        Args:
            other (str): string representing the title and artist of a track (Ex: "Thriller" by Michael Jackson)

        Returns:
            boolean: True if equal, False if not
        """
        if other != "":
            spl_answer = other.split('"')
            title = spl_answer[1]
            artist = spl_answer[2][4:]
            return self.get_title() == title and self.get_artist() == artist
        else:
            return False

    def __str__(self):
        """
        Defines the string representation of a given Song instance.

        Args:
            None

        Returns:
            str: a Song's string representation
        """
        return '\"' + self.get_title() + '\"' + " by " + self.get_artist()

"""
Set up of Flask and Spotify authentication
"""
app = Flask(__name__)
app.secret_key = 'ax9o4klasi-0oakdn'  # random secret key (needed for flashing)
cid = 'ebf045f92a8e4852ba83d2b2999b039c'
secret = '049ade7edae14362b3e03a63719ca67f'
scope = "user-top-read"
token = util.prompt_for_user_token('USERNAME',scope,client_id=cid,client_secret=secret,redirect_uri='http://localhost:5000/callback')
sp = spotipy.Spotify(auth=token)

"""
Set up for "top tracks" version of the game
"""
top_tracks_dict = sp.current_user_top_tracks(limit=100,time_range='short_term')
top_tracks = []
for i in range(len(top_tracks_dict['items'])):
    top_tracks.append(Song(top_tracks_dict['items'][i]['id']))
"""
Set up for "top artists" version of the game
"""
top_artists_dict = sp.current_user_top_artists(limit=5,time_range='short_term')
top_artists = {}
for i in range(len(top_artists_dict['items'])):
    top_artists.update({top_artists_dict['items'][i]['name']:top_artists_dict['items'][i]['id']})
all_artists_albums = {}
for k,v in top_artists.items():
    artist_albums = []
    sp_artist_albums = sp.artist_albums(v)['items']
    for i in range(len(sp_artist_albums)):
        artist_albums.append(sp_artist_albums[i]['id'])
    all_artists_albums.update({k:artist_albums})
all_artists_tracks = {}

for k,v in all_artists_albums.items():
    artist_track_ids = []
    artist_tracks = []
    for album_num in range(len(v)):
        sp_album_tracks = sp.album_tracks(v[album_num])
        for i in range(5):
            rand = random.randint(0,len(sp_album_tracks['items'])-1)
            track_id_to_add = sp_album_tracks['items'][rand]['id']
            
            if track_id_to_add not in artist_track_ids:
                artist_track_ids.append(track_id_to_add)
                artist_tracks.append(Song(track_id_to_add))
            else:
                i = i-1
    all_artists_tracks.update({k:artist_tracks})


"""
Settings for basis of the game
"""
current_song = Song("")

options = []

level = 0
MAX_GUESSES = 3

@app.route("/", methods=["GET"])
def home():
    """
    Brings the user to the homepage (based on the root URL) where the player can choose
    which game mode to play.

    Args:
        None

    Returns:
        The required returns by Flask to render the home_template.html.
    """
    return render_template("home_template.html",
                           artists= all_artists_tracks.keys()
                           )

@app.route('/new_artists', methods=['POST'])
def new_game_artists():
    """
    Generates a new game based on the user's top artists. A random song by the artist is selected
    and the game resets before being redirected to the game display.

    Args:
        None

    Returns:
        The required returns by Flask to redirect to the game display for the current game status.
    """
    if request.method == "GET":
        return redirect(url_for("home"))
    elif request.method == "POST":
        global level
        global current_song
        global options
        level = 0
        artist = request.form['artist']
        options = all_artists_tracks[artist]

        randint = random.randint(0,len(options)-1)
        current_song = options[randint]
        return redirect(url_for("display"))

@app.route('/new_tracks', methods=['GET'])
def new_game_tracks():
    """
    Generates a new game based on the user's top tracks. A random song is selected
    and the game resets before being redirected to the game display.

    Args:
        None

    Returns:
        The required returns by Flask to redirect to the game display for the current game status.
    """
    global level
    global current_song
    global options
    level = 0
    randint = random.randint(0,len(top_tracks)-1)
    options = top_tracks
    current_song = top_tracks[randint]
    print(current_song)
    return redirect(url_for("display"))
    

@app.route('/game', methods=['GET'])
def display():
    """
    Displays the current game status with the song preview, guess box with a dropdown of options,
    and the number of guesses left before the game is over.

    Args:
        None

    Returns:
        The required returns by Flask to render the game_template.html.
    """
    guesses = MAX_GUESSES - level
    return render_template("game_template.html",
                           guesses = guesses,
                           songs = options,
                           audio = current_song.get_audiolink())

@app.route("/check", methods=['POST'])
def check_guess():
    """
    Checks the user's answer and either returns back to the display method (game_template.html) or
    the end-of-game screen (end_template.html) if the user has won or lost.

    Args:
        None

    Returns:
        The required returns by Flask depending of the nature of the request method (GET or POST).
        Redirects to game_template.html display if the user has more guesses or renders the 
        end-of-game screen (end_template.html).
    """
    if request.method == "GET":
        return redirect(url_for("display"))
    elif request.method == "POST":
        global level
        global current_song
        global options
        user_answer = request.form['guess']

        if user_answer not in options and level < MAX_GUESSES-1:
            is_correct = False
            level+=1
            return redirect(url_for("display"))
        elif user_answer != "":
            is_correct = (current_song == user_answer)
            if not is_correct:
                level += 1
                if level == MAX_GUESSES:
                    return render_template("end_template.html",
                                   win = is_correct,
                                   title = current_song.get_title(),
                                   artist = current_song.get_artist(),
                                   img_url=current_song.get_img(),
                                   audio=current_song.get_audiolink())
                return redirect(url_for("display"))
            else:
                return render_template("end_template.html",
                                   win = is_correct,
                                   title = current_song.get_title(),
                                   artist = current_song.get_artist(),
                                   img_url=current_song.get_img(),
                                   audio=current_song.get_audiolink())
        else:
            return render_template("end_template.html",
                                   win = False,
                                   title = current_song.get_title(),
                                   artist = current_song.get_artist(),
                                   img_url=current_song.get_img(),
                                   audio=current_song.get_audiolink())
            


    

if __name__ == '__main__':
    app.run(port=5000, host="localhost", debug=True)