# YouTube Downloader App

This project is a Streamlit application that allows users to download YouTube videos in various formats, including audio formats. The application provides an interactive interface to display available formats and tracks download progress using TQDM.

## Features

- Download YouTube videos in different formats (video and audio).
- Interactive user interface built with Streamlit.
- Display available formats for selected videos.
- Track download progress with TQDM.

## Project Structure

```
youtube-downloader-app
├── src
│   ├── app.py          # Main entry point of the Streamlit application
│   ├── downloader.py   # Logic for downloading YouTube videos
│   └── utils.py        # Utility functions for the application
├── requirements.txt     # List of dependencies
└── README.md            # Project documentation
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd youtube-downloader-app
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the Streamlit application:
   ```
   streamlit run src/app.py
   ```

2. Open your web browser and navigate to `http://localhost:8501`.

3. Enter the YouTube video link in the provided input field.

4. Select the desired format from the available options.

5. Click the download button to start downloading the video.

## Dependencies

- Streamlit
- Pytube
- TQDM

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.