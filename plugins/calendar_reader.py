import os
import json
import datetime
import asyncio
from typing import Dict, Any, List
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .base_plugin import SmartPlugin
import smart_ai
from audio_player import speak_text

# Дозволи: читання подій (і днів народжень, якщо вони є в календарі)
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

class CalendarPlugin(SmartPlugin):
    """Плагін для роботи з Google Календарем: щоденні брифінги та фонові нагадування."""

    def __init__(self):
        super().__init__()
        self.credentials_file = 'credentials.json'
        self.tokens_dir = 'calendar_tokens'
        self.state_file = '.calendar_state.json'
        
        self.services = []
        self.state = self._load_state()
        self._monitor_task = None
        
        # Створюємо папку для токенів (мультиакаунт)
        if not os.path.exists(self.tokens_dir):
            os.makedirs(self.tokens_dir)
            
        # ДОДАНО: Одразу завантажуємо токени при ініціалізації
        self._authenticate_all()

    @property
    def name(self) -> str:
        return "calendar_manager"

    @property
    def description(self) -> str:
        return "Керування розкладом. Використовуй для команд: 'додай новий календар', 'прочитай мій розклад', 'що у мене на сьогодні'."

    @property
    def commands(self) -> Dict[str, str]:
        return {
            "add_account": "Авторизувати ще один Google акаунт для читання календаря.",
            "read_schedule": "Примусово прочитати розклад на сьогодні (якщо користувач просить)."
        }

    # ==========================================
    # СИСТЕМА ПАМ'ЯТІ ТА СТАНУ
    # ==========================================
    def _load_state(self) -> dict:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"last_briefing_date": "", "reminded_events": []}

    def _save_state(self):
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=4)

    # ==========================================
    # АВТОРИЗАЦІЯ (МУЛЬТИАКАУНТ)
    # ==========================================
    def _authenticate_all(self):
        """Завантажує всі збережені акаунти та автоматично оновлює токени."""
        self.services = []
        if not os.path.exists(self.tokens_dir):
            return
            
        token_files = [f for f in os.listdir(self.tokens_dir) if f.endswith('.json')]
        
        for token_file in token_files:
            token_path = os.path.join(self.tokens_dir, token_file)
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
                
                # Якщо токен прострочився, але є ключ для оновлення (Refresh Token)
                if creds and creds.expired and creds.refresh_token:
                    from google.auth.transport.requests import Request
                    print(f"[CALENDAR] Оновлюю прострочений токен: {token_file}")
                    creds.refresh(Request())
                    # Зберігаємо свіжий токен назад у файл
                    with open(token_path, 'w') as f:
                        f.write(creds.to_json())
                
                if creds and creds.valid:
                    service = build('calendar', 'v3', credentials=creds)
                    self.services.append(service)
                    print(f"[CALENDAR] Успішно підключено акаунт з файлу {token_file}")
            except Exception as e:
                print(f"[CALENDAR ERROR] Не вдалося завантажити токен {token_file}: {e}")

    def _add_new_account(self) -> str:
        """Додає новий акаунт через браузер."""
        if not os.path.exists(self.credentials_file):
            return f"Помилка: файл {self.credentials_file} не знайдено."
            
        flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Зберігаємо новий токен з унікальним іменем
        token_name = f"token_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        token_path = os.path.join(self.tokens_dir, token_name)
        
        with open(token_path, 'w') as token_file:
            token_file.write(creds.to_json())
            
        self._authenticate_all() # Оновлюємо список сервісів
        return "Новий акаунт успішно підключено!"

    # ==========================================
    # ОТРИМАННЯ ДАНИХ З КАЛЕНДАРЯ
    # ==========================================
    def _get_events(self, days_ahead=1) -> List[dict]:
        """Збирає події з усіх підключених акаунтів."""
        if not self.services:
            self._authenticate_all()
            
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        future = (datetime.datetime.utcnow() + datetime.timedelta(days=days_ahead)).isoformat() + 'Z'
        
        all_events = []
        for service in self.services:
            try:
                events_result = service.events().list(
                    calendarId='primary', timeMin=now, timeMax=future,
                    singleEvents=True, orderBy='startTime'
                ).execute()
                all_events.extend(events_result.get('items', []))
            except Exception as e:
                print(f"[CALENDAR ERROR] Не вдалося прочитати події: {e}")
                
        # Сортуємо події з усіх акаунтів за часом
        all_events.sort(key=lambda x: x['start'].get('dateTime', x['start'].get('date')))
        return all_events

    # ==========================================
    # БРИФІНГ ТА ФОНОВИЙ МОНІТОРИНГ
    # ==========================================
    async def startup_routine(self):
        """Викликається при старті Jarvis. Робить брифінг і запускає таймери."""
        if not self.services:
            print("[CALENDAR] Немає підключених акаунтів. Скажіть 'додай новий календар'.")
            return

        today_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Якщо сьогодні ще не було брифінгу
        if self.state["last_briefing_date"] != today_str:
            print("[CALENDAR] Формую ранковий брифінг...")
            events = self._get_events(days_ahead=7) # Беремо на тиждень вперед для днів народжень
            
            today_events = []
            upcoming_birthdays = []
            
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                summary = event.get('summary', 'Без назви')
                event_id = event.get('id')
                
                # Перевіряємо, чи це подія на сьогодні
                if start.startswith(today_str):
                    # Відсікаємо вже минулі події
                    if 'T' in start:
                        event_time = datetime.datetime.fromisoformat(start)
                        if event_time.replace(tzinfo=None) < datetime.datetime.now():
                            continue
                    today_events.append(f"{summary} (початок о {start[11:16] if 'T' in start else 'весь день'})")
                
                # Шукаємо дні народження у найближчі 7 днів
                elif "день народження" in summary.lower() or "birthday" in summary.lower():
                    # Приклад: якщо у Нюти день народження (заплановано на 11 листопада), це потрапить сюди
                    date_obj = datetime.datetime.fromisoformat(start[:10])
                    upcoming_birthdays.append(f"{summary} буде {date_obj.strftime('%d.%m')}")

            # Формуємо текст для GPT
            prompt = f"Ти Jarvis. Склади дуже короткий ранковий брифінг. Події сьогодні: {today_events}. Дні народження найближчим часом: {upcoming_birthdays}. Скажи це красиво, українською мовою. Якщо подій немає, скажи, що день вільний."
            
            # Якщо є події або дні народження — озвучуємо
            if today_events or upcoming_birthdays:
                try:
                    briefing_text = await self.ask_gpt(prompt, max_tokens=150)
                    import config_manager as cfg
                    config = cfg.load_config() if hasattr(cfg, 'load_config') else {}
                    speak_text(briefing_text, config)
                except:
                    pass
            
            # Записуємо, що брифінг проведено
            self.state["last_briefing_date"] = today_str
            self.state["reminded_events"] = [] # Очищаємо нагадування на новий день
            self._save_state()

        # Запускаємо фоновий моніторинг (таймери за 5 хвилин)
        if not self._monitor_task:
            self._monitor_task = asyncio.create_task(self._background_monitor())

    async def _background_monitor(self):
        """Безкінечний цикл, який перевіряє події кожну хвилину."""
        print("[CALENDAR] Фоновий моніторинг запущено.")
        while True:
            try:
                events = self._get_events(days_ahead=1)
                now = datetime.datetime.now()
                
                for event in events:
                    start_str = event['start'].get('dateTime')
                    if not start_str: continue # Ігноруємо події "на весь день"
                    
                    event_time = datetime.datetime.fromisoformat(start_str).replace(tzinfo=None)
                    time_diff = (event_time - now).total_seconds() / 60.0
                    event_id = event.get('id')
                    
                    # Якщо до події від 4 до 6 хвилин і ми ще не нагадували
                    if 4 <= time_diff <= 6 and event_id not in self.state["reminded_events"]:
                        summary = event.get('summary', 'Зустріч')
                        
                        # Озвучуємо нагадування
                        message = f"Сер, нагадую. За п'ять хвилин у вас заплановано: {summary}. Будь ласка, підготуйтеся."
                        print(f"[CALENDAR REMINDER] {message}")
                        
                        import config_manager as cfg
                        config = cfg.load_config() if hasattr(cfg, 'load_config') else {}
                        speak_text(message, config)
                        
                        # Записуємо в пам'ять
                        self.state["reminded_events"].append(event_id)
                        self._save_state()
                        
            except Exception as e:
                print(f"[CALENDAR ERROR] Фоновий моніторинг впав: {e}")
                
            await asyncio.sleep(60) # Перевіряємо раз на хвилину

    # ==========================================
    # ОБРОБКА КОМАНД ВІД КОРИСТУВАЧА
    # ==========================================
    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        if command_name == "add_account":
            # Цю дію краще виконувати в окремому потоці, бо вона відкриває браузер
            result = await asyncio.to_thread(self._add_new_account)
            return {"success": True, "result": None, "message": result, "speak_text": "Акаунт підключено, сер."}
            
        elif command_name == "read_schedule":
            # Примусовий виклик розкладу
            events = self._get_events(days_ahead=1)
            # Тут можна додати логіку генерації тексту через ask_gpt
            return {"success": True, "result": None, "message": "Озвучую розклад.", "speak_text": "Зараз прочитаю ваш розклад."}

        return {"success": False, "message": f"Невідома команда {command_name}"}