# learning/services.py
import requests
from bs4 import BeautifulSoup
import logging

# It's good practice to have a logger
logger = logging.getLogger(__name__)


def get_youtube_playlists(channel_url):
    """
    Scrapes a YouTube channel's playlist page for all public playlists.

    This is optimized to only make a single HTTP request.

    Returns:
        A list of playlist dictionaries or an empty list if an error occurs.
    """
    base_url = "https://www.youtube.com"
    playlists = []

    try:
        # Use a session with headers to look more like a real browser
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.5",
        }
        res = session.get(channel_url, headers=headers, timeout=10)
        res.raise_for_status()  # Raises an exception for bad status codes (4xx or 5xx)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching YouTube channel page: {e}")
        return []  # Return empty list on failure

    soup = BeautifulSoup(res.text, "html.parser")

    # This selector targets the container for each playlist in the grid
    playlist_blocks = soup.select("ytd-grid-playlist-renderer")

    for block in playlist_blocks:
        # Find the main link which contains the title and href
        link_tag = block.select_one("a#video-title")
        if not link_tag:
            continue

        title = link_tag.get("title", "No Title").strip()
        playlist_url = base_url + link_tag.get("href", "")

        # Extract the playlist ID from the URL
        playlist_id = playlist_url.split("list=")[-1]

        # Get the thumbnail URL (often higher quality from 'yt-img-shadow')
        thumb_tag = block.select_one("yt-img-shadow img")
        thumbnail_url = thumb_tag.get("src", "") if thumb_tag else ""

        # Get video count from the overlay
        video_count_tag = block.select_one("span.ytd-thumbnail-overlay-time-status-renderer")
        video_count = video_count_tag.get_text(strip=True) if video_count_tag else "0 videos"

        playlists.append({
            "title": title,
            "playlist_url": playlist_url,
            "playlist_id": playlist_id,
            "thumbnail_url": thumbnail_url,
            "video_count": video_count,
        })

    return playlists