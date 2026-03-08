import streamlit as st
import yt_dlp
import os
import re
from pathlib import Path
import json
import sqlite3
from datetime import datetime
import threading

# Configure Streamlit page
st.set_page_config(
    page_title="YouTube Downloader",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

    /* Global Styles */
    .stApp {
        background-color: #0F0F0F;
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, p {
        font-family: 'Inter', sans-serif;
    }

    /* Header */
    .main-header {
        text-align: center;
        background: linear-gradient(90deg, #FF0000 0%, #FF4B4B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    
    .subtitle {
        text-align: center;
        color: #AAAAAA;
        font-size: 1.1rem;
        margin-bottom: 3rem;
        font-weight: 400;
    }

    /* Inputs */
    .stTextInput > div > div > input {
        background-color: #272727;
        color: white;
        border: 1px solid #3F3F3F;
        border-radius: 12px;
        padding: 12px 15px;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #FF0000;
        box-shadow: 0 0 0 1px #FF0000;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #FF0000 0%, #D00000 100%);
        color: white;
        font-weight: 600;
        border-radius: 12px;
        border: none;
        padding: 0.8rem 2rem;
        box-shadow: 0 4px 15px rgba(255, 0, 0, 0.3);
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 0, 0, 0.4);
    }

    /* Cards */
    .video-card {
        background: #1E1E1E;
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid #333;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        margin-top: 2rem;
    }

    .info-label {
        color: #888;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.2rem;
    }

    .info-value {
        color: #FFF;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }

    /* Success/Error Messages */
    .stSuccess, .stError, .stInfo, .stWarning {
        border-radius: 12px;
        border: none;
    }
    
    /* Select Box */
    .stSelectbox > div > div {
        background-color: #272727;
        color: white;
        border: 1px solid #3F3F3F;
        border-radius: 12px;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #555;
        margin-top: 4rem;
        padding-top: 2rem;
        border-top: 1px solid #222;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Database setup
DB_PATH = "download_history.db"
db_lock = threading.Lock()

def init_database():
    """Initialize the download history database"""
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS download_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                format TEXT,
                filesize INTEGER,
                download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_path TEXT,
                UNIQUE(video_id, format)
            )
        ''')
        conn.commit()
        conn.close()

def add_to_history(video_id, title, url, format_str, filesize, file_path):
    """Add a download to history"""
    with db_lock:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO download_history 
                (video_id, title, url, format, filesize, download_date, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (video_id, title, url, format_str, filesize, datetime.now(), file_path))
            conn.commit()
            conn.close()
        except Exception as e:
            st.error(f"Failed to add to history: {e}")

def get_history(limit=50):
    """Get download history"""
    with db_lock:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT video_id, title, url, format, filesize, download_date, file_path
                FROM download_history
                ORDER BY download_date DESC
                LIMIT ?
            ''', (limit,))
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            return []

def is_downloaded(video_id, format_str=None):
    """Check if a video has been downloaded"""
    with db_lock:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            if format_str:
                cursor.execute('''
                    SELECT COUNT(*) FROM download_history 
                    WHERE video_id = ? AND format = ?
                ''', (video_id, format_str))
            else:
                cursor.execute('''
                    SELECT COUNT(*) FROM download_history 
                    WHERE video_id = ?
                ''', (video_id,))
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except Exception as e:
            return False

def detect_url_type(url):
    """Detect if URL is a video or playlist"""
    if 'list=' in url:
        return 'playlist'
    return 'video'

def get_playlist_info(url):
    """Get playlist information"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                return {
                    'title': info.get('title', 'Unknown Playlist'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'video_count': len(info['entries']),
                    'videos': info['entries']
                }
    except Exception as e:
        raise Exception(f"Could not fetch playlist info: {str(e)}")
    return None


def clean_url(url):
    """Extract clean video URL from playlist or other YouTube URLs"""
    if not url:
        return url
    
    # Extract video ID using regex
    patterns = [
        r'(?:v=|/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed/)([0-9A-Za-z_-]{11})',
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/watch?v={video_id}"
    
    return url

def validate_youtube_url(url):
    """Validate if URL is a proper YouTube URL"""
    if not url:
        return False
    
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:m\.)?youtube\.com/watch\?v=[\w-]+'
    ]
    
    return any(re.match(pattern, url.strip()) for pattern in youtube_patterns)

def get_video_info(url):
    """Get basic video information"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extractaudio': False,
        'skip_download': True,
        'no_playlist': True,
        'fragment_retries': 10,
        'retries': 10,
        'ignoreerrors': 'only_download'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'thumbnail': info.get('thumbnail', None),
                'view_count': info.get('view_count', 0)
            }
    except Exception as e:
        raise Exception(f"Could not fetch video info: {str(e)}")

def get_video_formats(url):
    """Get available video formats with proper audio+video combinations"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'no_playlist': True,
        'listformats': False
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            video_formats = []
            audio_formats = []
            combined_formats = []
            
            # Get video duration for size estimation
            duration = info.get('duration', 0)
            
            # Get available formats
            if 'formats' in info:
                for f in info['formats']:
                    # Estimate file size if not provided
                    filesize = f.get('filesize') or f.get('filesize_approx')
                    
                    if not filesize and duration:
                        # Estimate based on bitrate
                        tbr = f.get('tbr')  # Total bitrate
                        vbr = f.get('vbr')  # Video bitrate
                        abr = f.get('abr')  # Audio bitrate
                        
                        if tbr:
                            # tbr is in kbps, duration is in seconds
                            filesize = int((tbr * 1000 / 8) * duration)
                        elif vbr and abr:
                            filesize = int(((vbr + abr) * 1000 / 8) * duration)
                        elif vbr:
                            filesize = int((vbr * 1000 / 8) * duration)
                        elif abr:
                            filesize = int((abr * 1000 / 8) * duration)
                    
                    # Combined formats (video + audio)
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('height'):
                        combined_formats.append({
                            'format_id': f['format_id'],
                            'ext': f.get('ext', 'mp4'),
                            'quality': f"{f.get('height')}p",
                            'type': 'combined',
                            'filesize': filesize or 0,
                            'has_audio': True
                        })
                    
                    # Video-only formats
                    elif f.get('vcodec') != 'none' and f.get('acodec') == 'none' and f.get('height'):
                        video_formats.append({
                            'format_id': f['format_id'],
                            'ext': f.get('ext', 'mp4'),
                            'quality': f"{f.get('height')}p",
                            'type': 'video',
                            'filesize': filesize or 0,
                            'has_audio': False
                        })
                    
                    # Audio-only formats
                    elif f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        abr = f.get('abr')
                        quality_str = f"{int(abr)}kbps" if abr else "unknown"
                        
                        audio_formats.append({
                            'format_id': f['format_id'],
                            'ext': f.get('ext', 'mp3'),
                            'quality': quality_str,
                            'type': 'audio',
                            'filesize': filesize or 0,
                            'has_audio': True
                        })
            
            # Find best audio format for merging
            best_audio = None
            best_audio_size = 0
            if audio_formats:
                # Sort by quality and pick the best
                try:
                    sorted_audio = sorted(audio_formats, 
                                        key=lambda x: int(x['quality'].replace('kbps', '')) if 'kbps' in x['quality'] else 0, 
                                        reverse=True)
                    best_audio = sorted_audio[0]['format_id']
                    best_audio_size = sorted_audio[0]['filesize']
                except:
                    best_audio = audio_formats[0]['format_id']
                    best_audio_size = audio_formats[0]['filesize']
            
            # Create final format list
            final_formats = []
            
            # Add combined formats first (these have audio already)
            for fmt in combined_formats:
                final_formats.append(fmt)
            
            # Add video formats with audio merging options
            if best_audio:
                for fmt in video_formats:
                    # Create merged format option
                    final_formats.append({
                        'format_id': f"{fmt['format_id']}+{best_audio}",
                        'ext': 'mp4',
                        'quality': fmt['quality'],
                        'type': 'merged',
                        'filesize': fmt['filesize'] + best_audio_size,  # Estimate combined size
                        'has_audio': True
                    })
            
            # Add audio-only formats
            for fmt in audio_formats:
                final_formats.append(fmt)
            
            # Remove duplicates by quality and type
            unique_formats = {}
            for fmt in final_formats:
                key = (fmt['quality'], fmt['type'])
                
                current_size = fmt['filesize'] or 0
                existing_size = unique_formats[key]['filesize'] if key in unique_formats else 0
                existing_size = existing_size or 0
                
                if key not in unique_formats or current_size > existing_size:
                    unique_formats[key] = fmt
            
            return list(unique_formats.values())
            
    except Exception as e:
        raise Exception(f"Could not fetch formats: {str(e)}")

def format_file_size(size_bytes):
    """Convert bytes to human readable format"""
    if not size_bytes or size_bytes == 0:
        return "Size unknown"
    
    try:
        size_bytes = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    except (ValueError, TypeError):
        return "Size unknown"

def format_number(num):
    """Format large numbers (e.g. view count)"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    if num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)

def download_video(url, format_id, output_path, progress_callback=None, audio_only=False, video_info=None):
    """Download video/audio with selected format, merging audio+video if needed"""
    
    def progress_hook(d):
        if progress_callback and d['status'] == 'downloading':
            try:
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                
                if total > 0:
                    percentage = int((downloaded / total) * 100)
                    speed = d.get('speed', 0)
                    progress_callback(percentage, downloaded, total, speed)
            except:
                pass
        elif progress_callback and d['status'] == 'finished':
            progress_callback(100, d.get('total_bytes', 0), d.get('total_bytes', 0), 0)
    
    # Audio extraction
    if audio_only:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'no_playlist': True,
            'progress_hooks': [progress_hook] if progress_callback else [],
            'fragment_retries': 10,
            'retries': 10,
            'ignoreerrors': 'only_download',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }
    # Check if format needs audio merging
    elif '+' not in format_id:
        # Single format - might need best audio
        ydl_opts = {
            'format': f'{format_id}+bestaudio/best',  # Try to merge with best audio
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'no_playlist': True,
            'merge_output_format': 'mp4',  # Ensure mp4 output
            'writesubtitles': True,
            'subtitleslangs': ['en'],
            'embedsubtitles': True,
            'progress_hooks': [progress_hook] if progress_callback else [],
            'fragment_retries': 10,
            'retries': 10,
            'ignoreerrors': 'only_download',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }, {
                'key': 'FFmpegEmbedSubtitle',
            }]
        }
    else:
        # Already a combined format
        ydl_opts = {
            'format': format_id,
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'no_playlist': True,
            'merge_output_format': 'mp4',
            'writesubtitles': True,
            'subtitleslangs': ['en'],
            'embedsubtitles': True,
            'progress_hooks': [progress_hook] if progress_callback else [],
            'fragment_retries': 10,
            'retries': 10,
            'ignoreerrors': 'only_download',
            'postprocessors': [{
                'key': 'FFmpegEmbedSubtitle',
            }]
        }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Get the downloaded file path
            if info:
                filename = ydl.prepare_filename(info)
                if audio_only:
                    # Change extension to mp3
                    filename = os.path.splitext(filename)[0] + '.mp3'
                
                # Add to history
                video_id = info.get('id', '')
                title = info.get('title', 'Unknown')
                filesize = info.get('filesize', 0) or info.get('filesize_approx', 0)
                format_str = 'MP3 Audio' if audio_only else format_id
                
                add_to_history(video_id, title, url, format_str, filesize, filename)
        
        return True
    except Exception as e:
        raise Exception(f"Download failed: {str(e)}")

