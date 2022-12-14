import logging
import os
import uuid

import speech_recognition as sr
from aiogram import Bot, Dispatcher, executor, types
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv('BOT_API_TOKEN'))
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await bot.send_message(message.chat.id, text='Hi!')


CONTENT_TYPES = {
    'voice': {
        'input': '.ogg',
        'output': '.wav',
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
    if (content_type := message.content_type) in CONTENT_TYPES:
        # Prepare variables
        uuid_name = str(uuid.uuid4())
        input = CONTENT_TYPES[content_type]["input"]
        output = CONTENT_TYPES[content_type]["output"]

        # Download file
        file_info = await bot.get_file(getattr(message, content_type).file_id)
        file = await bot.download_file(file_info.file_path)
        file_name = f'{uuid_name}{input}'
        with open(file_name, 'wb') as f:
            f.write(file.read())
        AudioSegment.from_file(file_name).export(
            out_f=file_name.replace(input, output),
            format='wav'
        )
        return uuid_name


async def clean_files(uuid_name: str, content_type: str):
    if content_type in CONTENT_TYPES:
        os.remove(f'{uuid_name}{CONTENT_TYPES[content_type]["input"]}')
        os.remove(f'{uuid_name}{CONTENT_TYPES[content_type]["output"]}')


async def recognize_speech(uuid_name: str):
    r = sr.Recognizer()
    with sr.AudioFile(f'{uuid_name}.wav') as source:
        audio = r.record(source)
    try:
        text = r.recognize_google(audio, language='ru-RU')
    except sr.UnknownValueError:
        text = 'Не удалось распознать речь'
    return text


@dp.message_handler(content_types=[x for x in CONTENT_TYPES.keys()])
async def transcribe_audio(message: types.Message):
    # Convert vmessage to .wav
    uuid_name = await convert_in_wav(message)

    # Recognize voice message
    text = await recognize_speech(uuid_name)

    # Delete all files that start with file_name
    await clean_files(uuid_name, message.content_type)

    # Reply to voice message
    await bot.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_to_message_id=message.message_id
    )


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
