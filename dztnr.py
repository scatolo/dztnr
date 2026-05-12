with open("VERSION", "r") as file:
    __version__ = file.read().strip()

import argparse
import json
import logging
import os
import re
import sys
import time
import urllib.parse

from dotenv import load_dotenv
import requests
from colorama import init, Fore, Style
from tqdm import tqdm

# Load environment variables from .env file if it exists
if os.path.exists(".env"):
    load_dotenv()

# Record the start time
start_time = time.time()

# Config
NAV_BASE_URL = os.getenv("NAV_BASE_URL")
NAV_USER = os.getenv("NAV_USER")
NAV_PASS = os.getenv("NAV_PASS")

# Colors
LIGHT_PURPLE = Fore.MAGENTA + Style.BRIGHT
LIGHT_GREEN = Fore.GREEN + Style.BRIGHT
LIGHT_RED = Fore.RED + Style.BRIGHT
LIGHT_BLUE = Fore.BLUE + Style.BRIGHT
LIGHT_CYAN = Fore.CYAN + Style.BRIGHT
LIGHT_YELLOW = Fore.YELLOW + Style.BRIGHT
BOLD = Style.BRIGHT
RESET = Style.RESET_ALL

# Setup logs
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOGFILE = os.path.join(LOG_DIR, f"deezer-rank_{int(time.time())}.log")


class NoColorFormatter(logging.Formatter):
    ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")

    def format(self, record):
        record.msg = self.ansi_escape.sub("", record.msg)
        return super(NoColorFormatter, self).format(record)


# Set up the stream handler (console logging) without timestamp
logging.basicConfig(
    level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler()]
)

# Set up the file handler (file logging) with timestamp
file_handler = logging.FileHandler(LOGFILE, "a")
file_handler.setFormatter(NoColorFormatter("[%(asctime)s] %(message)s"))
logging.getLogger().addHandler(file_handler)

# Auth
HEX_ENCODED_PASS = NAV_PASS.encode().hex()

init(autoreset=True)

# Default flags
PREVIEW = 0
START = 0
LIMIT = 0
ARTIST_IDs = []
ALBUM_IDs = []

# Variables
ARTISTS_PROCESSED = 0
TOTAL_TRACKS = 0
FOUND_AND_UPDATED = 0
NOT_FOUND = 0
UNMATCHED_TRACKS = []

# Parse arguments
description_text = "process command-line flags for sync"
parser = argparse.ArgumentParser()

parser.add_argument(
    "-p",
    "--preview",
    action="store_true",
    help="execute script in preview mode (no changes made)",
)
parser.add_argument(
    "-a",
    "--artist",
    action="append",
    help="process the artist using the Navidrome artist ID (ignores START and LIMIT)",
    type=str,
)
parser.add_argument(
    "-b",
    "--album",
    action="append",
    help="process the album using the Navidrome album ID (ignores START and LIMIT)",
    type=str,
)
parser.add_argument(
    "-s",
    "--start",
    default=0,
    type=int,
    help="start processing from artist at index [NUM] (0-based index, so 0 is the first artist)",
)
parser.add_argument(
    "-l",
    "--limit",
    default=0,
    type=int,
    help="limit to processing [NUM] artists from the start index",
)

parser.add_argument(
    "-v", "--version", action="version", version=f"%(prog)s {__version__}"
)


args = parser.parse_args()

ARTIST_IDs = args.artist if args.artist else []
ALBUM_IDs = args.album if args.album else []
START = args.start
LIMIT = args.limit

logging.info(f"{BOLD}Version:{RESET} {LIGHT_YELLOW}dztnr v{__version__}{RESET}")

if args.preview:
    logging.info(f"{LIGHT_YELLOW}Preview mode, no changes will be made.{RESET}")
    PREVIEW = 1

# Check if both ARTIST_ID and START/LIMIT are provided
if ARTIST_IDs and (START != 0 or LIMIT != 0):
    START = 0
    LIMIT = 0
    logging.info(
        f"{LIGHT_YELLOW}Warning: The --artist flag overrides --start and --limit. Ignoring these settings.{RESET}"
    )

if not args.preview:
    logging.info(
        f"{BOLD}Syncing Deezer {LIGHT_CYAN}rank{RESET}{BOLD} with Navidrome {LIGHT_BLUE}rating{RESET}...{RESET}"
    )


def validate_url(url):
    if not re.match(r"https?://", url):
        logging.error(
            f"{LIGHT_RED}Config Error: URL must start with 'http://' or 'https://'.{RESET}"
        )
        return False
    if url.endswith("/"):
        logging.error(
            f"{LIGHT_RED}Config Error: URL must not end with a trailing slash.{RESET}"
        )
        return False
    return True


def url_encode(string):
    return urllib.parse.quote_plus(string)


def get_rating_from_rank(rank):
    rank = int(rank)
    if rank < 10000:
        return 0
    elif rank < 100000:
        return 1
    elif rank < 300000:
        return 2
    elif rank < 600000:
        return 3
    elif rank < 850000:
        return 4
    else:
        return 5


