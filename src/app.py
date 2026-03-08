import streamlit as st
from downloader import fetch_formats, download_video, fetch_english_subtitles, download_english_subtitle
from utils import validate_youtube_link, format_bytes

# ------------------------------
# Session State Initialization
# ------------------------------
if "formats" not in st.session_state:
    st.session_state.formats = None
if "video_info" not in st.session_state:
    st.session_state.video_info = None
if "subtitles_available" not in st.session_state:
    st.session_state.subtitles_available = None

st.set_page_config(layout="centered", page_title="YouTube Video Downloader")


def main():
    st.title("🎬 YouTube Video Downloader")
    st.write("Download videos, audio, and English subtitles.")

    video_url = st.text_input("Enter YouTube Video URL:")

    # ==============================
    # FETCH FORMATS BUTTON
    # ==============================
    if st.button("Fetch Formats"):
        # Reset state when a new URL is fetched
        st.session_state.formats = None
        st.session_state.video_info = None
        st.session_state.subtitles_available = None

        if validate_youtube_link(video_url):
            try:
                with st.spinner("Fetching video information..."):
                    # This call is wrapped in robust error handling
                    info, formats = fetch_formats(video_url)

                if formats:
                    st.session_state.formats = formats
                    st.session_state.video_info = info
                    
                    # CHECK SUBTITLES ONCE AND STORE THE RESULT
                    with st.spinner("Checking for English subtitles..."):
                        st.session_state.subtitles_available = fetch_english_subtitles(video_url)
                        
                    st.success("Video information loaded successfully!")
                else:
                    st.error("No downloadable formats found for this video.")

            except Exception as e:
                # Catch general errors during fetching (e.g., network, private video)
                st.error(f"Failed to fetch video information. It might be private, age-restricted, or deleted. Error: {e}")
                st.session_state.formats = None
                st.session_state.video_info = None
        else:
            st.error("Invalid YouTube URL. Please check and try again.")

    # Stop and wait if no formats yet
    if st.session_state.formats is None:
        return

    # ==============================
    # VIDEO PREVIEW
    # ==============================
    info = st.session_state.video_info

    st.subheader("📌 Video Information")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(info["thumbnail"], width=220)
    with col2:
        st.write(f"**Title:** {info['title']}")
        st.write(f"**Duration:** {info['duration']}")
        st.write(f"**Uploader:** {info.get('uploader', 'Unknown')}")
        st.write(f"**Views:** {info.get('view_count', 0):,}")

    st.divider()

    # ==============================
    # FORMAT SELECTION
    # ==============================
    st.subheader("🎥 Select Format to Download")

    # Use the new 'display_size' key which contains filesize or filesize_approx
    format_options = [
        f"{f['format_note']} | {f['ext']} | {f['resolution']} | {format_bytes(f.get('display_size'))}"
        for f in st.session_state.formats
    ]

    selected_format = st.selectbox("Available Formats", format_options, key="format_select")

    # ==============================
    # DOWNLOAD VIDEO BUTTON
    # ==============================
    if st.button("Download Video"):
        fmt = st.session_state.formats[format_options.index(selected_format)]
        try:
            with st.spinner("Downloading..."):
                filename = download_video(video_url, fmt) 

            if filename:
                st.success(f"Downloaded successfully: **{filename}**")
                st.balloons()
            else:
                st.error("Download failed. Check the console for details or try another format.")

        except Exception as e:
            st.error(f"An error occurred during download: {e}")

    st.divider()

    # ==============================
    # ENGLISH SUBTITLES ONLY
    # ==============================
    st.subheader("📝 English Subtitles")

    # Use the subtitle availability status stored in session state
    if st.session_state.subtitles_available:
        st.success("English subtitles available.")

        if st.button("Download English Subtitles"):
            try:
                with st.spinner("Downloading English subtitles..."):
                    subtitle_file = download_english_subtitle(video_url)

                st.success(f"Subtitle downloaded: **{subtitle_file}**")
            except Exception as e:
                 st.error(f"Failed to download subtitles: {e}")
    elif st.session_state.subtitles_available is False:
        st.info("❌ This video does NOT have English subtitles.")
    else:
         # Only show if fetching failed to run (i.e., video info itself failed)
         st.info("Subtitle availability check pending or failed.")


if __name__ == "__main__":
    main()