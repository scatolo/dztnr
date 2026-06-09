# Deezer Rank to Navidrome Ratings (dztnr)

This script repurposes the star ratings in Navidrome by aligning them with Deezer's track rank. It fetches the Deezer popularity rank (0–1,000,000+) for each track via the public search API and maps it to a 1–5 star rating. Higher rank = more popular on Deezer. **No API key is required** — the Deezer API is completely open.

> **This is a fork of [krestaino/sptnr](https://github.com/krestaino/sptnr) by Kevin Restaino**, which originally used Spotify's popularity score. This fork replaces Spotify with Deezer's public API, removing the need for OAuth, client secrets, or any authentication.

![Screenshot of script and phone](https://i.imgur.com/7NhSQFM.png)

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Quick Start (GHCR pre-built image)](#quick-start-ghcr-pre-built-image)
4. [Building from this fork](#building-from-this-fork)
5. [Using Docker Compose](#using-docker-compose)
6. [Running Natively (Python)](#running-natively-python)
7. [Usage](#usage)
8. [Examples](#examples)
9. [Resuming Interrupted Sessions](#resuming-interrupted-sessions)
10. [Managing Docker Containers](#managing-docker-containers)
11. [Mapping Deezer Rank to Navidrome Ratings](#mapping-deezer-rank-to-navidrome-ratings)
12. [Estimated Processing Times](#estimated-processing-times)
13. [Importance of Accurate Metadata for Track Lookup](#importance-of-accurate-metadata-for-track-lookup)
14. [Logs](#logs)
15. [CI/CD (GitHub Actions)](#cicd-github-actions)
16. [Credits](#credits)

## Features

- **Deezer Integration**: Uses the public Deezer Search API (`api.deezer.com/search`) — no API key or authentication needed.
- **Navidrome Integration**: Updates track ratings in Navidrome based on Deezer's popularity rank.
- **Flexible Processing**: Process specific artists, albums, or a range of artists or albums.
- **Preview Mode**: Run the script in preview mode to see changes without making any actual updates.
- **Logging**: Detailed logging of the process, both in the console and to a file.
- **Docker Support**: Pre-built image available on GitHub Container Registry (GHCR) with multi-arch support (amd64 + arm64).

## Requirements

- Docker **or** Python 3.x
- Access to a Navidrome server
- No API keys or external accounts required (Deezer API is public)

**Compatibility Note**: While this script was built with Navidrome in mind, it should theoretically work on any Subsonic server.

## Quick Start (GHCR pre-built image)

The easiest way to run dztnr is using the pre-built Docker image published to GitHub Container Registry on every push to `main`. It supports both `linux/amd64` and `linux/arm64`.

```console
docker run -t --rm \
  -e NAV_BASE_URL=https://your_navidrome.example.com \
  -e NAV_USER=your_navidrome_username \
  -e NAV_PASS=your_navidrome_password \
  ghcr.io/scatolo/dztnr:latest
```

To pin a specific version (check [packages](https://github.com/scatolo/dztnr/pkgs/container/dztnr) for available tags):

```console
docker run -t --rm \
  -e NAV_BASE_URL=https://your_navidrome.example.com \
  -e NAV_USER=your_navidrome_username \
  -e NAV_PASS=your_navidrome_password \
  ghcr.io/scatolo/dztnr:1.3.0
```

> **Tip**: Use `--rm` to auto-remove the container when it finishes. If you want persistent logs, add `-v ./logs:/usr/src/app/logs`.

**First run?** Start in preview mode with a single artist to test connectivity:

```console
docker run -t --rm \
  -e NAV_BASE_URL=https://your_navidrome.example.com \
  -e NAV_USER=your_admin_user \
  -e NAV_PASS=your_admin_password \
  ghcr.io/scatolo/dztnr:latest -p -l 1
```

(`-p` = preview, no writes; `-l 1` = only the first artist)

## Building from this fork

This is a fork of [krestaino/sptnr](https://github.com/krestaino/sptnr). The main changes are:
- **Deezer** instead of Spotify — no OAuth, no client ID/secret, no API key
- Rating based on Deezer rank instead of Spotify popularity
- Rate limiting at 0.2s per API call
- Pre-built images published to GHCR via GitHub Actions

### Build locally

```bash
git clone https://github.com/scatolo/dztnr.git
cd dztnr
docker build -t dztnr-local .
docker run -t --rm \
  -e NAV_BASE_URL=https://your_navidrome.example.com \
  -e NAV_USER=your_navidrome_username \
  -e NAV_PASS=your_navidrome_password \
  dztnr-local
```

### Run natively with Python

```bash
git clone https://github.com/scatolo/dztnr.git
cd dztnr
cp .env.example .env
# Edit .env with your Navidrome URL and credentials
pip install -r requirements.txt
python dztnr.py -p -l 1   # preview mode, first artist only
```

## Using Docker Compose

1. **Create `docker-compose.yml`:** copy `docker-compose.yml.example` and fill in your Navidrome details.

   **Using the pre-built GHCR image (recommended):**

   ```yaml
   version: "3.8"

   services:
     dztnr:
       container_name: dztnr
       image: ghcr.io/scatolo/dztnr:latest
       environment:
         - NAV_BASE_URL=https://your_navidrome.example.com
         - NAV_USER=your_navidrome_username
         - NAV_PASS=your_navidrome_password
       volumes:
         - ./logs:/usr/src/app/logs
   ```

   **Or build locally:**

   ```yaml
   version: "3.8"

   services:
     dztnr:
       container_name: dztnr
       build: .
       environment:
         - NAV_BASE_URL=https://your_navidrome.example.com
         - NAV_USER=your_navidrome_username
         - NAV_PASS=your_navidrome_password
       volumes:
         - ./logs:/usr/src/app/logs
   ```

2. **Run the script:**

   ```console
   docker-compose run --rm dztnr
   ```

   With options:

   ```console
   docker-compose run --rm dztnr -p -l 1
   ```

## Running Natively (Python)

1. **Clone the repository** or download the necessary files (`dztnr.py`, `requirements.txt`, `.env.example`).

2. **Install dependencies:**

   ```console
   pip install -r requirements.txt
   ```

3. **Configure environment variables.** Rename `.env.example` to `.env` and fill in your Navidrome credentials:

   ```bash
   cp .env.example .env
   # Edit .env — only NAV_BASE_URL, NAV_USER, NAV_PASS are needed
   ```

4. **Run the script:**

   ```console
   python dztnr.py [options]
   ```

## Usage

### Options

| Flag | Long form  | Description |
|------|-----------|-------------|
| `-p` | `--preview` | Preview mode — no changes written to Navidrome |
| `-a` | `--artist ID` | Process a specific artist by Navidrome ID (repeatable) |
| `-b` | `--album ID` | Process a specific album by Navidrome ID (repeatable) |
| `-s` | `--start N` | Start processing from artist at index N (0-based) |
| `-l` | `--limit N` | Process at most N artists from the start index |
| `-v` | `--version` | Print version and exit |

### Command Formats

| Method       | Command |
|-------------|---------|
| **GHCR image** | `docker run -t --rm -e NAV_BASE_URL=... -e NAV_USER=... -e NAV_PASS=... ghcr.io/scatolo/dztnr:latest [options]` |
| **Local Docker** | `docker run -t --rm -e NAV_BASE_URL=... -e NAV_USER=... -e NAV_PASS=... dztnr-local [options]` |
| **Docker Compose (GHCR)** | `docker-compose run --rm dztnr [options]` |
| **Python** | `python dztnr.py [options]` |

## Examples

### Preview Mode
See what would be updated without making changes:
```console
python dztnr.py -p
```
```console
docker-compose run --rm dztnr -p
```

### Process a Single Artist
```console
python dztnr.py -a <navidrome_artist_id>
```
```console
docker run -t --rm -e NAV_BASE_URL=... -e NAV_USER=... -e NAV_PASS=... ghcr.io/scatolo/dztnr:latest -a <navidrome_artist_id>
```

### Process a Range of Artists
Start from artist #10 and process the next 5:
```console
python dztnr.py -s 10 -l 5
```

### Process Specific Albums
```console
python dztnr.py -b <album_id_1> -b <album_id_2>
```

## Resuming Interrupted Sessions

If the session gets interrupted (network error, machine sleep, etc.), you can resume from where you left off.

Check the log file for the last processed artist. The log entry contains the index in brackets: `Artist: ARTIST_NAME (ARTIST_ID)[INDEX]`.

Restart with `-s INDEX`:

```console
python dztnr.py -s 42
```

```console
docker run -t --rm -e ... ghcr.io/scatolo/dztnr:latest -s 42
```

## Managing Docker Containers

`docker run` and `docker-compose run` create a new container each time. Use `--rm` to auto-remove them on exit, or clean up manually:

```console
docker container prune
```

**Warning**: This removes **all** stopped containers on your system. Check with `docker ps -a` first.

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

The script searches Deezer using the query `artist + track`. Deezer's search is fairly forgiving, but **accurate artist and track titles** significantly improve the match rate. Tag your music library with **MusicBrainz** for best results.

## Logs

Logs are stored in the `logs/` directory. Each execution creates a new log file named `deezer-rank_<timestamp>.log`. Delete old logs manually if needed.

### Log Format

```
r:450000 → ★:3 | Song Title
```

- `r:<number>` — Deezer rank (0–1,000,000+), or `??` if not found
- `→ ★:<rating>` — Navidrome star rating assigned (0–5)

### Terminal Output Colors

- **Green** — Track matched and processed
- **Red** — Track not found on Deezer (`??`)

Colors are terminal-only and stripped from log files.

## CI/CD (GitHub Actions)

On every push to `main`, a GitHub Actions workflow (`.github/workflows/docker-ghcr.yml`) builds a multi-arch Docker image (`linux/amd64` + `linux/arm64`) tagged with the version from the `VERSION` file and `latest`, then pushes it to **GitHub Container Registry** at `ghcr.io/scatolo/dztnr`.

Pull requests also trigger a build (amd64 only, no push) to validate the Dockerfile.

Available tags: [github.com/scatolo/dztnr/pkgs/container/dztnr](https://github.com/scatolo/dztnr/pkgs/container/dztnr)

## Credits

This project is a fork of **[krestaino/sptnr](https://github.com/krestaino/sptnr)** by **Kevin Restaino**, who originally created the script to sync Spotify popularity with Navidrome ratings. This fork adapts the codebase to use Deezer's public API instead, removing the need for any authentication or API keys while preserving all the original Navidrome integration logic, CLI flags, and Docker support.
