import os
import glob
import requests
from ytmusicapi import YTMusic

BOT_TOKEN = os.getenv("8706624042:AAGSl7uXl0SRYjxvKtjiGyjpGKCEHdHukKU")
CHAT_ID = os.getenv("-1004493781803")
PLAYLIST_ID = "PL4aK2Af8j6hp1xthQIcomzn1wU1pMRAOF"
TEMP_DIR = "/tmp/music"

def get_playlist_tracks(playlist_id):
    yt = YTMusic()
    playlist = yt.get_playlist(playlist_id)
    tracks = []
    for item in playlist.get('tracks', []):
        title = item.get('title')
        artist = item['artists'][0]['name'] if item.get('artists') else ''
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
    tracks = get_playlist_tracks(PLAYLIST_ID)
    print(f"Found {len(tracks)} tracks in playlist.")

    for idx, track in enumerate(tracks, start=1):
        print(f"[{idx}/{len(tracks)}] Processing track: {track}")
        os.system(f'spotiflac download --query "{track}" --output "{TEMP_DIR}"')

        for flac_file in glob.glob(f"{TEMP_DIR}/*.flac"):
            print(f"Uploading {flac_file} to Telegram...")
            res = send_to_telegram(flac_file, f"🎵 {track}")
            print(f"Telegram response: {res.get('ok')}")
            os.remove(flac_file)

if __name__ == "__main__":
    main()
