"""Safe printing für EXE-Versionen ohne Unicode-Fehler"""
import sys
import logging

def safe_print(message: str, logger=None):
    """Sicheres Printing das Unicode-Fehler verhindert"""
    try:
        # Emoji durch ASCII ersetzen für Console
        safe_message = message.replace('✅', '[OK]').replace('❌', '[ERROR]').replace('🔄', '[PROCESSING]').replace('🤖', '[AI]').replace('🎵', '[AUDIO]')
        
        # Versuche normales Print
        print(safe_message)
        
        # Optional auch ins Log
        if logger:
            logger.info(safe_message)
            
    except UnicodeEncodeError:
        # Fallback: Nur ASCII-Zeichen
        ascii_message = message.encode('ascii', errors='replace').decode('ascii')
        print(ascii_message)
        if logger:
            logger.info(ascii_message)

def get_safe_emoji(emoji_char: str) -> str:
    """Gibt sicheren ASCII-Ersatz für Emojis zurück"""
    emoji_map = {
        '✅': '[OK]',
        '❌': '[ERROR]', 
        '🔄': '[PROCESSING]',
        '🤖': '[AI]',
        '🎵': '[AUDIO]',
        '⚠️': '[WARNING]'
    }
    return emoji_map.get(emoji_char, '[?]')
