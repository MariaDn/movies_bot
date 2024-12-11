from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, CallbackContext
import telegram.ext.filters as filters
import requests
from dotenv import load_dotenv
import os
from openai import OpenAI
import logging

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
API_KEY = os.getenv('OPENAI_API_KEY')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

MOOD_GENRES = {
    'happy': 35,  # Comedy
    'sad': 18,    # Drama
    'excited': 28, # Action
    'scared': 27, # Horror
    'romantic': 10749 # Romance
}

def get_movie_recommendations(genre_id):
    url = f'https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&with_genres={genre_id}&sort_by=popularity.desc'
    response = requests.get(url)
    data = response.json()
    movies = data['results']
    recommendations = [f"<u><i>{movie['title']}</i></u> ({movie['release_date'][:4]}), rate: {movie['vote_average']}" for movie in movies[:5]]
    return recommendations

async def recommend(update, context):
    keyboard = [
        [InlineKeyboardButton("Happy", callback_data='happy')],
        [InlineKeyboardButton("Sad", callback_data='sad')],
        [InlineKeyboardButton("Excited", callback_data='excited')],
        [InlineKeyboardButton("Scared", callback_data='scared')],
        [InlineKeyboardButton("Romantic", callback_data='romantic')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('How are you feeling today?', reply_markup=reply_markup)

async def button(update, context):
    query = update.callback_query
    await query.answer()
    mood = query.data
    genre_id = MOOD_GENRES[mood]
    recommendations = get_movie_recommendations(genre_id)
    message = f"Here are some {mood} movies:\n" + "\n".join(recommendations)
    await query.edit_message_text(text=message, parse_mode='HTML')

async def handle_message(update, context):
    try:
        user_input = update.message.text
        logging.info(f"User input: {user_input}")
        client = OpenAI(api_key=API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides movie recommendations based on user input."},
                {"role": "user", "content": user_input}
            ]
        )
        recommendations = response.choices[0].message['content']
        await update.message.reply_text(recommendations)

    except Exception as e:
        logging.error(f"Error in handle_message: {e}")
        await update.message.reply_text("Sorry, something went wrong. Please try again later.")

async def unknown(update, context):
    await update.message.reply_text("Sorry, I didn't understand that command.")

async def start(update, context):
    await update.message.reply_text("Welcome! Type /recommend to get movie recommendations based on your mood.")

async def bye(update, context):
    await update.message.reply_text("Bye! Have a great day.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    start_handler = CommandHandler('start', start)
    bye_handler = CommandHandler('bye', bye)
    recommend_handler = CommandHandler('recommend', recommend)
    button_handler = CallbackQueryHandler(button)
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)

    application.add_handler(start_handler)
    application.add_handler(bye_handler)
    application.add_handler(recommend_handler)
    application.add_handler(button_handler)
    application.add_handler(message_handler)
    application.add_handler(unknown_handler)

    application.run_polling()

if __name__ == '__main__':
    main()