def process_track(track_id, artist_name, album, track_name):
    def get_deezer_rank(artist, track):
        encoded_query = url_encode(f"{artist}+{track}")
        deezer_url = f"https://api.deezer.com/search?q={encoded_query}"
        try:
            response = requests.get(deezer_url)
        except requests.exceptions.ConnectionError:
            logging.error(f"{LIGHT_RED}Deezer Error: Unable to reach server.{RESET}")
            sys.exit(1)
        try:
            data = response.json()
        except ValueError as e:
            logging.error(
                f"{LIGHT_RED}Deezer Error: Error decoding JSON from Deezer API: {e}{RESET}"
            )
            sys.exit(1)
        if not data.get("data"):
            return None
        rank = data["data"][0].get("rank")
        if rank is None:
            return None
        logging.info(f"      [DEBUG] url: {deezer_url}")
        logging.info(f"      [DEBUG] rank: {rank}")
        return int(rank)

    rank = get_deezer_rank(artist_name, track_name)
    time.sleep(0.2)

    if rank is not None:
        rating = get_rating_from_rank(rank)
        rank_str = f"{rank} " if 0 <= rank <= 9 else str(rank)
        message = f"    r:{LIGHT_CYAN}{rank_str}{RESET} → ★:{LIGHT_BLUE}{rating}{RESET} | {LIGHT_GREEN}{track_name}{RESET}"
        logging.info(message)
        if PREVIEW != 1:
            nav_url = f"{NAV_BASE_URL}/rest/setRating?u={NAV_USER}&p=enc:{HEX_ENCODED_PASS}&v=1.12.0&c=deezer_sync&id={track_id}&rating={rating}"
            try:
                nav_response = requests.get(nav_url)
                if nav_response.status_code != 200:
                    logging.warning(
                        f"    {LIGHT_YELLOW}Navidrome setRating failed ({nav_response.status_code}): {track_name}{RESET}"
                    )
            except requests.exceptions.RequestException as e:
                logging.warning(
                    f"    {LIGHT_YELLOW}Navidrome setRating error: {e} | {track_name}{RESET}"
                )
        global FOUND_AND_UPDATED
        FOUND_AND_UPDATED += 1
    else:
        logging.info(
            f"    r:{LIGHT_RED}??{RESET} → ★:{LIGHT_BLUE}0{RESET} | {LIGHT_RED}(not found) {track_name}{RESET}"
        )
        global UNMATCHED_TRACKS
        UNMATCHED_TRACKS.append(f"{artist_name} - {album} - {track_name}")
        global NOT_FOUND
        NOT_FOUND += 1

    global TOTAL_TRACKS
    TOTAL_TRACKS += 1


def process_album(album_id):
    nav_url = f"{NAV_BASE_URL}/rest/getAlbum?id={album_id}&u={NAV_USER}&p=enc:{HEX_ENCODED_PASS}&v=1.12.0&c=deezer_sync&f=json"
    response = requests.get(nav_url).json()

    album_info = response["subsonic-response"]["album"]
    album_artist = album_info["artist"]
    tracks = [
        (song["id"], album_artist, song["album"], song["title"])
        for song in album_info.get("song", [])
    ]

    for track in tracks:
        process_track(*track)


def process_artist(artist_id):
    nav_url = f"{NAV_BASE_URL}/rest/getArtist?id={artist_id}&u={NAV_USER}&p=enc:{HEX_ENCODED_PASS}&v=1.12.0&c=deezer_sync&f=json"
    response = requests.get(nav_url).json()

    albums = [
        (album["id"], album["name"])
        for album in response["subsonic-response"]["artist"].get("album", [])
    ]

    for album_id, album_name in albums:
        logging.info(f"  Album: {LIGHT_YELLOW}{album_name}{RESET} ({album_id})")
        process_album(album_id)


def fetch_data(url):
    try:
        response = requests.get(url)
        response_data = json.loads(response.text)

        if "subsonic-response" not in response_data:
            logging.error(
                f"{LIGHT_RED}Unexpected response format from Navidrome.{RESET}"
            )
            sys.exit(1)

        nav_response = response_data["subsonic-response"]

        if "error" in nav_response:
            error_message = nav_response["error"].get("message", "Unknown error")
            logging.error(f"{LIGHT_RED}Navidrome Error: {error_message}{RESET}")
            sys.exit(1)

        return nav_response

    except requests.exceptions.ConnectionError:
        logging.error(
            f"{LIGHT_RED}Connection Error: Failed to connect to the provided URL. Please check if the URL is correct and the server is reachable.{RESET}"
        )
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        logging.error(
            f"{LIGHT_RED}Connection Error: An error occurred while trying to connect to Navidrome: {e}{RESET}"
        )
        sys.exit(1)
    except json.JSONDecodeError:
        logging.error(
            f"{LIGHT_RED}JSON Parsing Error: Failed to parse JSON response from Navidrome. Please check if the provided URL is a valid Navidrome server.{RESET}"
        )
        sys.exit(1)


try:
    validate_url(NAV_BASE_URL)
