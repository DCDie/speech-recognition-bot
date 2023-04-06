import logging
import os
import uuid

import speech_recognition as sr
from aiogram import Bot, Dispatcher, executor, types
from dotenv import load_dotenv
from pydub import AudioSegment

load_dotenv()

logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv('BOT_API_TOKEN'))
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])  # Handles the "/start" command
async def start(message: types.Message):
    await bot.send_message(message.chat.id, text='Hi!')  # Sends a "Hi!" message


CONTENT_TYPES = {
    'voice': {
        'input': '.ogg',  # Telegram sends voice messages in the OGG format
        'output': '.wav',  # We'll convert them to WAV for transcription
    },
    'audio': {
        'input': '.mp3',
        'output': '.wav',
    },
    'video': {
        'input': '.mp4',
        'output': '.wav'
    },
    'video_note': {
        'input': '.mp4',
        'output': '.wav'
    },
}


async def convert_in_wav(message: types.Message):
    """
    Downloads the audio file from the message, converts it to WAV format and returns the name of the WAV file.

    Args:
        message (types.Message): Message object from Telegram

    Returns:
        str: Name of the WAV file without extension

    Example:
        >>> # assuming `message` contains an audio file
        >>> convert_in_wav(message)
        '82c7b30e-4680-4331-a07c-2799e8dfe85c'
    """
    if (content_type := message.content_type) in CONTENT_TYPES:
        # Prepare variables
        uuid_name = str(uuid.uuid4())  # Generate a random UUID for the downloaded file
        input = CONTENT_TYPES[content_type]["input"]
        output = CONTENT_TYPES[content_type]["output"]

        # Download file
        file_info = await bot.get_file(getattr(message, content_type).file_id)
        file = await bot.download_file(file_info.file_path)
        file_name = f'{uuid_name}{input}'
        with open(file_name, 'wb') as f:
            f.write(file.read())

        # Convert file to WAV
        AudioSegment.from_file(file_name).export(
            out_f=file_name.replace(input, output),
            format='wav'
        )

        return uuid_name


async def clean_files(uuid_name: str, content_type: str):
    """
    Deletes the downloaded and converted files.

    Args:
        uuid_name (str): Unique identifier for the downloaded file.
        content_type (str): Type of the input file, one of the keys in CONTENT_TYPES.

    Returns:
        None.

    Example:
        To delete the files with uuid_name '82c7b30e-4680-4331-a07c-2799e8dfe85c' and content_type 'voice':

        >>> await clean_files('82c7b30e-4680-4331-a07c-2799e8dfe85c', 'voice')
    """
    if content_type in CONTENT_TYPES:
        os.remove(f'{uuid_name}{CONTENT_TYPES[content_type]["input"]}')
        os.remove(f'{uuid_name}{CONTENT_TYPES[content_type]["output"]}')


async def recognize_speech(uuid_name: str) -> str:
    """
   Transcribe an audio file to text using Google's speech recognition API.

   Args:
       uuid_name (str): the UUID of the audio file to transcribe.

   Returns:
       text (str): the transcribed text from the audio file.

   Example:
       To transcribe an audio file named "test.wav" and get the transcribed text:

       >>> text = await recognize_speech('test')
   """
    r = sr.Recognizer()
    with sr.AudioFile(f'{uuid_name}.wav') as source:
        audio = r.record(source)
    try:
        text = r.recognize_google(audio, language='ru-RU')  # Transcribe audio using Google's speech recognition API
    except sr.UnknownValueError:
        text = 'Не удалось распознать речь'  # If the audio cannot be transcribed, return an error message
    return text


@dp.message_handler(content_types=[x for x in CONTENT_TYPES.keys()])  # Handles all other audio message types
async def transcribe_audio(message: types.Message):
    """
    Handles the incoming voice message, converts it to .wav format, transcribes the speech using
    Google's speech recognition API, deletes the temporary files, and sends a text message with the transcription.

    Args:
        message (telegram.types.Message): A Telegram message containing an audio file.

    Returns:
        None.

    Example:
        >>> # Sends an audio message to be transcribed
        >>> await transcribe_audio(message)
    """
    # Convert audio message to .wav
    uuid_name = await convert_in_wav(message)

    # Recognize voice message
    text = await recognize_speech(uuid_name)

    # Delete all files that start with uuid_name
    await clean_files(uuid_name, message.content_type)

    # Reply to audio message with transcription
    await bot.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_to_message_id=message.message_id
    )


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
