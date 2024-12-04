import telebot
import requests
from PIL import Image
import base64
from io import BytesIO
from flask import Flask, redirect, url_for
import threading
import time

# Token bot Telegram
TOKEN = '6324930447:AAEK_w2_6XELCbkpVLwPN0_Sm4pfaZYv1G0'
bot = telebot.TeleBot(TOKEN)

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# Fungsi untuk konversi gambar dari URL ke base64
def convert_image_from_url_to_base64(url):
    response = requests.get(url)
    response.raise_for_status()
    
    img = Image.open(BytesIO(response.content))
    img = img.convert("RGB")
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return img_base64

# Fungsi untuk mengirim request OCR ke API model
def ocr_image(image_base64):
    payload = {
        "model": "models/gemini-1.5-flash",
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_base64
                        }
                    },
                    {
                        "text": "Identify and extract all text visible"
                
             
                    }
                ]
            }
        ]
    }

    headers = {
        "Host": "generativelanguage.googleapis.com",
        "x-goog-api-key": "AIzaSyDmc-buN5VJotwI2MR732DM_cZQEhHIlmo",
        "x-goog-api-client": "genai-android/0.9.0",
        "accept": "application/json",
        "accept-charset": "UTF-8",
        "user-agent": "Ktor client",
        "content-type": "application/json",
        "accept-encoding": "gzip"
    }

    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
        json=payload,
        headers=headers
    )
    print(response.text)
    if response.status_code == 200:
        
        json_response = response.json()
        candidates = json_response.get('candidates', [])
        if candidates:
            content_parts = candidates[0].get('content', {}).get('parts', [])
            if content_parts:
                return content_parts[0].get('text', '')
        return "Tidak ada teks yang ditemukan di gambar."
    else:
        return "Error: Gagal melakukan OCR."

# Handler untuk perintah /ocr
@bot.message_handler(commands=['ocr'])
def handle_ocr_command(message):
    if message.chat.type in ['group', 'supergroup']:
        if message.reply_to_message and message.reply_to_message.photo:
            # Gambar dibalas, proses gambar
            try:
                processing_message = bot.reply_to(message, "Sedang memproses gambar, harap tunggu...")
                
                file_info = bot.get_file(message.reply_to_message.photo[-1].file_id)
                file_url = f'https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}'
                image_base64 = convert_image_from_url_to_base64(file_url)
                
                # Lakukan OCR pada gambar
                result_text = ocr_image(image_base64)
                
                # Kirim hasil OCR ke user dan hapus pesan proses
                bot.edit_message_text(result_text, chat_id=message.chat.id, message_id=processing_message.message_id)
            
            except Exception as e:
                bot.reply_to(message, f"Terjadi kesalahan: {str(e)}")
        else:
            pass
    else:
        bot.reply_to(message, "Kirim gambar atau URL gambar yang ingin di-OCR.")

# Handler untuk gambar yang dikirimkan oleh user
@bot.message_handler(content_types=['photo'])
def handle_image(message):
    if message.chat.type == 'private':
        try:
            processing_message = bot.reply_to(message, "Sedang memproses gambar, harap tunggu...")
            
            file_info = bot.get_file(message.photo[-1].file_id)
            file_url = f'https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}'
            image_base64 = convert_image_from_url_to_base64(file_url)
            
            # Lakukan OCR pada gambar
            result_text = ocr_image(image_base64)
            
            # Kirim hasil OCR ke user dan hapus pesan proses
            bot.edit_message_text(result_text, chat_id=message.chat.id, message_id=processing_message.message_id)
        
        except Exception as e:
            bot.reply_to(message, f"Terjadi kesalahan: {str(e)}")
    # Di grup, tidak perlu menangani gambar langsung, cukup menangani balasan gambar dengan perintah /ocr
    # Untuk gambar yang dikirim langsung di grup, user harus membalas gambar dengan perintah /ocr

# Handler untuk URL gambar yang dikirimkan oleh user
@bot.message_handler(func=lambda message: message.text and message.text.startswith('http'))
def handle_link(message):
    if message.chat.type == 'private':
        try:
            processing_message = bot.reply_to(message, "Sedang memproses URL gambar, harap tunggu...")
            
            # Ambil URL dari pesan
            image_url = message.text
            image_base64 = convert_image_from_url_to_base64(image_url)
            
            # Lakukan OCR pada gambar
            result_text = ocr_image(image_base64)
            
            # Kirim hasil OCR ke user dan hapus pesan proses
            bot.edit_message_text(result_text, chat_id=message.chat.id, message_id=processing_message.message_id)
        
        except Exception as e:
            bot.reply_to(message, f"Terjadi kesalahan: {str(e)}")
    elif message.chat.type in ['group', 'supergroup']:
        pass

# Endpoint Flask sederhana untuk pengalihan
@app.route('/')
def index():
    return "Hello World! This is a simple redirect page."

@app.route('/redirect')
def redirect_page():
    return redirect(url_for('index'))

# Fungsi untuk menjalankan Flask di thread terpisah
def run_flask():
    app.run(host='0.0.0.0', port=3000)

# Fungsi untuk menjalankan bot Telegram dengan mekanisme restart otomatis
def run_bot():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Bot berhenti dengan error: {e}")
            time.sleep(1)  # Tunggu sebelum mencoba polling lagi

# Main
if __name__ == '__main__':
    # Buat thread terpisah untuk Flask dan bot
    flask_thread = threading.Thread(target=run_flask)
    bot_thread = threading.Thread(target=run_bot)

    # Set daemon untuk otomatis berhenti saat aplikasi utama dihentikan
    flask_thread.daemon = True
    bot_thread.daemon = True

    # Jalankan keduanya
    flask_thread.start()
    bot_thread.start()

    # Menunggu kedua thread selesai
    flask_thread.join()
    bot_thread.join()
