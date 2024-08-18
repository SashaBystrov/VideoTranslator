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
OUTPUT_VIDEO_DIR = os.path.expanduser("~/Desktop/VideoTranslator")
os.makedirs(OUTPUT_VIDEO_DIR, exist_ok=True)

# Создание временных директорий
TEMP_DIR_LOCAL = tempfile.mkdtemp(prefix="video_translator_")
TEMP_DIR_GRADIO = "C:\\Users\\De1pl\\AppData\\Local\\Temp\\gradio"


def split_text(text, max_length=5000):
    """Разбивает текст на части с максимальной длиной max_length символов.

    Args:
        text: Текст для разделения.
        max_length: Максимальная длина каждой части текста.

    Returns:
        list: Список частей текста.
    """
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]


def extract_audio_text(videoclip, temp_dir):
    """Распознает речь из аудиодорожки.

    Args:
        videoclip: Видеоклип, из которого будет извлекаться аудио.
        temp_dir: Временная директория для сохранения аудиофайла.

    Returns:
        str: Распознанный текст.
    """
    try:
        temp_audio_file = os.path.join(temp_dir, "extracted_audio.wav")
        videoclip.audio.write_audiofile(temp_audio_file, codec="pcm_s16le")

        r = sr.Recognizer()
        with sr.AudioFile(temp_audio_file) as source:
            audio = r.record(source)
            text = r.recognize_sphinx(audio)

        return text

    except ValueError as e:
        raise ValueError(f"Ошибка при распознавании текста: {e}")
    except RuntimeError as e:
        raise RuntimeError(f"Ошибка при распознавании текста:  {e}")

def translate_text(text, max_chars=4999):
    """Переводит текст с английского на русский.

    Args:
        text: Текст для перевода.
        max_chars: Максимальное количество символов для одного запроса к переводчику.

    Returns:
        str: Переведенный текст.
    """
    try:
        translator_obj = GoogleTranslator(source="en", target="ru")
        text_parts = split_text(text, max_chars)
        translated_parts = [translator_obj.translate(part) for part in text_parts]

        return ' '.join(translated_parts)

    except ValueError as e:
        raise ValueError(f"Ошибка при переводе текста: {e}")
    except RuntimeError as e:
        raise RuntimeError(f"Ошибка при переводе текста:  {e}")

def synthesize_speech(text, temp_dir):
    """Синтезирует речь на русском языке из текста и сохраняет в аудиофайл.

    Args:
        text: Текст для синтеза речи.
        temp_dir: Временная директория для сохранения аудиофайла.

    Returns:
        str: Путь к сохраненному аудиофайлу.
    """
    try:
        temp_speech_file = os.path.join(temp_dir, "translated_speech.wav")
        engine_obj = pyttsx3.init()
        engine_obj.setProperty('voice', 'ru')
        engine_obj.save_to_file(text, temp_speech_file)
        engine_obj.runAndWait()

        return temp_speech_file

    except ValueError as e:
        raise ValueError(f"Ошибка при синтезе речи: {e}")
    except RuntimeError as e:
        raise RuntimeError(f"Ошибка при синтезе речи:  {e}")

def create_text_clip(text, start_time, end_time, font_size=28, color='white', bg_color='black',
                     position=('center', 0.7)):
    """Создает текстовый клип для видео с помощью библиотеки MoviePy.

    Args:
        text (str): Текст, который будет отображен на клипе.
        start_time (float): Время начала отображения текста в секундах.
        end_time (float): Время окончания отображения текста в секундах.
        font_size (int, optional): Размер шрифта текста. По умолчанию 28.
        color (str, optional): Цвет текста. По умолчанию белый.
        bg_color (str, optional): Цвет фона текста. По умолчанию черный.
        position (tuple, optional): Позиция текста на кадре в виде кортежа (горизонтальная позиция, вертикальная позиция).
            Горизонтальная позиция может быть числом от 0 до 1 (0 - левый край, 1 - правый край) или строкой ('left', 'center', 'right').
            Вертикальная позиция может быть числом от 0 до 1 (0 - верхний край, 1 - нижний край). По умолчанию ('center', 0.7).

    Returns:
        mp.TextClip: Объект текстового клипа, готовый для добавления в видео.
    """

    return mp.TextClip(text, fontsize=font_size, color=color, bg_color=bg_color) \
        .set_position(position) \
        .set_duration(end_time - start_time) \
        .set_start(start_time)


