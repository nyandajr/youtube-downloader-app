import yt_dlp
import os
import shutil

# --- Configuration ---
# Set a download directory relative to the script location
DOWNLOAD_DIR = "downloads"
# Create the directory if it doesn't exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
# Output template for downloaded files
OUTPUT_TEMPLATE = os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s')


def fetch_formats(url: str):
    """
    Fetches video information and a list of available formats using yt-dlp.
    Calculates and stores the best available size in 'display_size'.
    Returns a tuple: (info_dict, formats_list)
    """
    ydl_opts = {
        'format': 'best',
        'skip_download': True,
        'noplaylist': True,
        'quiet': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video information without downloading
            info = ydl.extract_info(url, download=False)

            formats = []
            for f in info.get('formats', []):
                # 1. Prioritize exact filesize, fallback to approximate size
                display_size = f.get('filesize') or f.get('filesize_approx')
                
                # 2. Filter out unwanted formats
                if display_size and f.get('format_note') not in ('DASH audio', 'DASH video'):
                    # Store the determined size for use in app.py
                    f['display_size'] = display_size
                    formats.append(f)
            
            # Sort formats by the size calculated above
            formats.sort(key=lambda x: x.get('display_size', 0) if x.get('display_size') is not None else 0, reverse=True)
            
            return info, formats
            
    except Exception as e:
        # Re-raise a general exception that app.py can catch
        raise Exception(f"yt-dlp error during fetch: {e}")


def download_video(url: str, format_info: dict) -> str | None:
    """
    Downloads the video using the specified format_id.
    Returns the final filename on success, or None on failure.
    """
    
    # Define the format string based on format_id
    format_id = format_info.get('format_id')
    
    ydl_opts = {
        'format': format_id,
        'outtmpl': OUTPUT_TEMPLATE,
        'noplaylist': True,
        'quiet': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'progress_hooks': [],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Perform the download
            info = ydl.extract_info(url, download=True)
            
            # Construct the final expected filename from the info dict
            final_filename = ydl.prepare_filename(info, template=OUTPUT_TEMPLATE)
            
            # Check if the file was created successfully
            if os.path.exists(final_filename):
                return final_filename
            
        return None

    except Exception as e:
        print(f"Error during download: {e}")
        return None


def fetch_english_subtitles(url: str) -> bool:
    """
    Checks if English subtitles are available for the video.
    """
    ydl_opts = {
        'writesubtitles': True,
        'skip_download': True,
        'noplaylist': True,
        'quiet': True,
        'subtitleslangs': ['en', 'en-US', 'en-GB'],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Check for English subtitles in the extracted info dictionary
            subtitles = info.get('subtitles', {})
            
            if any(lang in subtitles for lang in ['en', 'en-US', 'en-GB']):
                return True
            
            return False
            
    except Exception:
        return False


def download_english_subtitle(url: str) -> str | None:
    """
    Downloads the English subtitle file for the video.
    Returns the final subtitle filename on success.
    """
    ydl_opts = {
        'writesubtitles': True,
        'skip_download': True,
        'subtitleslangs': ['en'],
        'subtitlesformat': 'srt',
        'outtmpl': OUTPUT_TEMPLATE,
        'noplaylist': True,
        'quiet': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Construct the expected final subtitle filename
            base_filename = ydl.prepare_filename(info, template=OUTPUT_TEMPLATE)
            subtitle_file = f"{os.path.splitext(base_filename)[0]}.en.srt"
            
            if os.path.exists(subtitle_file):
                return subtitle_file
                
            return None

    except Exception as e:
        print(f"Error downloading subtitles: {e}")
        return None