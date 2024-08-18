import os
import tempfile
import shutil
from deep_translator import GoogleTranslator
import pyttsx3
import gradio as gr
import speech_recognition as sr
import moviepy.editor as mp
import pysubs2

# Создание директорий для хранения видео
output_video_dir = os.path.expanduser("~/Desktop/VideoTranslator")
os.makedirs(output_video_dir, exist_ok=True)

# Создание временных директорий
temp_dir_local = tempfile.mkdtemp(prefix="video_translator_")
temp_dir_gradio = "C:\\Users\\De1pl\\AppData\\Local\\Temp\\gradio"


def split_text(text, max_length=5000):
    """Разбивает текст на части с максимальной длиной max_length символов."""
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

def extract_audio_text(videoclip, temp_dir):
    """Извлекает текст из аудиодорожки видеоклипа с помощью распознавания речи."""
    temp_audio_file = os.path.join(temp_dir, "extracted_audio.wav")
    videoclip.audio.write_audiofile(temp_audio_file, codec="pcm_s16le")

    r = sr.Recognizer()
    with sr.AudioFile(temp_audio_file) as source:
        audio = r.record(source)
        text = r.recognize_sphinx(audio)

    return text


def translate_text(text, max_chars=4999):
    """Переводит текст с английского на русский, разбивая его на части, если он слишком длинный."""
    translator_obj = GoogleTranslator(source="en", target="ru")
    text_parts = split_text(text, max_chars)
    translated_parts = [translator_obj.translate(part) for part in text_parts]

    return ' '.join(translated_parts)


def synthesize_speech(text, temp_dir):
    """Синтезирует речь на русском языке из текста и возвращает путь к временному аудиофайлу."""
    temp_speech_file = os.path.join(temp_dir, "translated_speech.wav")
    engine_obj = pyttsx3.init()
    engine_obj.setProperty('voice', 'ru')
    engine_obj.save_to_file(text, temp_speech_file)
    engine_obj.runAndWait()

    return temp_speech_file


def add_subtitles_to_video_with_pysubs2(video_path, subtitles_path, output_video_path):
    """Добавляет субтитры к видео с использованием pysubs2 и moviepy."""
    videoclip = mp.VideoFileClip(video_path)
    subs = pysubs2.load(subtitles_path)

    def create_text_clip(text, start_time, end_time):
        """Создает текстовый клип для MoviePy."""
        return mp.TextClip(text, fontsize=28, color='white', bg_color='black').set_position(
            ('center', 0.7)).set_duration(end_time - start_time).set_start(start_time)

    subtitles = []
    for line in subs:
        start_time = line.start / 1000  # Время начала субтитров в секундах
        end_time = line.end / 1000  # Время конца субтитров в секундах
        text_clip = create_text_clip(line.text, start_time, end_time)
        subtitles.append(text_clip)

    composite = mp.CompositeVideoClip([videoclip] + subtitles)
    composite.write_videofile(output_video_path, codec='libx264', audio_codec='aac')


def translate_video(file_video):
    """Переводит видео и заменяет аудиодорожку на синтезированную."""
    try:
        videoclip = mp.VideoFileClip(file_video)

        # Извлечение аудио и текста
        extracted_text = extract_audio_text(videoclip, temp_dir_local)

        # Перевод текста
        translated_text = translate_text(extracted_text)

        # Синтез речи
        temp_speech_path = synthesize_speech(translated_text, temp_dir_local)

        # Замена аудио в видеоклипе
        audioclip = mp.AudioFileClip(temp_speech_path)
        videoclip = videoclip.set_audio(audioclip)

        # Сохранение переведенного видео в указанную директорию
        video_name = os.path.splitext(os.path.basename(file_video))[0]
        output_video_path = os.path.join(output_video_dir, f"{video_name}_translated.mp4")
        videoclip.write_videofile(output_video_path, codec='libx264', audio_codec='aac')

        # Закрытие клипов после использования
        audioclip.close()
        videoclip.close()

        return output_video_path

    finally:
        shutil.rmtree(temp_dir_local)
        shutil.rmtree(temp_dir_gradio)


def add_subtitles_to_video(file_video, file_srt):
    """Добавляет субтитры к существующему видео."""
    try:
        video_name = os.path.splitext(os.path.basename(file_video))[0]
        output_video_path = os.path.join(output_video_dir, f"{video_name}_with_subs.mp4")

        # Добавление субтитров с использованием pysubs2 и moviepy
        add_subtitles_to_video_with_pysubs2(file_video, file_srt, output_video_path)

        return output_video_path

    finally:
        shutil.rmtree(temp_dir_local)
        shutil.rmtree(temp_dir_gradio)


def translate_video_with_subtitles(file_video, file_srt):
    """Переводит видео и добавляет субтитры к переведенному видео."""
    translated_video_path = translate_video(file_video)
    return add_subtitles_to_video(translated_video_path, file_srt)

def process_video(file_video, file_srt=None, operation="Translate"):
    if operation == "Translate":
        return translate_video(file_video)
    elif operation == "Add Subtitles":
        return add_subtitles_to_video(file_video, file_srt)
    elif operation == "Translate and Add English Subtitles":
        return translate_video_with_subtitles(file_video, file_srt)

gr.Interface(
    fn=process_video,
    inputs=[
        gr.Video(label="Upload Video"),
        gr.File(label="Upload SRT File (Optional)"),
        gr.Radio(["Translate", "Add Subtitles", "Translate and Add English Subtitles"], label="Operation",
                 value="Translate Only")
    ],
    outputs=gr.Video(),
    title='Video Processor: Translation and Subtitles'
).launch()