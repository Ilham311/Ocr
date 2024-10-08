import telebot
import requests
from PIL import Image
import base64
from io import BytesIO

# Token bot Telegram
TOKEN = '7342220709:AAEyZVJPKuy6w_N9rwrVW3GghYyxx3jixww'
bot = telebot.TeleBot(TOKEN)

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
                        "text": "Gambar ini jadikan text tanpa adanya komentar # dan tanpa penbalan text **"
                    }
                ]
            }
        ]
    }

    headers = {
        "Host": "generativelanguage.googleapis.com",
        "x-goog-api-key": "AIzaSyDTsv7eS31kT3LsvoiuYNe_Le0DGpubJaM",
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
# Mulai bot
bot.polling()