def main():
    # Initialize database
    init_database()
    
    # Header
    st.markdown('<h1 class="main-header">YouTube Downloader</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Premium video downloads with playlist support & audio extraction</p>', unsafe_allow_html=True)
    
    # Check for ffmpeg
    try:
        import subprocess
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        st.warning("⚠️ FFmpeg not found. Some high-quality formats may not merge correctly. Please install FFmpeg.")

    # Check yt-dlp version
    try:
        import yt_dlp.version
        current_version = yt_dlp.version.__version__
        if not current_version.startswith('2025'):
             st.warning(f"⚠️ Your yt-dlp version ({current_version}) might be outdated. Please update it for best results.")
    except:
        pass
    
    # Initialize session state
    if 'video_info' not in st.session_state:
        st.session_state.video_info = None
    if 'formats' not in st.session_state:
        st.session_state.formats = []
    if 'current_url' not in st.session_state:
        st.session_state.current_url = ""
    if 'playlist_info' not in st.session_state:
        st.session_state.playlist_info = None
    if 'download_queue' not in st.session_state:
        st.session_state.download_queue = []
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📹 Single Video", "📋 Playlist", "📜 History"])
    
    # Tab 1: Single Video Download
    with tab1:
        with st.container():
            # URL Input Section
            col1, col2 = st.columns([3, 1])
            with col1:
                url_input = st.text_input(
                    "Video URL",
                    placeholder="Paste YouTube link here...",
                    label_visibility="collapsed",
                    key="url_input"
                )
            
            with col2:
                check_btn = st.button("Get Info", key="get_info_btn", use_container_width=True)

            # Settings
            with st.expander("⚙️ Settings"):
                output_dir = st.text_input(
                    "Download Folder",
                    value="downloads",
                    key="output_dir"
                )
                audio_only = st.checkbox("🎵 Extract Audio Only (MP3)", key="audio_only")
                if output_dir:
                    Path(output_dir).mkdir(exist_ok=True)

            # Process URL
            if check_btn:
                if not url_input:
                    st.error("Please enter a YouTube URL")
                elif not validate_youtube_url(url_input):
                    st.error("Invalid YouTube URL format")
                else:
                    clean_video_url = clean_url(url_input)
                    
                    # Check if already downloaded
                    with st.spinner("Fetching video details..."):
                        try:
                            video_info = get_video_info(clean_video_url)
                            st.session_state.video_info = video_info
                            st.session_state.current_url = clean_video_url
                            
                            # Check history
                            video_id = clean_video_url.split('v=')[1].split('&')[0] if 'v=' in clean_video_url else ''
                            if is_downloaded(video_id):
                                st.info("ℹ️ This video has been downloaded before")
                            
                            formats = get_video_formats(clean_video_url)
                            st.session_state.formats = formats
                            
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                            st.session_state.video_info = None
            
            # Video Info Display
            if st.session_state.video_info:
                st.markdown('<div class="video-card">', unsafe_allow_html=True)
                
                col_img, col_details = st.columns([1, 2])
                
                with col_img:
                    if st.session_state.video_info.get('thumbnail'):
                        st.image(st.session_state.video_info['thumbnail'], use_container_width=True)
                
                with col_details:
                    st.markdown(f"### {st.session_state.video_info['title']}")
                    
                    meta_col1, meta_col2, meta_col3 = st.columns(3)
                    with meta_col1:
                        st.markdown('<p class="info-label">Channel</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="info-value">{st.session_state.video_info["uploader"]}</p>', unsafe_allow_html=True)
                    
                    with meta_col2:
                        duration = st.session_state.video_info['duration']
                        mins, secs = divmod(duration, 60)
                        st.markdown('<p class="info-label">Duration</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="info-value">{int(mins)}:{int(secs):02d}</p>', unsafe_allow_html=True)
                        
                    with meta_col3:
                        views = st.session_state.video_info.get('view_count', 0)
                        st.markdown('<p class="info-label">Views</p>', unsafe_allow_html=True)
                        st.markdown(f'<p class="info-value">{format_number(views)}</p>', unsafe_allow_html=True)

                st.markdown("---")
                
                # Format Selection (only if not audio only)
                if not st.session_state.get('audio_only', False):
                    if st.session_state.formats:
                        combined_formats = [f for f in st.session_state.formats if f['type'] == 'combined']
                        merged_formats = [f for f in st.session_state.formats if f['type'] == 'merged']
                        video_formats = [f for f in st.session_state.formats if f['type'] == 'video']
                        audio_formats = [f for f in st.session_state.formats if f['type'] == 'audio']
                        
                        format_options = []
                        
                        def add_formats(formats, label_prefix, sort_key):
                            try:
                                sorted_fmts = sorted(formats, key=sort_key, reverse=True)
                            except:
                                sorted_fmts = formats
                            
                            for fmt in sorted_fmts:
                                size = format_file_size(fmt['filesize'])
                                format_options.append({
                                    'label': f"{label_prefix} {fmt['quality']} | {fmt['ext']} | {size}",
                                    'format_id': fmt['format_id']
                                })

                        add_formats(combined_formats, "🎬 Standard", lambda x: int(x['quality'].replace('p', '')) if x['quality'].replace('p', '').isdigit() else 0)
                        add_formats(merged_formats, "✨ High Quality", lambda x: int(x['quality'].replace('p', '')) if x['quality'].replace('p', '').isdigit() else 0)
                        add_formats(video_formats, "📹 Video Only", lambda x: int(x['quality'].replace('p', '')) if x['quality'].replace('p', '').isdigit() else 0)
                        add_formats(audio_formats, "🎵 Audio Only", lambda x: x['quality'])
                        
                        if format_options:
                            selected_idx = st.selectbox(
                                "Select Quality",
                                options=range(len(format_options)),
                                format_func=lambda x: format_options[x]['label']
                            )
                            selected_fmt_id = format_options[selected_idx]['format_id']
                        else:
                            st.warning("No formats available")
                            selected_fmt_id = None
                    else:
                        selected_fmt_id = None
                else:
                    st.info("🎵 Audio extraction mode - will download best audio quality as MP3")
                    selected_fmt_id = None
                
                # Download button
                if st.button("Download Now", key="dl_btn"):
                    if not output_dir:
                        st.error("Please set a download folder in settings")
                    else:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        def update_progress(percentage, downloaded, total, speed):
                            progress_bar.progress(percentage)
                            speed_mb = speed / (1024 * 1024) if speed else 0
                            status_text.markdown(f"`{percentage}%` | `{format_file_size(downloaded)}` / `{format_file_size(total)}` | `{speed_mb:.1f} MB/s`")
                        
                        try:
                            with st.spinner("Downloading..."):
                                success = download_video(
                                    st.session_state.current_url,
                                    selected_fmt_id if selected_fmt_id else 'best',
                                    output_dir,
                                    update_progress,
                                    audio_only=st.session_state.get('audio_only', False)
                                )
                            
                            if success:
                                st.balloons()
                                st.success(f"✅ Downloaded to {output_dir}")
                        except Exception as e:
                            st.error(f"Download failed: {str(e)}")
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Tab 2: Playlist Download
    with tab2:
        st.markdown("### 📋 Playlist Downloader")
        
        playlist_url = st.text_input(
            "Playlist URL",
            placeholder="Paste YouTube playlist link here...",
            key="playlist_url"
        )
        
        if st.button("Load Playlist", key="load_playlist_btn"):
            if playlist_url and 'list=' in playlist_url:
                with st.spinner("Loading playlist..."):
                    try:
                        playlist_info = get_playlist_info(playlist_url)
                        st.session_state.playlist_info = playlist_info
                        st.success(f"✅ Loaded playlist: {playlist_info['title']} ({playlist_info['video_count']} videos)")
                    except Exception as e:
                        st.error(f"Error loading playlist: {str(e)}")
            else:
                st.error("Please enter a valid playlist URL")
        
        if st.session_state.playlist_info:
            st.markdown(f"**{st.session_state.playlist_info['title']}**")
            st.markdown(f"By: {st.session_state.playlist_info['uploader']} | Videos: {st.session_state.playlist_info['video_count']}")
            
            st.info("🚧 Playlist batch download feature coming soon! For now, copy individual video URLs to download them in the Single Video tab.")
    
    # Tab 3: Download History
    with tab3:
        st.markdown("### 📜 Download History")
        
        history = get_history(limit=50)
        
        if history:
            st.markdown(f"**Total Downloads: {len(history)}**")
            
            for idx, (video_id, title, url, format_str, filesize, download_date, file_path) in enumerate(history):
                with st.expander(f"{idx+1}. {title}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Format:** {format_str}")
                        st.markdown(f"**Size:** {format_file_size(filesize)}")
                    with col2:
                        st.markdown(f"**Downloaded:** {download_date}")
                        st.markdown(f"**Path:** `{file_path}`")
                    
                    if st.button("Open URL", key=f"open_{idx}"):
                        st.markdown(f"[{url}]({url})")
        else:
            st.info("No download history yet. Start downloading videos to see them here!")

    # Footer
    st.markdown('<div class="footer">Built with Streamlit & yt-dlp</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