except ValueError as e:
    logging.error(f"{LIGHT_RED}{e}{RESET}")
    sys.exit(1)

if ARTIST_IDs:
    for ARTIST_ID in ARTIST_IDs:
        url = f"{NAV_BASE_URL}/rest/getArtist?id={ARTIST_ID}&u={NAV_USER}&p=enc:{HEX_ENCODED_PASS}&v=1.12.0&c=deezer_sync&f=json"
        data = fetch_data(url)
        ARTIST_NAME = data["artist"]["name"]

        logging.info("")
        logging.info(f"Artist: {LIGHT_PURPLE}{ARTIST_NAME}{RESET} ({ARTIST_ID})")
        process_artist(ARTIST_ID)

elif ALBUM_IDs:
    for ALBUM_ID in ALBUM_IDs:
        url = f"{NAV_BASE_URL}/rest/getAlbum?id={ALBUM_ID}&u={NAV_USER}&p=enc:{HEX_ENCODED_PASS}&v=1.12.0&c=deezer_sync&f=json"
        data = fetch_data(url)
        ARTIST_NAME = data["album"]["artist"]
        ARTIST_ID = data["album"]["artistId"]
        ALBUM_NAME = data["album"]["name"]

        logging.info("")
        logging.info(f"Artist: {LIGHT_PURPLE}{ARTIST_NAME}{RESET} ({ARTIST_ID})")
        logging.info(f"  Album: {LIGHT_YELLOW}{ALBUM_NAME}{RESET} ({ALBUM_ID})")
        process_album(ALBUM_ID)

else:
    url = f"{NAV_BASE_URL}/rest/getArtists?u={NAV_USER}&p=enc:{HEX_ENCODED_PASS}&v=1.12.0&c=deezer_sync&f=json"
    data = fetch_data(url)
    ARTIST_DATA = [
        (artist["id"], artist["name"])
        for index_entry in data["artists"]["index"]
        for artist in index_entry["artist"]
    ]

    if START == 0 and LIMIT == 0:
        data_slice = ARTIST_DATA
        total_count = len(ARTIST_DATA)
    else:
        if LIMIT == 0:
            data_slice = ARTIST_DATA[START:]
        else:
            data_slice = ARTIST_DATA[START : START + LIMIT]
        total_count = len(data_slice)

    logging.info(f"Total artists to process: {LIGHT_GREEN}{total_count}{RESET}")

    for index, ARTIST_ENTRY in tqdm(
        enumerate(data_slice), total=total_count, leave=False
    ):
        ARTIST_ID, ARTIST_NAME = ARTIST_ENTRY

        logging.info("")
        logging.info(
            f"Artist: {LIGHT_PURPLE}{ARTIST_NAME}{RESET} ({ARTIST_ID})[{index}]"
        )
        process_artist(ARTIST_ID)

        ARTISTS_PROCESSED += 1


# Display the results
logging.info("")
MATCH_PERCENTAGE = (FOUND_AND_UPDATED / TOTAL_TRACKS) * 100 if TOTAL_TRACKS != 0 else 0
FORMATTED_MATCH_PERCENTAGE = round(MATCH_PERCENTAGE, 2)  # Rounding to 2 decimal places
TOTAL_BLOCKS = 20

color_found = LIGHT_GREEN if FOUND_AND_UPDATED == TOTAL_TRACKS else LIGHT_YELLOW
color_found_white = LIGHT_GREEN if FOUND_AND_UPDATED == TOTAL_TRACKS else BOLD
color_not_found = LIGHT_GREEN if NOT_FOUND == 0 else LIGHT_RED
blocks_found = "█" * round(FOUND_AND_UPDATED * TOTAL_BLOCKS / TOTAL_TRACKS)
blocks_not_found = "█" * (TOTAL_BLOCKS - len(blocks_found))
full_blocks_found = f"{color_found_white}{blocks_found}{RESET}"
full_blocks_not_found = f"{color_not_found}{blocks_not_found}{RESET}"

# Calculate elapsed time
elapsed_time = time.time() - start_time
hours, remainder = divmod(elapsed_time, 3600)
minutes, seconds = divmod(remainder, 60)

parts = []
if hours:
    parts.append(f"{int(hours)}h")
if minutes:
    parts.append(f"{int(minutes)}m")
if seconds or not parts:  # Show seconds if it's the only value, even if it's 0
    parts.append(f"{int(seconds)}s")

formatted_elapsed_time = " ".join(parts)

# logging.info(f"Processing completed in {int(hours):02}:{int(minutes):02}:{int(seconds):02}")
logging.info(
    f"Tracks: {LIGHT_PURPLE}{TOTAL_TRACKS}{RESET} | Found: {color_found}{FOUND_AND_UPDATED}{RESET} |{full_blocks_found}{full_blocks_not_found}| Not Found: {color_not_found}{NOT_FOUND}{RESET} | Match: {color_found}{FORMATTED_MATCH_PERCENTAGE}%{RESET} | Time: {LIGHT_PURPLE}{formatted_elapsed_time}{RESET}"
)
