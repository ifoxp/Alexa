# __init__.py
"""
Smart plugins package for AI-powered voice assistant.
Contains plugins for Windows programs, browser search, and system control.
"""

from .base_plugin import SmartPlugin
from .windows_programs import WindowsProgramsPlugin
from .browser_search import BrowserSearchPlugin
from .sound_control import SystemControlPlugin

# Список всіх доступних плагінів
AVAILABLE_PLUGINS = [
    WindowsProgramsPlugin,
    BrowserSearchPlugin,
    SystemControlPlugin
]

__all__ = [
    'SmartPlugin',
    'WindowsProgramsPlugin',
    'BrowserSearchPlugin',
    'SystemControlPlugin',
    'AVAILABLE_PLUGINS'
]