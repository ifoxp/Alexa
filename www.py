import edge_tts
import asyncio
import io
import pygame

VOICE = "uk-UA-OstapNeural"
RATE = "+40%"  # Експериментуй тут: +30%, +50% тощо

async def speak(text):
    # Додаємо параметр rate
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
    
    audio_stream = io.BytesIO()
    
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_stream.write(chunk["data"])
    
    audio_stream.seek(0)
    
    pygame.mixer.init()
    pygame.mixer.music.load(audio_stream)
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

if __name__ == "__main__":
    text = "Систему прискорено. Тепер я говорю значно динамічніше, сер."
    asyncio.run(speak(text))