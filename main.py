import moviepy.editor as mp
from deep_translator import GoogleTranslator
import pyttsx3
import gradio as gr
import speech_recognition as sr
import os
import tempfile

# Определите путь для сохранения конечного видео
output_dir = os.path.expanduser("~/Desktop/VideoTranslatorOutput")
os.makedirs(output_dir, exist_ok=True)

def split_text(text, max_length=5000):
    """Разбивает текст на части с максимальной длиной max_length символов."""
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]


def extract_audio_text(videoclip, temp_dir):
    """Извлекает текст из аудиодорожки видеоклипа с помощью распознавания речи."""
    temp_audio_file = os.path.join(temp_dir, "extracted_audio.wav")
    videoclip.audio.write_audiofile(temp_audio_file, codec="pcm_s16le")

    # Преобразование аудио в текст
    r = sr.Recognizer()
    with sr.AudioFile(temp_audio_file) as source:
        audio = r.record(source)
        text = r.recognize_sphinx(audio)  # Используем Sphinx для оффлайн-распознавания

    return text


def translate_text(text, max_chars=4999):
    """Переводит текст с английского на русский, разбивая его на части, если он слишком длинный."""
    translator = GoogleTranslator(source="en", target="ru")
    text_parts = split_text(text, max_chars)
    translated_parts = [translator.translate(part) for part in text_parts]

    return ' '.join(translated_parts)


def synthesize_speech(text, temp_dir):
    """Синтезирует речь на русском языке из текста и возвращает путь к временному аудиофайлу."""
    temp_speech_file = os.path.join(temp_dir, "translated_speech.wav")
    engine = pyttsx3.init()
    engine.setProperty('voice', 'ru')
    engine.save_to_file(text, temp_speech_file)
    engine.runAndWait()

    return temp_speech_file


def video_to_translate(file_video):
    with tempfile.TemporaryDirectory() as local_temp_dir:

        videoclip = mp.VideoFileClip(file_video)

        extracted_text = extract_audio_text(videoclip, local_temp_dir)

        translated_text = translate_text(extracted_text)

        temp_speech_path = synthesize_speech(translated_text, local_temp_dir)

        audioclip = mp.AudioFileClip(temp_speech_path)
        videoclip = videoclip.set_audio(audioclip)

        output_video_path = os.path.join(output_dir, "translated_video.mp4")
        videoclip.write_videofile(output_video_path)

        return output_video_path

gr.Interface(fn=video_to_translate,
             inputs=[gr.Video(label="Upload Video")],
             outputs=gr.Video(),
             title='Video Translator'
             ).launch()
