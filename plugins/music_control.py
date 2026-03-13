import os
import asyncio
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import Dict, Any
from .base_plugin import SmartPlugin

# === ТВОЇ КЛЮЧІ SPOTIFY API ===
SPOTIFY_CLIENT_ID = "055bc51121ca4c29a06558a26acb46f9"
SPOTIFY_CLIENT_SECRET = "8d0cf0e380eb4ec4b873aba2261b2556"
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8080"
# ==============================
# ==============================

class MusicControlPlugin(SmartPlugin):
    """Плагін для управління музикою через офіційний Spotify API. (все що пов'язано з відтворенням, паузою, перемиканням треків, пошуком музики)"""

    def __init__(self):
        super().__init__()
        self.sp = None
        self._init_spotify()

    def _init_spotify(self):
        try:
            scope = "user-modify-playback-state user-read-playback-state"
            auth_manager = SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope=scope,
                open_browser=False
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
        except Exception as e:
            self.log_error(f"Failed to initialize Spotify API: {e}")

    @property
    def name(self) -> str:
        return "music_control"

    @property
    def description(self) -> str:
        return "Пряме управління Spotify. ЗАВЖДИ використовуй цей плагін для команд: включи музику, включи пісню, включи виконавця, включи трек, увімкни Spotify, пауза музики, наступний трек, попередній трек, відтворення музики."
    
    @property
    def commands(self) -> Dict[str, str]:
        return {
            "play_music": "включити конкретний трек або пісню",
            "play_playlist": "включити плейлист за назвою",
            "search_artist": "включити музику конкретного виконавця",
            "play_genre": "включити музику певного жанру (через плейлисти)",
            "pause_music": "поставити на паузу або відновити",
            "next_track": "увімкнути наступний трек",
            "prev_track": "увімкнути попередній трек",
            "open_spotify": "просто відкрити додаток Spotify"
        }

    async def _get_target_device_id(self):
        """Знаходить ID потрібного пристрою (ПК) для відтворення музики."""
        try:
            resp = self.sp.devices()
            devices = resp.get('devices', []) if resp else []
            
            # Якщо список порожній, запускаємо додаток і чекаємо
            if not devices:
                print("[SPOTIFY API] Немає пристроїв у мережі. Запускаю додаток Spotify...")
                os.startfile("spotify:")
                await asyncio.sleep(7.0)  # Даємо 7 секунд на повне завантаження і синхронізацію з API
                
                resp = self.sp.devices()
                devices = resp.get('devices', []) if resp else []
                
            if not devices:
                return None

            # 1. Пріоритет: пристрій, який вже відтворює музику
            for d in devices:
                if d.get('is_active'):
                    return d.get('id')
                    
            # 2. Пріоритет: будь-який комп'ютер
            for d in devices:
                if d.get('type', '').lower() == 'computer':
                    return d.get('id')
                    
            # 3. Якщо комп'ютера немає, беремо перший у списку
            if devices:
                return devices[0].get('id')
            return None
            
        except Exception as e:
            print(f"[SPOTIFY API] Помилка отримання пристроїв: {e}")
            return None

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        """Виконує команду плагіна через API."""
        if not self.sp:
            self._init_spotify()
            if not self.sp:
                return {"success": False, "result": None, "message": "Spotify API не налаштовано"}

        try:
            print(f"\n=== SPOTIFY API DEBUG ===")
            print(f"[1] Command: {command_name} | Args: {kwargs}")

            target_device_id = None
            playback_commands = ["play_music", "play_playlist", "search_artist", "play_genre", "pause_music", "next_track", "prev_track"]
            
            # Отримуємо ID пристрою
            if command_name in playback_commands:
                target_device_id = await self._get_target_device_id()
                if not target_device_id and command_name != "pause_music":
                     return {"success": False, "result": None, "message": "Spotify не знайдено. Відкрий його вручну і зачекай пару секунд."}

            # --- БРОНЕБІЙНИЙ РОЗБІР ВІДПОВІДЕЙ ---
            if command_name == "play_music":
                query = kwargs.get("value") or kwargs.get("track", "")
                result = self.sp.search(q=query, type='track', limit=1)
                
                # Безпечне витягування даних
                items = result.get('tracks', {}).get('items', []) if result else []
                
                if items and items[0]:
                    track_uri = items[0].get('uri')
                    track_name = items[0].get('name', 'Unknown')
                    artist_name = items[0].get('artists', [{}])[0].get('name', 'Unknown')
                    
                    self.sp.start_playback(device_id=target_device_id, uris=[track_uri])
                    return {"success": True, "result": None, "message": f"Вмикаю: {artist_name} - {track_name}"}
                return {"success": False, "result": None, "message": f"Трек '{query}' не знайдено"}

            elif command_name in ["play_playlist", "play_genre"]:
                query = kwargs.get("value") or kwargs.get("playlist") or kwargs.get("genre", "")
                result = self.sp.search(q=query, type='playlist', limit=1)
                
                items = result.get('playlists', {}).get('items', []) if result else []
                
                if items and items[0]:
                    playlist_uri = items[0].get('uri')
                    playlist_name = items[0].get('name', 'Unknown')
                    
                    self.sp.start_playback(device_id=target_device_id, context_uri=playlist_uri)
                    return {"success": True, "result": None, "message": f"Вмикаю плейлист: {playlist_name}"}
                return {"success": False, "result": None, "message": f"Плейлист '{query}' не знайдено"}

            elif command_name == "search_artist":
                query = kwargs.get("value") or kwargs.get("artist", "")
                result = self.sp.search(q=query, type='artist', limit=1)
                
                items = result.get('artists', {}).get('items', []) if result else []
                
                if items and items[0]:
                    artist_uri = items[0].get('uri')
                    artist_name = items[0].get('name', 'Unknown')
                    
                    self.sp.start_playback(device_id=target_device_id, context_uri=artist_uri)
                    return {"success": True, "result": None, "message": f"Вмикаю виконавця: {artist_name}"}
                return {"success": False, "result": None, "message": f"Виконавця '{query}' не знайдено"}

            elif command_name == "pause_music":
                playback = self.sp.current_playback()
                # Безпечна перевірка статусу
                if playback and playback.get('is_playing'):
                    self.sp.pause_playback(device_id=target_device_id)
                    return {"success": True, "result": None, "message": "Музику зупинено"}
                elif target_device_id:
                    self.sp.start_playback(device_id=target_device_id)
                    return {"success": True, "result": None, "message": "Відтворення відновлено"}
                return {"success": False, "result": None, "message": "Немає активних пристроїв"}

            elif command_name == "next_track":
                self.sp.next_track(device_id=target_device_id)
                return {"success": True, "result": None, "message": "Перемкнуто на наступний трек"}
                
            elif command_name == "prev_track":
                self.sp.previous_track(device_id=target_device_id)
                return {"success": True, "result": None, "message": "Перемкнуто на попередній трек"}

            elif command_name == "open_spotify":
                os.startfile("spotify:")
                return {"success": True, "result": None, "message": "Відкриваю Spotify"}

        except spotipy.exceptions.SpotifyException as e:
            # ЦЕЙ PRINT ПОКАЖЕ ТОЧНУ ПРИЧИНУ
            print(f"\n[🔴 CRITICAL SPOTIFY ERROR] Код: {e.http_status}, Повідомлення: {e.msg}")
            self.log_error(f"Spotify API Error: {e}")
            if e.http_status == 403 or "PREMIUM_REQUIRED" in str(e):
                 return {"success": False, "result": None, "message": "Для керування відтворенням потрібен Spotify Premium"}
            return {"success": False, "result": None, "message": f"Помилка доступу до Spotify: {e.msg}"}
        except Exception as e:
            print(f"\n[🔴 UNEXPECTED ERROR] {str(e)}")
            self.log_error(f"Unexpected Spotify API Error: {e}")
            return {"success": False, "result": None, "message": f"Внутрішня помилка: {str(e)}"}

        return {"success": False, "result": None, "message": f"Невідома команда: {command_name}"}