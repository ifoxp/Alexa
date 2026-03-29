import os
import asyncio
import spotipy
# 1. ЗМІНА: Імпортуємо SpotifyPKCE замість SpotifyOAuth
from spotipy.oauth2 import SpotifyPKCE 
from typing import Dict, Any
from .base_plugin import SmartPlugin

# === ТВОЇ КЛЮЧІ SPOTIFY API ===
SPOTIFY_CLIENT_ID = "055bc51121ca4c29a06558a26acb46f9"
# 2. ЗМІНА: SPOTIFY_CLIENT_SECRET повністю видалено! Він більше не потрібен.
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:8080"
# ==============================

class MusicControlPlugin(SmartPlugin):
    """Плагін для управління музикою (відтворення треків, виконавців, плейлистів та рекомендацій)."""

    def __init__(self):
        super().__init__()
        self.sp = None
        self._init_spotify()

    def _init_spotify(self):
        try:
            import sys as _sys
            if hasattr(_sys, '_MEIPASS'):
                _cache_dir = os.path.dirname(_sys.executable)
            else:
                _cache_dir = os.path.dirname(os.path.dirname(__file__))
            _cache_path = os.path.join(_cache_dir, '.spotify_cache')

            scope = "user-modify-playback-state user-read-playback-state user-top-read"
            
            # 3. ЗМІНА: Використовуємо SpotifyPKCE. Сюди передається тільки client_id.
            auth_manager = SpotifyPKCE(
                client_id=SPOTIFY_CLIENT_ID,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope=scope,
                cache_path=_cache_path,
                open_browser=True
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            
            current_user = self.sp.me()
            print(f"[SPOTIFY] Успішно підключено (PKCE)! Користувач: {current_user.get('display_name')}")

        except Exception as e:
            print(f"[ERROR] Помилка ініціалізації Spotify API: {e}")
            self.sp = None

    @property
    def name(self) -> str:
        return "music_control"

    @property
    def description(self) -> str:
        return "Управління Spotify. Використовуй цей плагін, коли користувач просить увімкнути музику, пісню, плейлист, жанр або виконавця."
    
    @property
    def commands(self) -> Dict[str, str]:
        # Залишили тільки найважливіше + додали рекомендації
        return {
            "play_track": "Увімкнути конкретний трек/пісню. Використовуй, якщо відома точна назва треку.",
            "play_artist": "Увімкнути музику виконавця/гурту (наприклад: Imagine Dragons, Rammstein).",
            "play_playlist": "Увімкнути плейлист за його точною назвою.",
            "play_genre": "Увімкнути музику певного жанру (поп, рок, фон тощо).",
            "play_recommended": "Увімкнути персоналізовану музику. Використовуй для загальних фраз: 'включи музику', 'щось на мій смак', 'увімкни щось класне'."
        }

    async def _get_target_device_id(self):
        """Знаходить ID потрібного пристрою (ПК) для відтворення музики."""
        try:
            resp = self.sp.devices()
            devices = resp.get('devices', []) if resp else []
            
            if not devices:
                print("[SPOTIFY API] Немає пристроїв у мережі. Запускаю додаток Spotify...")
                os.startfile("spotify:")
                for _ in range(15):
                    await asyncio.sleep(1.0)
                    resp = self.sp.devices()
                    devices = resp.get('devices', []) if resp else []
                    if devices:
                        print(f"[SPOTIFY API] Пристрій з'явився через {_ + 1} сек")
                        break
                
            if not devices: return None

            for d in devices:
                if d.get('is_active'): return d.get('id')
            for d in devices:
                if d.get('type', '').lower() == 'computer': return d.get('id')
            if devices: return devices[0].get('id')
            return None
            
        except Exception as e:
            print(f"[SPOTIFY API] Помилка отримання пристроїв: {e}")
            return None

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        if not self.sp:
            self._init_spotify()
            if not self.sp:
                return {"success": False, "result": None, "message": "Spotify API не налаштовано"}

        try:
            print(f"\n=== SPOTIFY API DEBUG ===")
            print(f"[1] Command: {command_name} | Args: {kwargs}")

            # Для всіх цих 5 команд нам потрібен пристрій
            target_device_id = await self._get_target_device_id()
            if not target_device_id:
                 return {"success": False, "result": None, "message": "Spotify не знайдено. Відкрий його вручну і зачекай пару секунд."}

            # Gemini передає параметр у поле "value"
            query = kwargs.get("value", "")

            # --- РОЗБІР КОМАНД ---
            if command_name == "play_track":
                result = self.sp.search(q=query, type='track', limit=1)
                items = result.get('tracks', {}).get('items', []) if result else []
                if items:
                    self.sp.start_playback(device_id=target_device_id, uris=[items[0].get('uri')])
                    return {"success": True, "result": None, "message": f"Вмикаю трек: {items[0].get('name')}"}
                return {"success": False, "result": None, "message": f"Трек '{query}' не знайдено"}

            elif command_name == "play_artist":
                result = self.sp.search(q=query, type='artist', limit=1)
                items = result.get('artists', {}).get('items', []) if result else []
                if items:
                    self.sp.start_playback(device_id=target_device_id, context_uri=items[0].get('uri'))
                    return {"success": True, "result": None, "message": f"Вмикаю виконавця: {items[0].get('name')}"}
                return {"success": False, "result": None, "message": f"Виконавця '{query}' не знайдено"}

            elif command_name in ["play_playlist", "play_genre"]:
                result = self.sp.search(q=query, type='playlist', limit=1)
                items = result.get('playlists', {}).get('items', []) if result else []
                if items:
                    self.sp.start_playback(device_id=target_device_id, context_uri=items[0].get('uri'))
                    return {"success": True, "result": None, "message": f"Вмикаю плейлист: {items[0].get('name')}"}
                return {"success": False, "result": None, "message": f"Плейлист '{query}' не знайдено"}

            elif command_name == "play_recommended":
                # Оскільки Spotify закрив API рекомендацій (повертає 404), ми робимо свій мікс!
                # 1. Беремо до 50 найулюбленіших треків користувача за останній місяць
                top_tracks = self.sp.current_user_top_tracks(limit=50, time_range='short_term')
                track_uris = [t['uri'] for t in top_tracks.get('items', [])]

                if track_uris:
                    import random
                    # 2. Перемішуємо твої улюблені треки, щоб порядок завжди був різним
                    random.shuffle(track_uris) 
                    
                    # 3. Запускаємо 20 випадкових треків з твоїх улюблених
                    self.sp.start_playback(device_id=target_device_id, uris=track_uris[:20])
                    return {"success": True, "result": None, "message": "Вмикаю мікс із твоїх улюблених пісень"}
                else:
                    # Fallback: якщо історія прослуховувань порожня, шукаємо глобальний плейлист
                    result = self.sp.search(q="Top 50 Global", type='playlist', limit=1)
                    items = result.get('playlists', {}).get('items', []) if result else []
                    if items:
                        self.sp.start_playback(device_id=target_device_id, context_uri=items[0].get('uri'))
                        return {"success": True, "result": None, "message": "Вмикаю популярні хіти"}

                return {"success": False, "result": None, "message": "Не вдалося згенерувати плейлист"}

        except spotipy.exceptions.SpotifyException as e:
            print(f"\n[🔴 CRITICAL SPOTIFY ERROR] Код: {e.http_status}, Повідомлення: {e.msg}")
            if e.http_status == 403 or "PREMIUM_REQUIRED" in str(e):
                 return {"success": False, "result": None, "message": "Для керування відтворенням потрібен Spotify Premium"}
            return {"success": False, "result": None, "message": f"Помилка доступу до Spotify: {e.msg}"}
        except Exception as e:
            print(f"\n[🔴 UNEXPECTED ERROR] {str(e)}")
            return {"success": False, "result": None, "message": f"Внутрішня помилка: {str(e)}"}

        return {"success": False, "result": None, "message": f"Невідома команда: {command_name}"}