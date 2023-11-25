import os
from pathlib import Path
import subprocess
from bookscraper import read_next_post, confirm_post_read
from openai import OpenAI
import logging

# Read api key from .env
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def read_book(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def chunk_text(input_text, max_length=4096):
    cleaned_text = input_text.replace('[', '').replace(']', '')
    paragraphs = cleaned_text.split('\n\n')
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        paragraph += '\n\n'
        if len(current_chunk) + len(paragraph) <= max_length:
            current_chunk += paragraph
        else:
            chunks.append(current_chunk)
            current_chunk = paragraph
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def generate_audio(chunk, index, temp_folder):
    speech_file_path = temp_folder / f"chunk_{index}.mp3"
    if not speech_file_path.exists():  # Generate audio only if file doesn't exist
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice="nova",
            speed=1,
            input=chunk
        )
        response.stream_to_file(speech_file_path)
    return speech_file_path

def combine_audio(files, output_path):
    command = ["ffmpeg", "-y", "-i", "concat:" + "|".join(files), "-acodec", "copy", output_path]
    subprocess.run(command, check=True)

def main(posts_filename, file_path = None):
    if file_path is None and posts_filename is not None:
        result = read_next_post(posts_filename)
    elif file_path is not None:
        result = file_path, read_book(file_path)
    else:
        raise Exception("No file path or posts filename provided")
    if result is None:
        logging.info("No more posts to read")
        return
    filename, book_text = result

    logging.info(f"Read {len(book_text)} characters")

    temp_folder = Path(__file__).parent / "temp_audio_files"
    temp_folder.mkdir(exist_ok=True)  # Create the temp folder if it doesn't exist

    chunks = chunk_text(book_text)
    logging.info(f"Generated {len(chunks)} chunks")
    audio_files = []

    for index, chunk in enumerate(chunks):
        audio_path = generate_audio(chunk, index, temp_folder)
        audio_files.append(str(audio_path))

    # get title from filename

    title = '_'.join(str(filename).split('/')[-1].split('.')[0].split('_')[1:])
    combined_audio_path = Path(__file__).parent / "combined_audio_files"
    combined_audio_path.mkdir(exist_ok=True)
    combined_audio_file = combined_audio_path / f"{title}.mp3"
    combine_audio(audio_files, str(combined_audio_file))

    # # Optionally, clean up individual chunk files
    for file in audio_files:
        os.remove(file)
    
    confirm_post_read(filename, book_text)

if __name__ == "__main__":
    # main('book.txt') # override default behavior
    # main(posts_filename="fetchdata/filtered_posts_demoness.json")
    main(posts_filename="fetchdata/filtered_posts_elydes.json")