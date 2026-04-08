# system_monitor.py
import asyncio
import traceback
from typing import Dict, Any
from .base_plugin import SmartPlugin


def _n(value, decimals=0) -> str:
    """Число → рядок без зайвих символів для TTS (без % і °C — вони додаються словами окремо)."""
    if decimals == 0:
        return str(int(round(value)))
    return f"{value:.{decimals}f}".replace(".", ",")


class SystemMonitorPlugin(SmartPlugin):
    """Плагін для моніторингу системних ресурсів: CPU, GPU, RAM, диски."""

    @property
    def name(self) -> str:
        return "system_monitor"

    @property
    def description(self) -> str:
        return (
            "Моніторинг системних ресурсів комп'ютера. "
            "Використовуй коли питають 'як почувається система', 'перевір температуру', "
            "'скільки оперативки', 'перевір навантаження', 'скільки працює пк', "
            "'перевір диски', 'що треба почистити на комп'ютері'."
        )

    @property
    def commands(self) -> Dict[str, str]:
        return {
            "get_hardware_status": "навантаження і температура CPU з деталями по перевантажених ядрах, навантаження і температура GPU, використання RAM",
            "get_uptime": "скільки часу комп'ютер безперервно працює з моменту останнього запуску",
            "get_disk_status": "заповненість дисків, розмір кошика і тимчасових файлів — що варто почистити",
        }

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        try:
            if command_name == "get_hardware_status":
                return await self._get_hardware_status()
            elif command_name == "get_uptime":
                return await self._get_uptime()
            elif command_name == "get_disk_status":
                return await self._get_disk_status()
            else:
                return {"success": False, "result": None, "message": f"Невідома команда: {command_name}"}
        except Exception as e:
            traceback.print_exc()
            return {"success": False, "result": None, "message": f"Помилка: {str(e)}"}

    # ── CPU ──────────────────────────────────────────────────────────────────

    async def _get_cpu_info(self) -> Dict[str, Any]:
        import psutil

        per_core = await asyncio.to_thread(psutil.cpu_percent, 0.5, True)
        total_load = sum(per_core) / len(per_core)

        # Ядра завантажені більше за 70%
        hot_cores = sorted(
            [(i, load) for i, load in enumerate(per_core) if load > 70],
            key=lambda x: x[1], reverse=True
        )

        temps = await asyncio.to_thread(self._read_cpu_temps)

        parts = [f"Процесор: {_n(total_load)} відсотків"]
        if hot_cores:
            core_list = ", ".join(f"ядро {_n(i+1)} на {_n(load)} відсотків" for i, load in hot_cores[:3])
            parts.append(f"гарячі ядра: {core_list}")
        if temps:
            parts.append(f"температура {temps}")

        return {
            "total_load": round(total_load, 1),
            "hot_cores": hot_cores,
            "temperature": temps,
            "message": ", ".join(parts),
        }

    def _read_cpu_temps(self) -> str:
        try:
            import psutil
            sensors = psutil.sensors_temperatures()
            if sensors:
                for key in ("coretemp", "k10temp", "cpu_thermal", "acpitz"):
                    if key in sensors:
                        vals = [e.current for e in sensors[key] if e.current and e.current > 0]
                        if vals:
                            return f"середня {_n(sum(vals)/len(vals))} градусів, максимум {_n(max(vals))} градусів"
                for key, entries in sensors.items():
                    vals = [e.current for e in entries if e.current and e.current > 20]
                    if vals:
                        return f"приблизно {_n(max(vals))} градусів"
        except Exception:
            pass

        # Fallback: OpenHardwareMonitor через WMI
        try:
            import wmi
            w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            vals = [
                float(s.Value) for s in w.Sensor()
                if s.SensorType == "Temperature" and "CPU" in s.Name and float(s.Value) > 20
            ]
            if vals:
                return f"середня {_n(sum(vals)/len(vals))} градусів, максимум {_n(max(vals))} градусів"
        except Exception:
            pass

        return "недоступна"

    # ── GPU ──────────────────────────────────────────────────────────────────

    async def _get_gpu_info(self) -> list:
        return await asyncio.to_thread(self._read_gpu_data)

    def _read_gpu_data(self) -> list:
        result = []

        # pynvml — офіційна NVIDIA бібліотека
        try:
            import pynvml
            pynvml.nvmlInit()
            for i in range(pynvml.nvmlDeviceGetCount()):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode()
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                result.append({
                    "name": name,
                    "load": util.gpu,
                    "mem_used_mb": round(mem.used / 1024 / 1024),
                    "mem_total_mb": round(mem.total / 1024 / 1024),
                    "mem_percent": round(mem.used / mem.total * 100),
                    "temperature": temp,
                })
            pynvml.nvmlShutdown()
            return result
        except Exception:
            pass

        # Fallback: GPUtil
        try:
            import GPUtil
            for gpu in GPUtil.getGPUs():
                result.append({
                    "name": gpu.name,
                    "load": round(gpu.load * 100),
                    "mem_used_mb": round(gpu.memoryUsed),
                    "mem_total_mb": round(gpu.memoryTotal),
                    "mem_percent": round(gpu.memoryUtil * 100),
                    "temperature": round(gpu.temperature),
                })
            return result
        except Exception:
            pass

        return result

    # ── RAM ──────────────────────────────────────────────────────────────────

    async def _get_ram_info(self) -> Dict[str, Any]:
        import psutil
        ram = psutil.virtual_memory()
        used_gb = ram.used / 1024 ** 3
        total_gb = ram.total / 1024 ** 3
        return {
            "used_gb": round(used_gb, 1),
            "total_gb": round(total_gb, 1),
            "available_gb": round(ram.available / 1024 ** 3, 1),
            "percent": ram.percent,
            "message": f"Оперативна пам'ять: {_n(used_gb, 1)} з {_n(total_gb, 1)} гігабайт, {_n(ram.percent)} відсотків",
        }

    # ── Команда 1: CPU + GPU + RAM ───────────────────────────────────────────

    async def _get_hardware_status(self) -> Dict[str, Any]:
        try:
            cpu, gpu_list, ram = await asyncio.gather(
                self._get_cpu_info(),
                self._get_gpu_info(),
                self._get_ram_info(),
            )

            parts = [cpu["message"], ram["message"]]

            if gpu_list:
                for gpu in gpu_list:
                    parts.append(
                        f"{gpu['name']}: навантаження {_n(gpu['load'])} відсотків, "
                        f"відеопам'ять {_n(gpu['mem_used_mb'])} з {_n(gpu['mem_total_mb'])} мегабайт, "
                        f"температура {_n(gpu['temperature'])} градусів"
                    )
            else:
                parts.append("GPU: дані недоступні (встанови pynvml або GPUtil)")

            self.log_info(f"Hardware status: CPU={cpu['total_load']}%, RAM={ram['percent']}%")

            return {
                "success": True,
                "result": {"cpu": cpu, "gpu": gpu_list, "ram": ram},
                "message": ". ".join(parts),
            }
        except Exception as e:
            self.log_error(f"Hardware status failed: {e}")
            return {"success": False, "result": None, "message": f"Помилка: {str(e)}"}

    # ── Команда 2: Аптайм ────────────────────────────────────────────────────

    async def _get_uptime(self) -> Dict[str, Any]:
        try:
            import psutil
            import time
            import datetime

            uptime_seconds = int(time.time() - psutil.boot_time())
            td = datetime.timedelta(seconds=uptime_seconds)

            days = td.days
            hours, remainder = divmod(td.seconds, 3600)
            minutes = remainder // 60

            parts = []
            if days:
                parts.append(f"{_n(days)} {'день' if days == 1 else 'дні' if 2 <= days <= 4 else 'днів'}")
            if hours:
                parts.append(f"{_n(hours)} {'година' if hours == 1 else 'години' if 2 <= hours <= 4 else 'годин'}")
            if minutes:
                parts.append(f"{_n(minutes)} {'хвилину' if minutes == 1 else 'хвилини' if 2 <= minutes <= 4 else 'хвилин'}")

            uptime_str = " ".join(parts) if parts else "менше хвилини"
            message = f"Комп'ютер працює {uptime_str} без перезапуску"

            self.log_info(f"Uptime: {uptime_str}")
            return {"success": True, "result": {"uptime_seconds": uptime_seconds, "uptime_str": uptime_str}, "message": message}
        except Exception as e:
            self.log_error(f"Uptime failed: {e}")
            return {"success": False, "result": None, "message": f"Помилка: {str(e)}"}

    # ── Команда 3: Диски + кошик + temp ─────────────────────────────────────

    async def _get_disk_status(self) -> Dict[str, Any]:
        try:
            import psutil

            disk_parts = psutil.disk_partitions(all=False)
            disk_info = []
            messages = []

            for p in disk_parts:
                try:
                    usage = psutil.disk_usage(p.mountpoint)
                    total_gb = usage.total / 1024 ** 3
                    used_gb = usage.used / 1024 ** 3
                    free_gb = usage.free / 1024 ** 3
                    percent = usage.percent

                    disk_info.append({
                        "drive": p.mountpoint,
                        "total_gb": round(total_gb, 1),
                        "used_gb": round(used_gb, 1),
                        "free_gb": round(free_gb, 1),
                        "percent": percent,
                    })

                    warn = ", мало місця!" if percent > 85 else ""
                    messages.append(f"Диск {p.mountpoint}: {_n(used_gb)} з {_n(total_gb)} гігабайт, {_n(percent)} відсотків{warn}")
                except PermissionError:
                    continue

            # Кошик
            recycle_gb = await asyncio.to_thread(self._get_recycle_bin_size)
            if recycle_gb > 0.01:
                messages.append(f"Кошик займає {_n(recycle_gb, 1)} гігабайт, можна очистити")

            # Тимчасові файли Windows
            temp_gb = await asyncio.to_thread(self._get_temp_folder_size)
            if temp_gb > 0.1:
                messages.append(f"Тимчасові файли займають {_n(temp_gb, 1)} гігабайт, варто очистити")

            # Папка завантажень (інформативно, якщо велика)
            downloads_gb = await asyncio.to_thread(self._get_downloads_size)
            if downloads_gb > 5:
                messages.append(f"Папка завантажень займає {_n(downloads_gb, 1)} гігабайт, перевір чи є непотрібне")

            message = ". ".join(messages) if messages else "Дані по дисках недоступні"
            self.log_info(f"Disk status: {message}")

            return {
                "success": True,
                "result": {
                    "disks": disk_info,
                    "recycle_bin_gb": recycle_gb,
                    "temp_folder_gb": temp_gb,
                    "downloads_gb": downloads_gb,
                },
                "message": message,
            }
        except Exception as e:
            self.log_error(f"Disk status failed: {e}")
            return {"success": False, "result": None, "message": f"Помилка: {str(e)}"}

    def _get_recycle_bin_size(self) -> float:
        """Розмір кошика в ГБ через winshell або пряме сканування."""
        try:
            import winshell
            total = sum(item.size() for item in winshell.recycle_bin())
            return total / 1024 ** 3
        except Exception:
            pass

        # Fallback: пряме сканування папки $Recycle.Bin
        try:
            import os
            total = 0
            for drive_letter in "CDEFGH":
                rb_path = f"{drive_letter}:\\$Recycle.Bin"
                if not os.path.exists(rb_path):
                    continue
                for root, _, files in os.walk(rb_path):
                    for f in files:
                        try:
                            total += os.path.getsize(os.path.join(root, f))
                        except Exception:
                            pass
            return total / 1024 ** 3
        except Exception:
            return 0.0

    def _get_temp_folder_size(self) -> float:
        """Розмір папки %TEMP% в ГБ."""
        try:
            import os
            temp_path = os.environ.get("TEMP") or os.environ.get("TMP") or "C:\\Windows\\Temp"
            total = 0
            for root, _, files in os.walk(temp_path):
                for f in files:
                    try:
                        total += os.path.getsize(os.path.join(root, f))
                    except Exception:
                        pass
            return total / 1024 ** 3
        except Exception:
            return 0.0

    def _get_downloads_size(self) -> float:
        """Розмір папки Завантаження в ГБ."""
        try:
            import os
            downloads = os.path.join(os.path.expanduser("~"), "Downloads")
            if not os.path.exists(downloads):
                return 0.0
            total = 0
            for root, _, files in os.walk(downloads):
                for f in files:
                    try:
                        total += os.path.getsize(os.path.join(root, f))
                    except Exception:
                        pass
            return total / 1024 ** 3
        except Exception:
            return 0.0
