# hr_app/services.py (Final Corrected Version)

import yt_dlp
import logging

logger = logging.getLogger(__name__)


# This helper can stay, as it's useful for keeping the main server log clean.
class YtDlpLogger:
    def debug(self, msg): pass

    def warning(self, msg): pass

    def error(self, msg): logger.error(f"yt-dlp error: {msg}")


def get_youtube_playlists(channel_url):
    """
    Fetches all public playlists from a YouTube channel using yt-dlp.
    """
    logger.info(f"Fetching playlists for {channel_url} using yt-dlp.")

    ydl_opts = {
        'extract_flat': 'in_playlist',
        'quiet': True,
        'logger': YtDlpLogger(),
        'skip_download': True,
        'source_address': '0.0.0.0',  # Keep this, it can help prevent network blocks
    }

    playlists = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(channel_url, download=False)

            if 'entries' in result:
                for entry in result['entries']:
                    # --- THE FIX IS HERE ---
                    # We accept entries that are either 'YoutubePlaylist' or 'YoutubeTab',
                    # and ensure they have a URL containing 'playlist?list='. This is very robust.
                    entry_type = entry.get('ie_key')
                    entry_url = entry.get('url', '')

                    if (entry_type in ['YoutubePlaylist', 'YoutubeTab']) and ('playlist?list=' in entry_url):

                        # Get the highest resolution thumbnail available
                        thumbnail = "https://i.ytimg.com/vi/default.jpg"  # A fallback image
                        if entry.get('thumbnails'):
                            # The last thumbnail in the list is usually the highest quality
                            thumbnail = entry['thumbnails'][-1]['url']

                        playlists.append({
                            "title": entry.get('title', 'No Title'),
                            "playlist_id": entry.get('id'),
                            "playlist_url": entry_url,
                            "thumbnail_url": thumbnail,
                            # The playlist_count is not always available in this mode, so we provide a fallback
                            "video_count": f"{entry.get('playlist_count', 'N/A')} videos",
                        })

    except Exception as e:
        logger.error(f"An error occurred with yt-dlp: {e}")
        return []

    logger.info(f"Successfully fetched {len(playlists)} playlists.")
    return playlists