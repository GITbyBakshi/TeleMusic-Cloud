import os
import glob
import requests
from ytmusicapi import YTMusic

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
HISTORY_FILE = "uploaded_tracks.txt"
TEMP_DIR = "/tmp/music"

# Add all your YouTube Music playlist IDs here
PLAYLIST_IDS = [
    "PL4aK2Af8j6hp1xthQIcomzn1wU1pMRAOF",
    "PL4aK2Af8j6hp0S1zJEpAdjbvQPg_Mmqhm",
    "PL4aK2Af8j6hrXfTckj4AnEuXdtHk46BuR",
    "PL4aK2Af8j6hr6sbbrns0m1EMpiVGAD2_2",
    "PLR7rAjg3oCcw"
]


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def save_history(track_name):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{track_name}\n")


def send_to_telegram(file_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"
    with open(file_path, "rb") as audio:
        payload = {"chat_id": CHAT_ID, "caption": caption}
        files = {"audio": audio}
        res = requests.post(url, data=payload, files=files)
        return res.status_code == 200


def get_playlist_tracks(yt, playlist_id):
    try:
        playlist = yt.get_playlist(playlist_id, limit=None)
        tracks = []
        for item in playlist.get("tracks", []):
            title = item.get("title")
            artists = ", ".join([a["name"] for a in item.get("artists", [])])
            if title:
                tracks.append(f"{artists} - {title}" if artists else title)
        return tracks
    except Exception as e:
        print(f"Error fetching playlist {playlist_id}: {e}")
        return []


def clean_temp_dir():
    if os.path.exists(TEMP_DIR):
        for f in glob.glob(f"{TEMP_DIR}/*"):
            try:
                os.remove(f)
            except Exception:
                pass


clean_temp_dir()
os.makedirs(TEMP_DIR, exist_ok=True)
uploaded_tracks = load_history()
yt = YTMusic()

for p_idx, playlist_id in enumerate(PLAYLIST_IDS, start=1):
    print(f"\n--- Processing Playlist [{p_idx}/{len(PLAYLIST_IDS)}]: {playlist_id} ---")
    tracks = get_playlist_tracks(yt, playlist_id)
    print(f"Found {len(tracks)} total tracks in playlist.")

    for idx, track in enumerate(tracks, start=1):
        if track in uploaded_tracks:
            print(f"[{idx}/{len(tracks)}] Skipping (already uploaded): {track}")
            continue

        print(f"[{idx}/{len(tracks)}] Processing new track: {track}")

        # Write track query to a temporary CSV file for spotiflac
        csv_path = "/tmp/track.csv"
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(f'"{track}"\n')

        # Run spotiflac targeting Tidal in Hi-Res Lossless quality via CSV mode
        os.system(f'spotiflac --csv "{csv_path}" --output-path "{TEMP_DIR}" --service tidal --quality HI_RES_LOSSLESS')

        # Clean up temporary CSV file
        if os.path.exists(csv_path):
            os.remove(csv_path)

        # Locate downloaded audio file (.flac or .mp3)
        downloaded_files = glob.glob(f"{TEMP_DIR}/*.*")
        audio_files = [f for f in downloaded_files if f.lower().endswith(('.flac', '.mp3', '.m4a'))]

        if not audio_files:
            print(f"Failed to download audio for: {track}")
            continue

        for audio_file in audio_files:
            print(f"Uploading to Telegram: {audio_file}")
            success = send_to_telegram(audio_file, caption=f"🎵 {track}")
            if success:
                print(f"Successfully uploaded: {track}")
                uploaded_tracks.add(track)
                save_history(track)
            else:
                print(f"Failed to upload to Telegram: {track}")

        clean_temp_dir()
