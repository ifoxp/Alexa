# windows_programs.py
import os
import subprocess
import webbrowser
import json
from typing import Dict, List, Any
from .base_plugin import SmartPlugin
import smart_ai


class WindowsProgramsPlugin(SmartPlugin):
    """Плагін для пошуку та запуску Windows програм."""

    @property
    def name(self) -> str:
        return "windows_programs"

    @property
    def description(self) -> str:
        return "Запуск програм Windows: Steam, Discord, Telegram, браузери, ігри, додатки (наприклад: 'відкрий Steam', 'запусти Discord')"

    @property
    def commands(self) -> Dict[str, str]:
        return {
            "open_program": "відкрити програму (назва програми)"
        }

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        """Виконує команду плагіна з розумним пошуком через ШІ."""
        try:
            if command_name == "open_program":
                print(f"\n=== WINDOWS_PROGRAMS DEBUG ===")
                print(f"[1] Received command: {command_name}")
                print(f"[2] All kwargs: {kwargs}")

                # Отримуємо назву програми з параметрів
                program_query = kwargs.get("value", "")

                print(f"[3] Extracted program_query: '{program_query}'")

                if not program_query:
                    print(f"[ERROR] No program query provided")
                    return {
                        "success": False,
                        "result": None,
                        "message": "Не вказано назву програми"
                    }

                print(f"[4] Starting Universal Launcher...")

                # Використовуємо Universal Launcher (твій код)
                result = await self._universal_launcher(program_query)

                print(f"[FINAL] Universal launcher result: {result}")
                print(f"=== END WINDOWS_PROGRAMS DEBUG ===\n")

                return result

            else:
                return {
                    "success": False,
                    "result": None,
                    "message": f"Невідома команда: {command_name}"
                }

        except Exception as e:
            self.log_error(f"Error executing {command_name}", error=str(e))
            return {
                "success": False,
                "result": None,
                "message": f"Помилка виконання команди: {str(e)}"
            }

    async def _search_programs(self, query: str) -> Dict[str, Any]:
        """Шукає програми за запитом."""
        if not query:
            return {
                "success": False,
                "result": None,
                "message": "Запит для пошуку не може бути пустим"
            }

        mapper = smart_ai.get_program_mapper()
        all_programs = mapper.installed_programs

        query_lower = query.lower()
        matches = []

        # Додатковий пошук через PowerShell для конкретних програм
        if not matches and query_lower in ['telegram', 'chrome', 'firefox', 'discord']:
            powershell_matches = await self._search_via_powershell(query)
            matches.extend(powershell_matches)

        # Пошук за назвою програми (включаючи часткові збіги)
        for name, path in all_programs.items():
            name_lower = name.lower()

            # Прямий збіг
            if query_lower in name_lower:
                matches.append({
                    "name": name,
                    "path": path,
                    "match_type": "name"
                })
            # Спеціальні збіги для популярних програм
            elif query_lower == "telegram" and "telegram" in name_lower:
                matches.append({
                    "name": name,
                    "path": path,
                    "match_type": "special"
                })
            elif query_lower == "chrome" and "chrome" in name_lower:
                matches.append({
                    "name": name,
                    "path": path,
                    "match_type": "special"
                })
            elif query_lower == "firefox" and "firefox" in name_lower:
                matches.append({
                    "name": name,
                    "path": path,
                    "match_type": "special"
                })

        # Додаємо системні програми
        system_programs = {
            "calculator": "calc.exe",
            "калькулятор": "calc.exe",
            "notepad": "notepad.exe",
            "блокнот": "notepad.exe",
            "paint": "mspaint.exe",
            "explorer": "explorer.exe",
            "провідник": "explorer.exe"
        }

        for sys_name, sys_path in system_programs.items():
            if query_lower in sys_name.lower():
                matches.append({
                    "name": sys_name,
                    "path": sys_path,
                    "match_type": "system"
                })

        return {
            "success": True,
            "result": matches,
            "message": f"Знайдено {len(matches)} програм за запитом '{query}'"
        }

    async def _open_program(self, program_name: str) -> Dict[str, Any]:
        """Відкриває програму за назвою."""
        if not program_name:
            return {
                "success": False,
                "result": None,
                "message": "Назва програми не може бути пустою"
            }

        mapper = smart_ai.get_program_mapper()
        mapped_path = mapper.map_app_name(program_name)

        success = await self._launch_application(mapped_path)

        if success:
            return {
                "success": True,
                "result": {"program": program_name, "path": mapped_path},
                "message": f"Запущено програму: {program_name}"
            }
        else:
            return {
                "success": False,
                "result": None,
                "message": f"Не вдалося запустити програму: {program_name}"
            }

    async def _list_programs(self) -> Dict[str, Any]:
        """Повертає список всіх доступних програм."""
        mapper = smart_ai.get_program_mapper()
        programs = list(mapper.installed_programs.keys())

        return {
            "success": True,
            "result": programs[:50],  # Обмежуємо до 50 для GPT
            "message": f"Знайдено {len(programs)} програм (показано перші 50)"
        }

    async def _launch_application(self, path: str) -> bool:
        """Запускає додаток."""
        try:
            # Розширюємо змінні середовища
            expanded_path = os.path.expandvars(path)

            # === ЛОГІКА ДЛЯ ЗАПУСКУ MS STORE ДОДАТКІВ ===
            if expanded_path.startswith("shell:AppsFolder"):
                launch_cmd = f'explorer.exe {expanded_path}'
                subprocess.Popen(launch_cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                self.log_info(f"Launched MS Store App: {expanded_path}")
                return True
            # ============================================

            # Якщо це URL - відкриваємо в браузері
            if expanded_path.startswith(('http://', 'https://')):
                webbrowser.open(expanded_path)
                self.log_info(f"Opened website: {expanded_path}")
                return True

            # Якщо це .lnk файл, використовуємо os.startfile (без консолі)
            if expanded_path.endswith('.lnk') and os.path.exists(expanded_path):
                os.startfile(expanded_path)
                self.log_info(f"Launched .lnk file: {expanded_path}")
                return True

            # Спробуємо запустити через Windows start команду
            if self._try_start_app_via_windows(path):
                self.log_info(f"Launched via Windows start: {path}")
                return True

            # Якщо це команда з параметрами
            if ' --' in expanded_path:
                parts = expanded_path.split(' ', 1)
                exe_path = parts[0]
                args = parts[1]
                if os.path.exists(exe_path) or exe_path in ['calc.exe', 'notepad.exe', 'mspaint.exe', 'explorer.exe']:
                    subprocess.Popen(f'"{exe_path}" {args}', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    self.log_info(f"Launched with args: {exe_path}")
                    return True

            # Звичайні exe файли та системні команди
            if os.path.exists(expanded_path) or expanded_path in ['calc.exe', 'notepad.exe', 'mspaint.exe', 'explorer.exe']:
                subprocess.Popen([expanded_path], creationflags=subprocess.CREATE_NO_WINDOW)
                self.log_info(f"Launched directly: {expanded_path}")
                return True

            return False

        except Exception as e:
            self.log_error(f"Failed to launch application {path}", error=str(e))
            return False

    def _try_start_app_via_windows(self, app_name: str) -> bool:
        """Намагається запустити програму через Windows start команду."""
        try:
            # Якщо це вже повний шлях до exe - не використовуємо start
            if app_name.endswith('.exe') and ('\\' in app_name or '/' in app_name):
                return False

            # Спробуємо декілька варіантів запуску
            methods = [
                # 1. Windows start команда
                ["cmd", "/c", "start", app_name],
                # 2. Безпосередньо через shell
                ["cmd", "/c", app_name],
                # 3. PowerShell Start-Process
                ["powershell", "-Command", f"Start-Process '{app_name}' -ErrorAction SilentlyContinue"]
            ]

            for method in methods:
                try:
                    result = subprocess.run(
                        method,
                        capture_output=True,
                        text=True,
                        timeout=3,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )

                    if result.returncode == 0:
                        return True

                except Exception:
                    continue

            return False

        except Exception:
            return False

    async def _test_search(self, query: str) -> Dict[str, Any]:
        """Тестує різні методи пошуку програм"""
        print(f"\n[TEST] Searching for '{query}' using different methods...")
        results = {}

        # Метод 1: Windows Search через PowerShell
        try:
            print(f"[TEST] Method 1: Windows Search via PowerShell")
            ps_command = f"Get-StartApps | Where-Object {{$_.Name -like '*{query}*'}} | Select-Object Name, AppID"
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print(f"[TEST] PowerShell output: {result.stdout[:200]}...")
                results["powershell_search"] = result.stdout
            else:
                print(f"[TEST] PowerShell failed: {result.stderr}")
        except Exception as e:
            print(f"[TEST] PowerShell error: {e}")

        # Метод 2: Windows Start menu search
        try:
            print(f"[TEST] Method 2: Start Menu items")
            start_menu_paths = [
                os.path.expanduser("~/AppData/Roaming/Microsoft/Windows/Start Menu/Programs"),
                "C:/ProgramData/Microsoft/Windows/Start Menu/Programs"
            ]

            found_shortcuts = []
            for path in start_menu_paths:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            if file.lower().endswith('.lnk') and query.lower() in file.lower():
                                full_path = os.path.join(root, file)
                                found_shortcuts.append(full_path)
                                print(f"[TEST] Found shortcut: {file} -> {full_path}")

            results["start_menu_shortcuts"] = found_shortcuts

        except Exception as e:
            print(f"[TEST] Start menu search error: {e}")

        # Метод 3: Спробувати запустити напряму
        try:
            print(f"[TEST] Method 3: Direct launch test")
            test_commands = [
                f"{query}",
                f"{query}.exe",
                f"start {query}",
                f"start \"\" \"{query}\""
            ]

            for cmd in test_commands:
                try:
                    print(f"[TEST] Testing: {cmd}")
                    test_result = subprocess.run(
                        ["cmd", "/c", cmd],
                        capture_output=True, text=True, timeout=3,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    print(f"[TEST] Command '{cmd}' - return code: {test_result.returncode}")
                    if test_result.returncode == 0:
                        results["direct_launch_success"] = cmd
                        break
                except Exception as inner_e:
                    print(f"[TEST] Command '{cmd}' failed: {inner_e}")

        except Exception as e:
            print(f"[TEST] Direct launch error: {e}")

        return {
            "success": True,
            "result": results,
            "message": f"Completed search test for '{query}'"
        }

    async def _search_via_powershell(self, query: str) -> List[Dict[str, Any]]:
        """Пошук програми через PowerShell (спеціально для MS Store додатків)"""
        matches = []
        try:
            print(f"[POWERSHELL_SEARCH] Looking for Store apps matching: '{query}'")
            ps_command = 'Get-StartApps | Select-Object Name, AppID | ConvertTo-Json -Compress'
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True, check=True
            )
            
            # Безпечне розкодування (кирилиця/латиниця)
            try:
                output = result.stdout.decode('cp1251')
            except UnicodeDecodeError:
                output = result.stdout.decode('utf-8', errors='ignore')

            if not output.strip():
                return matches

            apps = json.loads(output)
            # Якщо повернувся один об'єкт, а не список
            if isinstance(apps, dict):
                apps = [apps]

            for app in apps:
                name = app.get('Name', '')
                app_id = app.get('AppID', '')
                
                # Порівнюємо в нижньому регістрі
                if query.lower() in name.lower():
                    # Визначаємо пріоритет для сортування
                    priority = 0
                    if name.lower() == query.lower(): priority = 10
                    elif name.lower().startswith(query.lower()): priority = 5
                    else: priority = 2

                    matches.append({
                        "name": name,
                        "path": f"shell:AppsFolder\\{app_id}", # Спеціальний шлях!
                        "priority": priority
                    })
                    print(f"[POWERSHELL_SEARCH] Found: {name} -> {app_id}")
                    
        except Exception as e:
            self.log_error(f"PowerShell search failed for {query}", error=str(e))
            print(f"[POWERSHELL_SEARCH] Error: {e}")

        return matches


    async def _universal_launcher(self, program_query: str) -> Dict[str, Any]:
        """Universal launcher - шукає програми через ярлики Start Menu та MS Store."""
        query = program_query.lower().strip()

        print(f"[UNIVERSAL_LAUNCHER] Starting search for: '{query}'")

        # 1. Складаємо список усіх місць, де можуть бути ярлики
        search_dirs = [
            os.path.join(os.environ['AppData'], r'Microsoft\Windows\Start Menu\Programs'),
            os.path.join(os.environ.get('ProgramData', 'C:\\ProgramData'), r'Microsoft\Windows\Start Menu\Programs'),
            os.path.join(os.environ['USERPROFILE'], 'Desktop'),
            os.path.join(os.environ['USERPROFILE'], 'OneDrive', 'Desktop')
        ]

        candidates = []

        # 2. Скануємо ці папки на наявність .lnk та .exe
        for d in search_dirs:
            if not os.path.exists(d):
                continue
            print(f"[UNIVERSAL_LAUNCHER] Scanning: {d}")

            for root, _, files in os.walk(d):
                for f in files:
                    if query in f.lower() and f.endswith(('.lnk', '.exe')):
                        full_path = os.path.join(root, f)
                        name = f.replace('.lnk', '').replace('.exe', '')

                        priority = 0
                        if name.lower() == query: priority = 10
                        elif name.lower().startswith(query): priority = 5
                        else: priority = 1

                        candidates.append({
                            "name": name,
                            "path": full_path,
                            "priority": priority
                        })

        # === ДОДАЄМО ПОШУК MS STORE ДОДАТКІВ ===
        print(f"[UNIVERSAL_LAUNCHER] Scanning MS Store applications...")
        store_candidates = await self._search_via_powershell(query)
        candidates.extend(store_candidates)
        # =======================================

        # 3. Сортуємо: спочатку найвищий пріоритет
        candidates = sorted(candidates, key=lambda x: x['priority'], reverse=True)

        # Видаляємо дублікати
        seen = set()
        final_list = []
        for c in candidates:
            if c['name'].lower() not in seen:
                final_list.append(c)
                seen.add(c['name'].lower())

        print(f"[UNIVERSAL_LAUNCHER] Found {len(final_list)} candidates")
        for i, app in enumerate(final_list[:3], 1):
            print(f"[UNIVERSAL_LAUNCHER] {i}. {app['name']} (priority: {app['priority']}) -> {app['path']}")

        # 4. Спробуємо запустити кращі варіанти
        for app in final_list[:3]:
            print(f"[UNIVERSAL_LAUNCHER] Trying to launch: {app['name']} -> {app['path']}")
            success = await self._launch_application(app['path'])
            if success:
                print(f"[UNIVERSAL_LAUNCHER] Successfully launched: {app['name']}")
                return {
                    "success": True,
                    "result": {"name": app['name'], "path": app['path']},
                    "message": f"Запущено програму: {app['name']}"
                }
            else:
                print(f"[UNIVERSAL_LAUNCHER] Failed to launch: {app['name']}")

        print(f"[UNIVERSAL_LAUNCHER] No working applications found for '{query}'")
        return {
            "success": False,
            "result": None,
            "message": f"Програму '{program_query}' не знайдено"
        }