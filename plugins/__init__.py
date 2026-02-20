# __init__.py
"""
Smart plugins package for AI-powered voice assistant.
Contains plugins for:
- Windows programs and applications
- Browser search and YouTube control
- Music control (Spotify, YouTube Music)
- Movie/anime recommendations with GPT
- News reading with GPT summaries
- Entertainment (jokes, facts) with GPT generation
- System sound control
- Quick notes
"""

from .base_plugin import SmartPlugin
from .windows_programs import WindowsProgramsPlugin
from .browser_search import BrowserSearchPlugin
from .sound_control import SystemControlPlugin
from .quick_notes import QuickNotesPlugin
from .music_control import MusicControlPlugin
from .movie_recommendations import MovieRecommendationsPlugin
from .news_reader import NewsReaderPlugin
from .entertainment import EntertainmentPlugin

# Список всіх доступних плагінів
AVAILABLE_PLUGINS = [
    WindowsProgramsPlugin,
    BrowserSearchPlugin,
    SystemControlPlugin,
    QuickNotesPlugin,
    MusicControlPlugin,
    MovieRecommendationsPlugin,
    NewsReaderPlugin,
    EntertainmentPlugin
]

__all__ = [
    'SmartPlugin',
    'WindowsProgramsPlugin',
    'BrowserSearchPlugin',
    'SystemControlPlugin',
    'QuickNotesPlugin',
    'MusicControlPlugin',
    'MovieRecommendationsPlugin',
    'NewsReaderPlugin',
    'EntertainmentPlugin',
    'AVAILABLE_PLUGINS'
]