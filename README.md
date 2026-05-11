# Last.fm Listeners to Navidrome Ratings (sptnr)

This script repurposes the star ratings in Navidrome by aligning them with Last.fm global listener counts. Instead of Spotify's popularity score (0-100), it now fetches the total number of unique listeners for each track from the Last.fm API and maps them to a 1-5 star rating using a logarithmic scale. This gives a much more meaningful signal: a track with millions of listeners is globally known, while one with <1000 listeners is obscure.

> **Fork note**: This version replaces Spotify with Last.fm. No OAuth flow is required — only a single API key. See [Building from this fork](#building-from-this-fork) for local build instructions.

![Screenshot of script and phone](https://i.imgur.com/7NhSQFM.png)

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Getting a Last.fm API Key](#getting-a-lastfm-api-key)
4. [Quick Start](#quick-start)
5. [Building from this fork](#building-from-this-fork)
6. [Using Docker Compose](#using-docker-compose)
7. [Running Natively or Building Locally](#running-natively-or-building-locally)
8. [Usage](#usage)
9. [Examples](#examples)
10. [Resuming Interrupted Sessions](#resuming-interrupted-sessions)
11. [Managing Docker Containers](#managing-docker-containers)
12. [Mapping Last.fm Listeners to Navidrome Ratings](#mapping-lastfm-listeners-to-navidrome-ratings)
13. [Estimated Processing Times](#estimated-processing-times)
14. [Importance of Accurate Metadata for Track Lookup](#importance-of-accurate-metadata-for-track-lookup)
15. [Logs](#logs)

## Features

- **Last.fm Integration**: Connects to the Last.fm API to fetch global listener counts for tracks using artist + track name lookup with `autocorrect=1`.
- **Navidrome Integration**: Updates track ratings in Navidrome based on Last.fm listener counts.
- **Flexible Processing**: Process specific artists, albums, or a range of artists or albums.
- **Preview Mode**: Run the script in preview mode to see changes without making any actual updates.
- **Logging**: Detailed logging of the process, both in the console and to a file.
- **Docker Support**: Run the script in a Docker container for consistent environments and ease of use.

## Requirements

- Python 3.x or Docker
- A Last.fm API key ([see below](#getting-a-lastfm-api-key))
- Access to a Navidrome server

**Compatibility Note**: While this script was built with Navidrome in mind, it should theoretically work on any Subsonic server. If you successfully use it with other Subsonic servers, please open an issue to let me know, so I can document it and assist others.

## Getting a Last.fm API Key

1. Go to [last.fm/api/account/create](https://www.last.fm/api/account/create)
2. Fill in the form:
   - **Application name**: any name (e.g. `sptnr`)
   - **Application description**: short description
   - Leave **Callback URL** and **Application homepage** empty (not needed)
3. Submit the form. You will receive an **API Key** immediately — no approval wait.
4. Copy the API Key; you will use it as `LASTFM_API_KEY`.

> Unlike Spotify, Last.fm does not require OAuth, client secrets, or token refresh. A single API key is all you need.

## Quick Start

You can run the script with environment variables. Replace the placeholder values with your own:

```console
docker build -t sptnr-local .
docker run -t \
  -e NAV_BASE_URL=your_navidrome_server_url \
  -e NAV_USER=your_navidrome_username \
  -e NAV_PASS=your_navidrome_password \
  -e LASTFM_API_KEY=your_lastfm_api_key \
  sptnr-local
```

**Note**: The `-t` flag is used to allocate a pseudo-terminal which assists in displaying colored and bold text in the terminal output, which this script uses.

## Building from this fork

If you have cloned this fork and want to build and run the Docker image locally:

```bash
docker build -t sptnr-local .
docker run -t \
  -e NAV_BASE_URL=your_navidrome_server_url \
  -e NAV_USER=your_navidrome_username \
  -e NAV_PASS=your_navidrome_password \
  -e LASTFM_API_KEY=your_lastfm_api_key \
  sptnr-local
```

You can also run it natively with Python after setting up a `.env` file:

```bash
cp .env.example .env
# Edit .env with your Navidrome URL, credentials, and LASTFM_API_KEY
pip install -r requirements.txt
python sptnr.py -p -l 1   # preview mode, first artist only
```

### Using Docker Compose

1. **Create `docker-compose.yml` File**: Copy the example and replace the environment variables with your own details:

   ```yaml
   version: "3.8"

   services:
     sptnr:
       container_name: sptnr
       build: .
       environment:
         - NAV_BASE_URL=your_navidrome_server_url
         - NAV_USER=your_navidrome_username
         - NAV_PASS=your_navidrome_password
         - LASTFM_API_KEY=your_lastfm_api_key
       volumes:
         - ./logs:/usr/src/app/logs
   ```

2. **Run the Script**: Execute the Docker Compose command to run the script:

   ```console
   docker-compose run sptnr
   ```

## Running Natively or Building Locally

For those who prefer running the script natively using Python or building the Docker image locally, the following steps apply:

### Running Natively (Without Docker)

1. **Clone the Repository**: Clone the repository or download the necessary files (`sptnr.py`, `requirements.txt`, `.env.example`) to your local machine.

2. **Install Python Packages**: Use the `requirements.txt` file to install dependencies:

   ```console
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**: Rename `.env.example` to `.env` and fill in your details:

   ```console
   mv .env.example .env
   # Edit the .env file with your details
   ```

4. **Run the Script**: Execute the script with Python:

   ```console
   python sptnr.py [options]
   ```

### Building and Running with Docker Locally

1. **Clone the Repository**: Clone the repository or download the necessary files (`sptnr.py`, `requirements.txt`, `Dockerfile`, `docker-compose.yml.example`) to your local machine.

2. **Configure Docker Compose**: Rename and edit your `docker-compose.yml`:

   ```console
   mv docker-compose.yml.example docker-compose.yml
   # Edit the docker-compose.yml file
   ```

3. **Set the Docker Image Source**: Uncomment the line `build: .` in the `docker-compose.yml` file to build a local Docker image.

4. **Build and Run**: Build the Docker image and run the script:

   ```console
   docker-compose build
   docker-compose run sptnr [options]
   ```

## Usage

The script supports various options for flexible usage. Below are examples of how to run the script with different options, using Python and Docker Compose methods. Replace `[options]` with any of the specified options based on your needs.

### Options

- `-p, --preview`: Execute the script in preview mode (no changes made).
- `-a, --artist ARTIST_ID`: Process a specific artist. Multiple artists can be specified.
- `-b, --album ALBUM_ID`: Process a specific album. Multiple albums can be specified.
- `-s, --start START_INDEX`: Start processing from the artist at the specified index (0-based).
- `-l, --limit LIMIT`: Limit the processing to a specific number of artists from the start index.

### Command Formats

1. **Running Natively (Python)**:

   ```console
   python sptnr.py [options]
   ```

2. **Using Docker Compose**:

   ```console
   docker-compose run sptnr [options]
   ```

3. **Using Docker Run**:
   ```console
   docker run -t [environment variables] sptnr-local [options]
   ```

## Examples

- **Preview Mode**:
  Run the script in preview mode to see changes without making any actual updates.

  - Python: `python sptnr.py -p`
  - Docker Compose: `docker-compose run sptnr -p`

- **Process Specific Artist**:
  Process only one artist by specifying their ID.

  - Python: `python sptnr.py -a artist_id`
  - Docker Compose: `docker-compose run sptnr -a artist_id`

- **Process Specific Albums**:
  Process multiple specific albums by specifying their IDs.

  - Python: `python sptnr.py -b album_id1 -b album_id2`
  - Docker Compose: `docker-compose run sptnr -b album_id1 -b album_id2`

- **Process Range of Artists**:
  Process artists starting from a certain index with a limit.
  - Python: `python sptnr.py -s 10 -l 5`
  - Docker Compose: `docker-compose run sptnr -s 10 -l 5`

## Resuming Interrupted Sessions

In cases where your session gets interrupted — for instance, if your machine goes to sleep, you encounter rate limits from Last.fm, or for any other reason that causes the script to not complete — you have the option to resume from where you left off.

To determine the point of interruption, check the log file. The log entry will contain details of the artist it failed on, along with the index in a format similar to: `Artist: ARTIST_NAME (ARTIST_NAVIDROME_ID)[INDEX]`. Here, the index is enclosed in brackets.

When you restart the script, use the `-s INDEX` option, where `INDEX` is the index number from the log. This tells the script to start processing from that specific artist, skipping all previously processed entries.

Example command to continue from a specific point:

- Python: `python sptnr.py -s INDEX`
- Docker Compose: `docker-compose run sptnr -s INDEX`

_Note: Replace `INDEX` with the specific index number from your log file._

## Managing Docker Containers

In this project, `docker-compose run` is used instead of `docker-compose up`. This choice allows for greater flexibility in passing command-line options directly to the script, which is essential for its varied operational modes. It's important to understand that `docker-compose run` and `docker run` create a new container each time they're executed. If you frequently run the script, you might accumulate a number of these containers. To manage this, the following method can be used to remove stopped Docker containers from your system.

**Important Note**: This command removes **all** stopped containers on your system, not just the ones related to this script. Please ensure that you do not have any other stopped containers that you want to keep before running this command. You can check your stopped containers using `docker ps -a` to ensure that removing them won't affect your other Docker projects or setups.

```console
docker container prune
```

## Mapping Last.fm Listeners to Navidrome Ratings

The script translates Last.fm's global listener count into Navidrome's 5-star rating system using a logarithmic scale. This conversion allows you to quickly gauge a track's worldwide reach directly within Navidrome. The mapping is as follows:

| Listeners         | Rating | Description            |
| ----------------- | ------ | ---------------------- |
| 0 – 999           | 0      | Unknown / Niche        |
| 1,000 – 49,999    | 1      | Low popularity         |
| 50,000 – 199,999  | 2      | Moderately popular     |
| 200,000 – 999,999 | 3      | Popular                |
| 1,000,000 – 4,999,999 | 4 | Very popular         |
| 5,000,000+        | 5      | Globally known / Viral |

## Estimated Processing Times

With a `time.sleep(0.2)` delay between Last.fm API calls, each track takes roughly 0.2–0.5 seconds depending on network latency:

| Library Size (Number of Tracks) | Estimated Processing Time |
| ------------------------------- | ------------------------- |
| 1,000                           | ~5 minutes                |
| 5,000                           | ~25 minutes               |
| 10,000                          | ~50 minutes               |
| 50,000                          | ~4 hours                  |
| 100,000                         | ~8 hours                  |

These estimates assume a stable network connection and Last.fm API availability. Actual times may vary.

## Importance of Accurate Metadata for Track Lookup

The script uses Last.fm's `track.getInfo` endpoint with `autocorrect=1`, which helps correct minor spelling mistakes and canonical artist/track names. However, accurate artist and track titles still improve the match rate significantly.

For best results, tag your music library with **MusicBrainz** before running the script. MusicBrainz provides reliable and standardized music metadata that aligns well with Last.fm's database.

## Logs

Logs are stored in the `logs` directory, and each script execution creates a new log file marked with a timestamp. Since these logs are retained indefinitely, you should manually delete old logs if they are no longer needed.

### Log Format

The script logs its actions in a straightforward format, using `l:123456 → r:3` to summarize operations:

- `l:123456` indicates the Last.fm global listener count, where `123456` is the specific value.
- `→` symbolizes the mapping performed by the script.
- `r:3` shows the Navidrome rating assigned based on the listener count.

### Terminal Output Colors

In the terminal, certain lines are color-coded for quick identification:

- **Red**: Denotes tracks not matched with Last.fm's data. In the logs, these are shown with `??` for listener counts.
- **Green**: Indicates successful matches and processing of tracks.

These colors are exclusive to the terminal output for visual clarity and are not included in the log files to facilitate easier file parsing.
