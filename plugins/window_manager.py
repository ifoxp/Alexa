# window_manager.py
import asyncio
import traceback
import json
from typing import Dict, Any, List
from .base_plugin import SmartPlugin


class WindowManagerPlugin(SmartPlugin):
    """Плагін для управління вікнами: розташування, переміщення між моніторами, аналіз та оптимізація."""

    @property
    def name(self) -> str:
        return "window_manager"

    @property
    def description(self) -> str:
        return (
            "Управління вікнами на екрані. "
            "Використовуй коли просять: 'розділи екран', 'згорни всі', 'розташуй вікна для роботи/ігор/відео', "
            "'перенеси вікно на другий монітор', 'налаштуй робоче місце', 'прибери зайві вікна', "
            "'розклади вікна по моніторам', 'підготуй екран для [чогось]'."
        )

    @property
    def commands(self) -> Dict[str, str]:
        return {
            "analyze_and_arrange": "проаналізувати вікна, браузери та монітори і розставити все під мету користувача. Передай мету у value (наприклад: 'робота', 'ігри', 'відео', 'прибери зайве')",
            "minimize_all": "згорнути всі вікна і показати робочий стіл",
            "restore_windows": "відновити всі раніше згорнуті вікна",
            "snap_active_window": "прив'язати активне вікно до частини екрана. value: 'left', 'right', 'top', 'bottom', 'maximize', 'topleft', 'topright', 'bottomleft', 'bottomright'",
            "move_to_monitor": "перенести активне або вказане вікно на інший монітор. value: номер монітора або 'назва програми номер' (наприклад: 'chrome 2')",
        }

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        try:
            value = kwargs.get("value", "")

            if command_name == "analyze_and_arrange":
                return await self._analyze_and_arrange(str(value) if value else "загальне впорядкування")
            elif command_name == "minimize_all":
                return await self._minimize_all()
            elif command_name == "restore_windows":
                return await self._restore_windows()
            elif command_name == "snap_active_window":
                return await self._snap_active_window(str(value))
            elif command_name == "move_to_monitor":
                return await self._move_to_monitor(str(value))
            else:
                return {"success": False, "result": None, "message": f"Невідома команда: {command_name}"}
        except Exception as e:
            traceback.print_exc()
            return {"success": False, "result": None, "message": f"Помилка: {str(e)}"}

    # ── Збір інформації про систему ──────────────────────────────────────────

    def _get_monitors_info(self) -> List[Dict]:
        """Повертає список моніторів з координатами та роздільністю."""
        try:
            import mss
            monitors = []
            with mss.mss() as sct:
                for i, m in enumerate(sct.monitors[1:], 1):
                    monitors.append({
                        "index": i,
                        "x": m["left"],
                        "y": m["top"],
                        "width": m["width"],
                        "height": m["height"],
                        "is_portrait": m["height"] > m["width"],
                    })
            return monitors
        except Exception as e:
            self.log_error(f"Get monitors failed: {e}")
            return []

    def _get_all_windows(self) -> List[Dict]:
        """Повертає список усіх видимих вікон з позиціями та розмірами."""
        import win32gui
        import win32process
        import psutil

        windows = []

        def enum_handler(hwnd, _):
            try:
                if not win32gui.IsWindowVisible(hwnd):
                    return
                title = win32gui.GetWindowText(hwnd)
                if not title or len(title) < 2:
                    return

                rect = win32gui.GetWindowRect(hwnd)
                x, y, x2, y2 = rect
                w, h = x2 - x, y2 - y
                if w < 50 or h < 50:
                    return

                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    proc_name = psutil.Process(pid).name()
                except Exception:
                    proc_name = "unknown"

                windows.append({
                    "hwnd": hwnd,
                    "title": title,
                    "process": proc_name,
                    "x": x, "y": y,
                    "width": w, "height": h,
                })
            except Exception:
                pass

        win32gui.EnumWindows(enum_handler, None)
        return windows

    def _get_browser_tabs(self) -> Dict[str, List[str]]:
        """
        Отримує список відкритих вкладок браузерів через UI Automation.
        Підтримує Chrome, Edge, Firefox.
        """
        tabs = {}
        try:
            import uiautomation as auto

            browser_processes = {
                "chrome.exe": "Google Chrome",
                "msedge.exe": "Microsoft Edge",
                "firefox.exe": "Mozilla Firefox",
            }

            for proc_name, display_name in browser_processes.items():
                try:
                    # Шукаємо головне вікно браузера
                    windows = auto.GetRootControl().GetChildren()
                    for w in windows:
                        try:
                            class_name = w.ClassName
                            name = w.Name
                            if not name:
                                continue

                            is_browser = False
                            if proc_name == "chrome.exe" and "Chrome" in class_name:
                                is_browser = True
                            elif proc_name == "msedge.exe" and "Edge" in class_name:
                                is_browser = True
                            elif proc_name == "firefox.exe" and "MozillaWindowClass" in class_name:
                                is_browser = True

                            if not is_browser:
                                continue

                            # Намагаємось дістати таб-бар
                            tab_bar = w.TabControl()
                            if tab_bar:
                                tab_titles = [t.Name for t in tab_bar.GetChildren() if t.Name]
                                if tab_titles:
                                    tabs[display_name] = tabs.get(display_name, []) + tab_titles
                        except Exception:
                            continue
                except Exception:
                    continue
        except Exception:
            pass

        # Fallback: якщо uiautomation не спрацював — беремо заголовки вікон браузерів
        if not tabs:
            try:
                import win32gui
                import win32process
                import psutil

                browser_map = {
                    "chrome.exe": "Chrome",
                    "msedge.exe": "Edge",
                    "firefox.exe": "Firefox",
                }

                def fallback_handler(hwnd, _):
                    if not win32gui.IsWindowVisible(hwnd):
                        return
                    title = win32gui.GetWindowText(hwnd)
                    if not title:
                        return
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    try:
                        proc = psutil.Process(pid).name().lower()
                        for key, label in browser_map.items():
                            if key in proc:
                                tabs.setdefault(label, []).append(title)
                    except Exception:
                        pass

                win32gui.EnumWindows(fallback_handler, None)
            except Exception:
                pass

        return tabs

    def _find_monitor_for_window(self, wx, wy, ww, wh, monitors: List[Dict]) -> int:
        """Визначає на якому моніторі знаходиться вікно (за центром)."""
        cx = wx + ww // 2
        cy = wy + wh // 2
        for m in monitors:
            if m["x"] <= cx <= m["x"] + m["width"] and m["y"] <= cy <= m["y"] + m["height"]:
                return m["index"]
        return 1

    # ── Головна команда: аналіз + розстановка ───────────────────────────────

    async def _analyze_and_arrange(self, goal: str) -> Dict[str, Any]:
        try:
            # Збираємо всю інфу паралельно
            monitors, windows, browser_tabs = await asyncio.gather(
                asyncio.to_thread(self._get_monitors_info),
                asyncio.to_thread(self._get_all_windows),
                asyncio.to_thread(self._get_browser_tabs),
            )

            if not monitors:
                return {"success": False, "result": None, "message": "Не вдалося отримати інформацію про монітори"}

            # Додаємо до вікон інфо про монітор
            for w in windows:
                w["monitor"] = self._find_monitor_for_window(
                    w["x"], w["y"], w["width"], w["height"], monitors
                )

            # Формуємо промпт для Gemini
            monitor_desc = []
            for m in monitors:
                orient = "вертикальний (портрет)" if m["is_portrait"] else "горизонтальний"
                monitor_desc.append(
                    f"Монітор {m['index']}: {m['width']}x{m['height']}, позиція ({m['x']},{m['y']}), {orient}"
                )

            window_desc = []
            for w in windows:
                window_desc.append(
                    f"  - \"{w['title']}\" [{w['process']}] на моніторі {w['monitor']}, "
                    f"розмір {w['width']}x{w['height']}, позиція ({w['x']},{w['y']})"
                )

            browser_desc = []
            for browser, tab_list in browser_tabs.items():
                browser_desc.append(f"  {browser}: {', '.join(tab_list[:10])}")

            prompt = f"""Ти — розумний оконний менеджер Jarvis. Тобі треба оптимально розставити вікна.

МЕТА КОРИСТУВАЧА: "{goal}"

МОНІТОРИ ({len(monitors)} шт.):
{chr(10).join(monitor_desc)}

ВІДКРИТІ ВІКНА ({len(windows)} шт.):
{chr(10).join(window_desc[:30])}

ВКЛАДКИ БРАУЗЕРІВ:
{chr(10).join(browser_desc) if browser_desc else "  (не вдалося отримати)"}

ЗАВДАННЯ:
1. Проаналізуй конфігурацію моніторів (їх орієнтацію, розміри, позиції)
2. Врахуй вміст браузерів та назви вікон щоб зрозуміти контекст
3. Поверни JSON з двома полями:
   - "actions": масив дій для кожного вікна
   - "speak_text": що сказати користувачу (коротко, українською)

Формат дій (action може бути: "move", "snap", "minimize", "close_suggest", "maximize"):
{{
  "actions": [
    {{
      "title_contains": "частина назви вікна",
      "process": "назва процесу або порожньо",
      "action": "snap",
      "params": {{
        "monitor": 1,
        "position": "left"
      }}
    }},
    {{
      "title_contains": "...",
      "action": "move",
      "params": {{
        "monitor": 2,
        "x": 0, "y": 0,
        "width": 1920, "height": 1080
      }}
    }},
    {{
      "title_contains": "...",
      "action": "minimize",
      "params": {{}}
    }}
  ],
  "speak_text": "Я розставив вікна для роботи: браузер зліва, редактор справа."
}}

Позиції для snap: "left", "right", "top", "bottom", "maximize", "topleft", "topright", "bottomleft", "bottomright"
ВАЖЛИВО: для вертикального монітора враховуй що він повернутий (висота > ширина).
Відповідай ТІЛЬКИ JSON, без пояснень."""

            response_text = await self.ask_gpt(prompt, max_tokens=1500, temperature=0.3)

            # Парсимо відповідь Gemini
            try:
                # Видаляємо можливі markdown блоки
                clean = response_text.strip()
                if clean.startswith("```"):
                    clean = clean.split("```")[1]
                    if clean.startswith("json"):
                        clean = clean[4:]
                plan = json.loads(clean)
            except Exception:
                self.log_error(f"Failed to parse Gemini window plan: {response_text[:200]}")
                return {
                    "success": False,
                    "result": None,
                    "message": "Не вдалося побудувати план розстановки вікон",
                }

            actions = plan.get("actions", [])
            speak_text = plan.get("speak_text", "Виконую розстановку вікон")

            # Виконуємо дії
            executed = []
            errors = []

            for action_item in actions:
                try:
                    result = await asyncio.to_thread(
                        self._execute_window_action, action_item, windows, monitors
                    )
                    if result:
                        executed.append(result)
                except Exception as e:
                    errors.append(str(e))

            self.log_info(f"Arranged {len(executed)} windows for goal='{goal}'")

            return {
                "success": True,
                "result": {"executed": executed, "errors": errors},
                "message": speak_text,
                "speak_text": speak_text,
            }

        except Exception as e:
            traceback.print_exc()
            self.log_error(f"analyze_and_arrange failed: {e}")
            return {"success": False, "result": None, "message": f"Помилка аналізу вікон: {str(e)}"}

    def _execute_window_action(self, action_item: Dict, windows: List[Dict], monitors: List[Dict]) -> str:
        """Виконує одну дію над вікном."""
        import win32gui
        import win32con

        title_contains = action_item.get("title_contains", "").lower()
        process_filter = action_item.get("process", "").lower()
        action = action_item.get("action", "")
        params = action_item.get("params", {})

        # Знаходимо вікно
        hwnd = None
        for w in windows:
            title_match = title_contains and title_contains in w["title"].lower()
            proc_match = process_filter and process_filter in w["process"].lower()

            if title_contains and proc_match is not False and title_match:
                hwnd = w["hwnd"]
                break
            elif not title_contains and proc_match:
                hwnd = w["hwnd"]
                break

        if not hwnd:
            return None

        if action == "minimize":
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return f"Згорнуто: {title_contains}"

        elif action == "maximize":
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            return f"Розгорнуто: {title_contains}"

        elif action == "snap":
            monitor_idx = params.get("monitor", 1)
            position = params.get("position", "maximize")
            monitor = next((m for m in monitors if m["index"] == monitor_idx), monitors[0])
            self._snap_hwnd(hwnd, monitor, position)
            return f"Прив'язано '{title_contains}' до {position} на моніторі {monitor_idx}"

        elif action == "move":
            monitor_idx = params.get("monitor", 1)
            monitor = next((m for m in monitors if m["index"] == monitor_idx), monitors[0])
            x = monitor["x"] + params.get("x", 0)
            y = monitor["y"] + params.get("y", 0)
            w = params.get("width", monitor["width"])
            h = params.get("height", monitor["height"])
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.MoveWindow(hwnd, x, y, w, h, True)
            return f"Переміщено '{title_contains}' на монітор {monitor_idx}"

        return None

    def _snap_hwnd(self, hwnd, monitor: Dict, position: str):
        """Прив'язує вікно до частини монітора."""
        import win32gui
        import win32con

        mx, my = monitor["x"], monitor["y"]
        mw, mh = monitor["width"], monitor["height"]
        hw, hh = mw // 2, mh // 2

        positions = {
            "left":        (mx,        my,        hw,   mh),
            "right":       (mx + hw,   my,        hw,   mh),
            "top":         (mx,        my,        mw,   hh),
            "bottom":      (mx,        my + hh,   mw,   hh),
            "topleft":     (mx,        my,        hw,   hh),
            "topright":    (mx + hw,   my,        hw,   hh),
            "bottomleft":  (mx,        my + hh,   hw,   hh),
            "bottomright": (mx + hw,   my + hh,   hw,   hh),
            "maximize":    (mx,        my,        mw,   mh),
        }

        coords = positions.get(position, (mx, my, mw, mh))
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.MoveWindow(hwnd, coords[0], coords[1], coords[2], coords[3], True)

    # ── Прості команди ───────────────────────────────────────────────────────

    async def _minimize_all(self) -> Dict[str, Any]:
        try:
            import win32gui
            import win32con

            def minimize_handler(hwnd, _):
                if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                    try:
                        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                    except Exception:
                        pass

            await asyncio.to_thread(win32gui.EnumWindows, minimize_handler, None)
            self.log_info("All windows minimized")
            return {"success": True, "result": None, "message": "Всі вікна згорнуто, показую робочий стіл"}
        except Exception as e:
            return {"success": False, "result": None, "message": f"Помилка: {str(e)}"}

    async def _restore_windows(self) -> Dict[str, Any]:
        try:
            import win32gui
            import win32con

            def restore_handler(hwnd, _):
                if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                    try:
                        placement = win32gui.GetWindowPlacement(hwnd)
                        if placement[1] == win32con.SW_SHOWMINIMIZED:
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    except Exception:
                        pass

            await asyncio.to_thread(win32gui.EnumWindows, restore_handler, None)
            self.log_info("Windows restored")
            return {"success": True, "result": None, "message": "Вікна відновлено"}
        except Exception as e:
            return {"success": False, "result": None, "message": f"Помилка: {str(e)}"}

    async def _snap_active_window(self, position: str) -> Dict[str, Any]:
        try:
            import win32gui

            hwnd = await asyncio.to_thread(win32gui.GetForegroundWindow)
            title = win32gui.GetWindowText(hwnd)
            monitors = await asyncio.to_thread(self._get_monitors_info)

            if not monitors:
                return {"success": False, "result": None, "message": "Монітори не знайдено"}

            # Визначаємо на якому моніторі зараз вікно
            rect = win32gui.GetWindowRect(hwnd)
            x, y, x2, y2 = rect
            monitor_idx = self._find_monitor_for_window(x, y, x2 - x, y2 - y, monitors)
            monitor = next((m for m in monitors if m["index"] == monitor_idx), monitors[0])

            await asyncio.to_thread(self._snap_hwnd, hwnd, monitor, position)
            self.log_info(f"Snapped '{title}' to {position} on monitor {monitor_idx}")
            return {"success": True, "result": None, "message": f"Вікно '{title}' прив'язано до позиції '{position}'"}
        except Exception as e:
            return {"success": False, "result": None, "message": f"Помилка: {str(e)}"}

    async def _move_to_monitor(self, value: str) -> Dict[str, Any]:
        try:
            import win32gui
            import win32con

            monitors = await asyncio.to_thread(self._get_monitors_info)
            if not monitors:
                return {"success": False, "result": None, "message": "Монітори не знайдено"}

            # Парсимо: або просто "2", або "chrome 2"
            parts = value.strip().split()
            monitor_num = None
            window_title_filter = None

            for part in reversed(parts):
                if part.isdigit():
                    monitor_num = int(part)
                    window_title_filter = " ".join(p for p in parts if p != part).lower()
                    break

            if monitor_num is None:
                return {"success": False, "result": None, "message": "Вкажи номер монітора, наприклад: 'перенеси на монітор 2'"}

            target_monitor = next((m for m in monitors if m["index"] == monitor_num), None)
            if not target_monitor:
                return {"success": False, "result": None, "message": f"Монітор {monitor_num} не знайдено"}

            # Знаходимо вікно
            if window_title_filter:
                windows = await asyncio.to_thread(self._get_all_windows)
                hwnd = None
                for w in windows:
                    if window_title_filter in w["title"].lower() or window_title_filter in w["process"].lower():
                        hwnd = w["hwnd"]
                        break
                if not hwnd:
                    return {"success": False, "result": None, "message": f"Вікно '{window_title_filter}' не знайдено"}
            else:
                hwnd = await asyncio.to_thread(win32gui.GetForegroundWindow)

            title = win32gui.GetWindowText(hwnd)

            # Переміщуємо на монітор (розгортаємо на весь екран)
            mx, my = target_monitor["x"], target_monitor["y"]
            mw, mh = target_monitor["width"], target_monitor["height"]

            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.MoveWindow(hwnd, mx, my, mw, mh, True)

            self.log_info(f"Moved '{title}' to monitor {monitor_num}")
            return {"success": True, "result": None, "message": f"Вікно '{title}' переміщено на монітор {monitor_num}"}

        except Exception as e:
            traceback.print_exc()
            return {"success": False, "result": None, "message": f"Помилка: {str(e)}"}
