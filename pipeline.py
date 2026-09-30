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
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_to_history(track_name):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{track_name}\n")

def get_playlist_tracks(yt, playlist_id):
    playlist = yt.get_playlist(playlist_id, limit=None)
    tracks = []
    for item in playlist.get('tracks', []):
        title = item.get('title')
        artist = item['artists'][0]['name'] if item.get('artists') else ''
        if title:
            tracks.append(f"{title} {artist}".strip())
    return tracks

def send_to_telegram(file_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    with open(file_path, "rb") as doc:
        response = requests.post(
            url,
            data={"chat_id": CHAT_ID, "caption": caption},
            files={"document": doc}
        )
    return response.json()

def main():
    if not BOT_TOKEN or not CHAT_ID:
        print("Error: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in GitHub Secrets.")
        return

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
            os.system(f'spotiflac "{track}" --output-path "{TEMP_DIR}"')

            flac_files = glob.glob(f"{TEMP_DIR}/*.flac")
            if not flac_files:
                print(f"Failed to download audio for: {track}")
                continue

            for flac_file in flac_files:
                print(f"Uploading {flac_file} to Telegram...")
                res = send_to_telegram(flac_file, f"🎵 {track}")
                
                if res.get('ok'):
                    print("Upload successful!")
                    save_to_history(track)
                    uploaded_tracks.add(track)
                else:
                    print(f"Telegram upload failed: {res}")
                
                os.remove(flac_file)

if __name__ == "__main__":
    main()
