import streamlit as st
import requests
import os
from urllib.parse import urlencode
from base64 import b64encode
from dotenv import load_dotenv


load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URL = os.getenv("SPOTIFY_REDIRECT_URL", "http://localhost:8501/")
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000/chat")

if not CLIENT_ID or not CLIENT_SECRET:
    st.error("❌ Missing Spotify CLIENT_ID or CLIENT_SECRET in .env file")
    st.stop()



st.set_page_config(page_title="Spotify + Music Chatbot", page_icon="🎵")
st.title(" Music Chatbot & Spotify Recommender")

def get_spotify_auth_url():
    scope = "user-top-read"
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URL,
        "scope": scope
    }
    return f"https://accounts.spotify.com/authorize?{urlencode(params)}"

def get_token(code):
    url = "https://accounts.spotify.com/api/token"
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth = b64encode(auth_str.encode()).decode()
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URL
    }
    headers = {"Authorization": f"Basic {b64_auth}"}
    resp = requests.post(url, data=data, headers=headers)
    st.write("DEBUG TOKEN RESPONSE:", resp.text)
    return resp.json().get("access_token")

def get_recommendations(token, mood=None):
    headers = {"Authorization": f"Bearer {token}"}

    # Категории поиска по mood
    mood_queries = {
        "Happy": "k-pop upbeat",
        "Chill": "k-pop chill",
        "Workout": "k-pop workout"
    }

    query = mood_queries.get(mood, "k-pop")

    # 1) Ищем плейлисты по запросу
    search_url = f"https://api.spotify.com/v1/search?q={query}&type=playlist&limit=5"
    resp_search = requests.get(search_url, headers=headers)

    if resp_search.status_code != 200:
        st.error("⚠ Failed to load playlists.")
        st.write("DEBUG SEARCH ERROR:", resp_search.text)
        return []

    playlists = resp_search.json().get("playlists", {}).get("items", [])
    if not playlists:
        st.error("⚠ No playlists found.")
        return []

    tracks = []

    # 2) Извлекаем треки из найденных плейлистов
    for pl in playlists:
        if not pl or not isinstance(pl, dict):
            continue

        pl_id = pl.get("id")
        if not pl_id:
            continue

        playlist_url = f"https://api.spotify.com/v1/playlists/{pl_id}/tracks"
        resp_tracks = requests.get(playlist_url, headers=headers)

        if resp_tracks.status_code != 200:
            continue

        items = resp_tracks.json().get("items", [])
        for item in items:
            track = item.get("track")
            if track and track.get("id"):
                tracks.append(track)

        if len(tracks) >= 20:
            break

    # 3) Возвращаем первые 10 треков (без audio_features)
    return tracks[:10]



st.subheader("💬 Chat with Music Bot")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.text_input("Ask about music, professors, or support:")

if st.button("Send") and user_input:
    # Сохраняем сообщение пользователя
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Отправляем запрос на FastAPI сервер
    try:
        resp = requests.post(FASTAPI_URL, json={"message": user_input})
        bot_reply = resp.json().get("message", "Error: no reply")
    except Exception as e:
        bot_reply = f"Error connecting to server: {e}"

    # Сохраняем ответ бота
    st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})

# Отображаем историю чата
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f"**🧑‍🎤 You:** {msg['content']}")
    else:
        st.markdown(f"**🤖 Bot:** {msg['content']}")

st.divider()

# --- Получение параметров из URL ---
code = st.query_params.get("code", None)

if "spotify_token" not in st.session_state:
    st.session_state.spotify_token = None

if code and st.session_state.spotify_token is None:
    token = get_token(code)
    if token:
        st.session_state.spotify_token = token
        st.success("✅ Logged in successfully with Spotify!")
    else:
        st.error("❌ Failed to get access token from Spotify")

token = st.session_state.spotify_token

if token:
    mood = st.selectbox("🎭 Choose your mood", ["Happy", "Chill", "Workout", "None"])
    mood_param = None if mood == "None" else mood

    tracks = get_recommendations(token, mood=mood_param)
    st.subheader("🎵 Recommended Tracks:")
    
    for t in tracks:
        st.image(t["album"]["images"][0]["url"], width=60)
        st.markdown(f"[{t['name']} - {t['artists'][0]['name']}]({t['external_urls']['spotify']})")

else:
    st.info("🔒 Log in to Spotify to get personalized recommendations.")
    st.markdown(f"[🎵 Login with Spotify]({get_spotify_auth_url()})")
