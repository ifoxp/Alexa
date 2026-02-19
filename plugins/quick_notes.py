# plugins/quick_notes.py
import os
import datetime
import ctypes
from ctypes import wintypes
from typing import Dict, Any
from .base_plugin import SmartPlugin

class QuickNotesPlugin(SmartPlugin):
    """
    Плагін для швидкого створення нотаток.
    Використовує Windows API для отримання точного шляху до Робочого столу.
    """

    @property
    def name(self) -> str:
        return "quick_notes"

    @property
    def description(self) -> str:
        return "Швидке створення нотаток, заміток, напоминалок, ідей."

    @property
    def commands(self) -> Dict[str, str]:
        return {
            "add_note": "створити нотатку (текст нотатки)",
            "read_today": "прочитати нотатки за сьогодні",
            "open_notes_folder": "відкрити папку з нотатками"
        }

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        try:
            # Отримуємо справжній шлях через Windows API
            desktop = self._get_real_desktop_path()
            notes_dir = os.path.join(desktop, "AI_Notes")
            
            # Створюємо папку
            if not os.path.exists(notes_dir):
                os.makedirs(notes_dir)
                self.log_info(f"Created notes directory at: {notes_dir}")

            today_str = datetime.datetime.now().strftime("%Y-%m-%d")
            file_path = os.path.join(notes_dir, f"{today_str}.md")

            if command_name == "add_note":
                text = kwargs.get("value", "")
                if not text:
                    return {"success": False, "message": "Нотатка пуста."}

                formatted_entry = self._structure_note(text)
                
                with open(file_path, "a", encoding="utf-8") as f:
                    f.write(formatted_entry)

                return {
                    "success": True,
                    "message": "Записав."
                }

            elif command_name == "read_today":
                if not os.path.exists(file_path):
                    return {"success": True, "message": "На сьогодні записів немає."}
                
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                clean_content = content.replace("##", "").replace("**", "")
                preview = clean_content[:300] + "..." if len(clean_content) > 300 else clean_content
                
                return {
                    "success": True, 
                    "result": {"content": content},
                    "message": f"Ваші нотатки: {preview}"
                }

            elif command_name == "open_notes_folder":
                os.startfile(notes_dir)
                return {"success": True, "message": "Відкриваю папку."}

            else:
                return {"success": False, "message": "Невідома команда."}

        except Exception as e:
            self.log_error(f"Notes error", error=str(e))
            return {"success": False, "message": f"Помилка: {str(e)}"}

    def _get_real_desktop_path(self) -> str:
        """
        Запитує у Windows точний шлях до папки Desktop через CSIDL.
        Працює незалежно від мови системи чи OneDrive.
        """
        CSIDL_DESKTOP = 0x0000
        SHGFP_TYPE_CURRENT = 0
        buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        
        # Виклик shell32.dll
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOP, None, SHGFP_TYPE_CURRENT, buf)
        
        return buf.value

    def _structure_note(self, text: str) -> str:
        now_time = datetime.datetime.now().strftime("%H:%M")
        category = "📝 General"
        lower_text = text.lower()
        
        if any(w in lower_text for w in ['баг', 'fix', 'код', 'api']): category = "🐛 Dev"
        elif any(w in lower_text for w in ['купити', 'ціна']): category = "🛒 Shop"
        elif any(w in lower_text for w in ['ідея', 'фіча']): category = "💡 Idea"
        elif any(w in lower_text for w in ['офіс', 'зустріч', 'план']): category = "📅 Plan"
        
        entry = f"\n## [{now_time}] {category}\n{text.capitalize()}\n" + "-"*30 + "\n"
        return entry