# picfacebot
# Face Swapper Telegram Bot

This is a Telegram bot that applies face swapping to the provided images. It uses the [face_recognition](https://github.com/ageitgey/face_recognition) [roop](https://github.com/s0md3v/roop) for face detection and swapping.

## Getting Started
### Setting Up
Prerequisites
Python 3.10

1. Clone this repository.
```bash
git clone https://github.com/megagernan/picfacebot.git
```
2. Create venv and install dependencies
```bash
python -m venv picfacebotvenv
picfacebotvenv\Scripts\activate
cd picfacebot
pip install -r requirements.txt
```

3. Add your Telegram Bot API key in the `main()` function where indicated:

```python
updater = Updater("API_KEY")
```

### Running the Bot

```bash
python main.py
```

## Usage

1. Start a conversation with the bot by sending the `/start` command.

2. Follow the instructions to send a selfie.

3. The bot will process the image and reply with the result.

## Commands

- `/start`: Initiates a conversation with the bot.
- `/queue`: Checks the number of tasks in the processing queue.

## Important Notes

- The bot is designed to run continuously, processing tasks in the background.
- Target images for face swapping are randomly selected from the `target` directory.

## Customization

- You can customize the bot's behavior by modifying the Python code.

## Troubleshooting

- If you encounter any issues, refer to the logs in `bot.log` for debugging information.

## License

This project is licensed under the [MIT License](LICENSE).