def add_subtitles_to_video_with_pysubs2(video_path, subtitles_path, output_video_path):
    """Добавляет субтитры к видео с использованием библиотек pysubs2 и moviepy.

    Args:
        video_path (str): Путь к исходному видеофайлу.
        subtitles_path (str): Путь к файлу с субтитрами в формате SRT.
        output_video_path (str): Путь для сохранения результирующего видеофайла с субтитрами.

    Returns:
        None: Функция сохраняет результат в указанный файл.
    """
    try:
        videoclip = mp.VideoFileClip(video_path)
        subs = pysubs2.load(subtitles_path)

        subtitles = []
        for line in subs:
            start_time = line.start / 1000  # Время начала субтитров в секундах
            end_time = line.end / 1000  # Время конца субтитров в секундах
            text_clip = create_text_clip(line.text, start_time, end_time)
            subtitles.append(text_clip)

        composite = mp.CompositeVideoClip([videoclip] + subtitles)
        composite.write_videofile(output_video_path, codec='libx264', audio_codec='aac')

    except ValueError as e:
        raise ValueError(f"Ошибка при добавлении субтитров: {e}")
    except RuntimeError as e:
        raise RuntimeError(f"Непредвиденная ошибка: {e}")


def translate_video(file_video):
    """Переводит видео: извлекает аудио, переводит на русский язык, синтезирует речь и заменяет оригинальную аудиодорожку.

    Args:
        file_video (str): Путь к исходному видеофайлу.

    Returns:
        str: Путь к переведенному видеофайлу.
    """
    try:
        videoclip = mp.VideoFileClip(file_video)

        # Извлечение аудио и текста
        extracted_text = extract_audio_text(videoclip, TEMP_DIR_LOCAL)

        # Перевод текста
        translated_text = translate_text(extracted_text)

        # Синтез речи
        temp_speech_path = synthesize_speech(translated_text, TEMP_DIR_LOCAL)

        # Замена аудио в видеоклипе
        audioclip = mp.AudioFileClip(temp_speech_path)
        videoclip = videoclip.set_audio(audioclip)

        # Сохранение переведенного видео в указанную директорию
        video_name = os.path.splitext(os.path.basename(file_video))[0]
        output_video_path = os.path.join(OUTPUT_VIDEO_DIR, f"{video_name}_translated.mp4")
        videoclip.write_videofile(output_video_path, codec='libx264', audio_codec='aac')

        # Закрытие клипов после использования
        audioclip.close()
        videoclip.close()

        return output_video_path

    except FileNotFoundError:
        raise FileNotFoundError(f"Файл видео '{file_video}' не найден.")
    except ValueError as e:
        raise ValueError(f"Ошибка при обработке видео: {e}")
    except RuntimeError as e:
        raise RuntimeError(f"Непредвиденная ошибка: {e}")

    finally:
        shutil.rmtree(TEMP_DIR_LOCAL)
        shutil.rmtree(TEMP_DIR_GRADIO)



def add_subtitles_to_video(file_video, file_srt):
    """Добавляет субтитры к существующему видеофайлу.

    Args:
        file_video (str): Путь к исходному видеофайлу.
        file_srt (str): Путь к файлу с субтитрами в формате SRT.

    Returns:
        str: Путь к видеофайлу с добавленными субтитрами.
    """
    try:
        video_name = os.path.splitext(os.path.basename(file_video))[0]
        output_video_path = os.path.join(OUTPUT_VIDEO_DIR, f"{video_name}_with_subs.mp4")

        # Добавление субтитров с использованием pysubs2 и moviepy
        add_subtitles_to_video_with_pysubs2(file_video, file_srt, output_video_path)

        return output_video_path
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл видеозаписи или srt-файл '{file_video}' или '{file_srt}' не найден.")

    finally:
        shutil.rmtree(TEMP_DIR_LOCAL)
        shutil.rmtree(TEMP_DIR_GRADIO)


def translate_video_with_subtitles(file_video, file_srt):
    """Переводит видео: извлекает аудио, переводит на русский язык, синтезирует речь и заменяет оригинальную аудиодорожку.

    Args:
        file_video (str): Путь к исходному видеофайлу.
        file_srt (str): Путь к .srt файлу.
    Returns:
        str: Путь к переведенному видеофайлу.
    """
    try:
        translated_video_path = translate_video(file_video)
        return add_subtitles_to_video(translated_video_path, file_srt)

    except FileNotFoundError:
        raise FileNotFoundError(f"Файл видеозаписи или srt-файл '{file_video}' или '{file_srt}' не найден.")


def process_video(file_video, file_srt=None, operation="Translate"):
    """Обрабатывает видео: перевод, добавление субтитров или и то, и другое.

        Args:
            file_video: Путь к видеофайлу.
            file_srt: Путь к файлу с субтитрами (необязательно).
            operation: Операция, которую необходимо выполнить (перевод, добавление субтитров или оба).

        Returns:
            str: Путь к обработанному видеофайлу.
        """
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
