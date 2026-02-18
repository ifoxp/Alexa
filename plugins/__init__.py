# __init__.py
"""
Smart plugins package for AI-powered voice assistant.
Contains plugins for Windows programs, browser search, and system control.
"""

from .base_plugin import SmartPlugin
from .windows_programs import WindowsProgramsPlugin
from .browser_search import BrowserSearchPlugin
from .sound_control import SystemControlPlugin
from .quick_notes import QuickNotesPlugin
# Список всіх доступних плагінів
AVAILABLE_PLUGINS = [
    WindowsProgramsPlugin,
    BrowserSearchPlugin,
    SystemControlPlugin,
    QuickNotesPlugin
]

__all__ = [
    'SmartPlugin',
    'WindowsProgramsPlugin',
    'BrowserSearchPlugin',
    'SystemControlPlugin',
    'QuickNotesPlugin',
    'AVAILABLE_PLUGINS'
]