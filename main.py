import os
import logging
import queue
import threading
import traceback
import face_recognition
import random
import uuid
import subprocess
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


logging.basicConfig(filename='bot.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

task_queue = queue.Queue()
user_tasks = {}
user_progress = {}

SELECTING_IMAGE = 1

def create_directories():
    directories = ['target', 'source', 'output']
    [os.makedirs(directory, exist_ok=True) for directory in directories]

def start(update: Update, _: CallbackContext) -> None:
    update.message.reply_text('Hello, lets find out what kind of office worker you are!! Send a selfie! 🤪👔🧑‍💻👩‍💻📊👩‍💼📈')
    user_progress[update.effective_chat.id] = {'source': None}

def check_queue(update: Update, _: CallbackContext) -> None:
    queue_size = task_queue.qsize()
    update.message.reply_text(f'In the general queue {queue_size} tasks.')

def detect_faces(image_path: str) -> bool:
    try:
        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)
        return len(face_locations) > 0
    except Exception as e:
        logging.error(f'Error detecting faces: {e}')
        traceback.print_exc()
        return False

def get_and_check_image(update: Update, queue_key: str) -> str:
    chat_id = update.effective_chat.id
    image_path = f'{queue_key}/{chat_id}_{str(uuid.uuid4())}.jpg'
    update.message.photo[-1].get_file().download(image_path)

    if not detect_faces(image_path):
        update.message.reply_text(f"Oh no, it seems there is no face detected in the photo!😱😱😱 Please send another photo.😎")
        os.remove(image_path)  # Delete the image if it does not contain faces
        raise ValueError("No faces found in the image.")

    return image_path

def reset_user_progress(chat_id: int) -> None:
    user_progress.pop(chat_id, None)

def receive_image(update: Update, _: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_data = user_progress.get(chat_id, {'source': None})  # Initialize with default value
    queue_key = 'source'
    image_path = get_and_check_image(update, queue_key)

    user_data[queue_key] = image_path
    user_progress[chat_id] = user_data

    # If source image is collected, start processing
    if user_data['source']:
        queue_size = task_queue.qsize()
        task_index = queue_size  # The index of the task in the queue is the current size of the queue
        update.message.reply_text(f'Photo accepted. There are {queue_size + 1} tasks in the general queue. Your queue position: {task_index + 1}')

        # Add the task to the queue along with the task index
        task_queue.put((update, chat_id, user_data['source'], task_index))

        return


def send_result_image(update: Update, output_image_path: str, source_image_path: str) -> None:
    update.message.reply_text('Done!💋🙈😎😜 This is the result, you are such a cool office worker!')
    update.message.reply_photo(photo=open(output_image_path, 'rb'))

    queue_size = task_queue.qsize()
    update.message.reply_text(f'The process is complete. There are {queue_size} tasks left in the queue. Want more? Send a photo. 💋🙈😎😜')

    # Удаляем временные файлы после отправки результата
    cleanup_files(source_image_path, output_image_path)

def process_image_from_queue(update: Update, chat_id: int, source_image_path: str, task_id: str) -> None:
    try:
        output_image_path = f'output/{chat_id}_{task_id}.jpg'
        frame_processor = 'face_swapper'

        command = f'python run.py --target "{random_target_image_path()}" --source "{source_image_path}" -o "{output_image_path}" --frame-processor {frame_processor}'
        try:
            subprocess.run(command, shell=True, check=True, capture_output=True)
            if os.path.exists(output_image_path):
                send_result_image(update, output_image_path, source_image_path)  # Pass the source image path
                reset_user_progress(chat_id)  # Reset user progress after processing is done
                # Remove the specific task files after processing
                cleanup_files(source_image_path, output_image_path)
            else:
                update.message.reply_text('An error occurred while processing the image.😥 Please start again.')
        except subprocess.CalledProcessError as e:
            logging.error(f'Error processing images: {e}')
            traceback.print_exc()
            update.message.reply_text('An error occurred while processing the image.😥 Please start again.')
    except Exception as e:
        logging.error(f'Error processing source image: {e}')
        traceback.print_exc()

def random_target_image_path():
    target_dir = "target"
    target_images = [os.path.join(target_dir, file_name) for file_name in os.listdir(target_dir)]
    return random.choice(target_images)

def process_queue():
    while True:
        task = task_queue.get()
        update, chat_id, source_image_path, task_index = task
        task_id = str(uuid.uuid4())  
        user_tasks[chat_id] = task_index 
        process_image_from_queue(update, chat_id, source_image_path, task_id)
        task_queue.task_done()

def cleanup_files(*file_paths):
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)

def initialize_bot():
    task_queue.queue.clear()
    user_tasks.clear()

    source_dir = "source"
    output_dir = "output"

    for file_name in os.listdir(source_dir):
        file_path = os.path.join(source_dir, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)

    for file_name in os.listdir(output_dir):
        file_path = os.path.join(output_dir, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)

def main() -> None:
    create_directories()

    initialize_bot()

    updater = Updater("API_KEY")

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("queue", check_queue))
    dispatcher.add_handler(MessageHandler(Filters.photo & ~Filters.command, receive_image))

    # Start a separate thread to process the queue
    queue_processor_thread = threading.Thread(target=process_queue)
    queue_processor_thread.start()

    updater.start_polling()
    logging.info('Bot is running...')
    updater.idle()

if __name__ == '__main__':
    main()
