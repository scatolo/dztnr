# Deezer Rank to Navidrome Ratings (sptnr)

This script repurposes the star ratings in Navidrome by aligning them with Deezer's track rank. It fetches the Deezer popularity rank (0–1,000,000+) for each track via the public search API and maps it to a 1–5 star rating. Higher rank = more popular on Deezer. **No API key is required** — the Deezer API is completely open.

> **This is a fork of [krestaino/sptnr](https://github.com/krestaino/sptnr) by Kevin Restaino**, which originally used Spotify's popularity score. This fork replaces Spotify with Deezer's public API, removing the need for OAuth, client secrets, or any authentication. See [Building from this fork](#building-from-this-fork) for local build instructions.

![Screenshot of script and phone](https://i.imgur.com/7NhSQFM.png)

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Quick Start](#quick-start)
4. [Building from this fork](#building-from-this-fork)
5. [Using Docker Compose](#using-docker-compose)
6. [Running Natively or Building Locally](#running-natively-or-building-locally)
7. [Usage](#usage)
8. [Examples](#examples)
9. [Resuming Interrupted Sessions](#resuming-interrupted-sessions)
10. [Managing Docker Containers](#managing-docker-containers)
11. [Mapping Deezer Rank to Navidrome Ratings](#mapping-deezer-rank-to-navidrome-ratings)
12. [Estimated Processing Times](#estimated-processing-times)
13. [Importance of Accurate Metadata for Track Lookup](#importance-of-accurate-metadata-for-track-lookup)
14. [Logs](#logs)
15. [Credits](#credits)

## Features

- **Deezer Integration**: Uses the public Deezer Search API (`api.deezer.com/search`) — no API key or authentication needed.
- **Navidrome Integration**: Updates track ratings in Navidrome based on Deezer's popularity rank.
- **Flexible Processing**: Process specific artists, albums, or a range of artists or albums.
- **Preview Mode**: Run the script in preview mode to see changes without making any actual updates.
- **Logging**: Detailed logging of the process, both in the console and to a file.
- **Docker Support**: Run the script in a Docker container for consistent environments and ease of use.

## Requirements

- Python 3.x or Docker
- Access to a Navidrome server
- No API keys or external accounts required (Deezer API is public)

**Compatibility Note**: While this script was built with Navidrome in mind, it should theoretically work on any Subsonic server.

## Quick Start

```console
docker build -t sptnr-local .
docker run -t \
  -e NAV_BASE_URL=your_navidrome_server_url \
  -e NAV_USER=your_navidrome_username \
  -e NAV_PASS=your_navidrome_password \
  sptnr-local
```

**Note**: The `-t` flag is used to allocate a pseudo-terminal which assists in displaying colored and bold text in the terminal output, which this script uses.

## Building from this fork

This is a fork of [krestaino/sptnr](https://github.com/krestaino/sptnr). The main changes are:
- **Deezer** instead of Spotify — no OAuth, no client ID/secret, no API key
- Rating based on Deezer rank instead of Spotify popularity
- Rate limiting at 0.2s per call

Clone and build:

```bash
git clone <this-repo-url>
cd sptnr-main
docker build -t sptnr-local .
docker run -t \
  -e NAV_BASE_URL=your_navidrome_server_url \
  -e NAV_USER=your_navidrome_username \
  -e NAV_PASS=your_navidrome_password \
  sptnr-local
```

Run natively with Python:

```bash
cp .env.example .env
# Edit .env with your Navidrome URL and credentials
pip install -r requirements.txt
python sptnr.py -p -l 1   # preview mode, first artist only
```

### Using Docker Compose

1. **Create `docker-compose.yml` File**: Copy the example and replace the environment variables:

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
       volumes:
         - ./logs:/usr/src/app/logs
   ```

2. **Run the Script**:

   ```console
   docker-compose run sptnr
   ```

## Running Natively or Building Locally

### Running Natively (Without Docker)

1. **Clone the Repository**: Clone or download the necessary files (`sptnr.py`, `requirements.txt`, `.env.example`).

2. **Install Python Packages**:

   ```console
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**: Rename `.env.example` to `.env` and fill in your Navidrome details:

   ```console
   mv .env.example .env
   # Edit the .env file with your Navidrome URL, user, and password
   ```

4. **Run the Script**:

   ```console
   python sptnr.py [options]
   ```

### Building and Running with Docker Locally

1. **Clone the Repository** and download the necessary files.

2. **Configure Docker Compose**: Rename and edit `docker-compose.yml`:

   ```console
   mv docker-compose.yml.example docker-compose.yml
   # Edit the docker-compose.yml file
   ```

3. **Set the Docker Image Source**: Uncomment `build: .` in `docker-compose.yml`.

4. **Build and Run**:

   ```console
   docker-compose build
   docker-compose run sptnr [options]
   ```

## Usage

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

  - Python: `python sptnr.py -p`
  - Docker Compose: `docker-compose run sptnr -p`

- **Process Specific Artist**:

  - Python: `python sptnr.py -a artist_id`
  - Docker Compose: `docker-compose run sptnr -a artist_id`

- **Process Specific Albums**:

  - Python: `python sptnr.py -b album_id1 -b album_id2`
  - Docker Compose: `docker-compose run sptnr -b album_id1 -b album_id2`

- **Process Range of Artists**:

  - Python: `python sptnr.py -s 10 -l 5`
  - Docker Compose: `docker-compose run sptnr -s 10 -l 5`

## Resuming Interrupted Sessions

In cases where your session gets interrupted — for instance, if your machine goes to sleep or you encounter network issues — you can resume from where you left off.

Check the log file for the last processed artist. The log entry contains the index in brackets: `Artist: ARTIST_NAME (ARTIST_ID)[INDEX]`.

Restart the script using `-s INDEX`:

- Python: `python sptnr.py -s INDEX`
- Docker Compose: `docker-compose run sptnr -s INDEX`

## Managing Docker Containers

`docker-compose run` creates a new container each time it's executed. To clean up stopped containers:

```console
docker container prune
```

**Important**: This removes **all** stopped containers on your system. Check with `docker ps -a` first.

## Mapping Deezer Rank to Navidrome Ratings

The script translates Deezer's popularity rank into Navidrome's 5-star rating system:

| Deezer Rank        | Rating | Description        |
| ------------------ | ------ | ------------------ |
| 0 – 9,999          | 0      | Unknown / Niche    |
| 10,000 – 99,999    | 1      | Low popularity     |
| 100,000 – 299,999  | 2      | Moderately popular |
| 300,000 – 599,999  | 3      | Popular            |
| 600,000 – 849,999  | 4      | Very popular       |
| 850,000+           | 5      | Globally known     |

## Estimated Processing Times

With a `time.sleep(0.2)` delay between Deezer API calls:

| Library Size (Tracks) | Estimated Time |
| --------------------- | -------------- |
| 1,000                 | ~5 minutes     |
| 5,000                 | ~25 minutes    |
| 10,000                | ~50 minutes    |
| 50,000                | ~4 hours       |
| 100,000               | ~8 hours       |

These estimates assume a stable network connection. Actual times may vary.

## Importance of Accurate Metadata for Track Lookup

The script searches Deezer using the query `artist + track`. Deezer's search is fairly forgiving, but **accurate artist and track titles** significantly improve the match rate.

For best results, tag your music library with **MusicBrainz** before running the script.

## Logs

Logs are stored in the `logs` directory, and each script execution creates a new log file marked with a timestamp. Delete old logs manually if they are no longer needed.

### Log Format

The script uses `rank → ★rating` format:

- `r:123456` — Deezer rank (0–1,000,000+)
- `→ ★:3` — Navidrome star rating assigned

Example: `r:450000 → ★:3 | Song Title`

### Terminal Output Colors

- **Red**: Tracks not found on Deezer (shown as `??`)
- **Green**: Successful matches and processing

These colors are exclusive to the terminal output and are not included in the log files.

## Credits

This project is a fork of **[krestaino/sptnr](https://github.com/krestaino/sptnr)** by **Kevin Restaino**, who originally created the script to sync Spotify popularity with Navidrome ratings. This fork adapts the codebase to use Deezer's public API instead, removing the need for any authentication or API keys while preserving all the original Navidrome integration logic, CLI flags, and Docker support.
