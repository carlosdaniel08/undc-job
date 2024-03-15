import telebot
import requests
from bs4 import BeautifulSoup
from telebot import types
import config  # Importa el archivo config.py

# Conexión con el bot
bot = telebot.TeleBot(config.TOKEN)

# Lista para almacenar los códigos de las convocatorias ya notificadas
convocatorias_notificadas = []

# Estado de la convocatoria
estado_convocatoria = None

# Número de registros a mostrar
num_registros = None

# Función para enviar notificación de nueva convocatoria con formato HTML
def enviar_notificacion(chat_id, mensaje):
    bot.send_message(chat_id, mensaje, parse_mode="HTML")

# Creación de comandos '/start', '/help' y '/borrar'

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "¡Hola! Soy el bot de Convocatoria de Bienes y Servicios de la UNDC")

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "Los comandos funcionales son '/start', '/help' y '/convocatoria'")

@bot.message_handler(commands=['convocatoria'])
def send_options(message):
    markup = types.InlineKeyboardMarkup(row_width=2)

    # Creación de botones
    btn_si = types.InlineKeyboardButton('Si', callback_data='notificaciones_si')
    btn_no = types.InlineKeyboardButton('No', callback_data='notificaciones_no')
    
    # Agregar botones al markup
    markup.add(btn_si, btn_no)

    # Enviar mensaje con botones
    bot.send_message(message.chat.id, "¿Desea recibir notificaciones de convocatorias?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global estado_convocatoria, num_registros
    
    if call.data == 'notificaciones_si':
        markup = types.InlineKeyboardMarkup(row_width=2)

        # Creación de botones
        btn_activas = types.InlineKeyboardButton('Convocatorias Activas', callback_data='activas')
        btn_todas = types.InlineKeyboardButton('Todas las Convocatorias', callback_data='todas')
        
        # Agregar botones al markup
        markup.add(btn_activas, btn_todas)

        # Enviar mensaje con botones
        bot.send_message(call.message.chat.id, "¿Desea recibir solo las convocatorias ACTIVAS o todas las convocatorias?", reply_markup=markup)

    elif call.data == 'activas':
        estado_convocatoria = 'Vigente'
        bot.send_message(call.message.chat.id, "Recibirá notificaciones de convocatorias activas")
        ask_for_num_records(call.message.chat.id)
        
    elif call.data == 'todas':
        estado_convocatoria = None
        bot.send_message(call.message.chat.id, "Recibirá notificaciones de todas las convocatorias")
        ask_for_num_records(call.message.chat.id)
        
    elif call.data.isdigit():
        num_registros = int(call.data)
        bot.send_message(call.message.chat.id, f"Recibirá {num_registros} registros")
        fetch_convocatorias(call.message.chat.id)

def ask_for_num_records(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)

    btn_25 = types.InlineKeyboardButton('25 registros', callback_data='25')
    btn_50 = types.InlineKeyboardButton('50 registros', callback_data='50')
    btn_75 = types.InlineKeyboardButton('75 registros', callback_data='75')
    btn_100 = types.InlineKeyboardButton('100 registros', callback_data='100')
    
    markup.add(btn_25, btn_50, btn_75, btn_100)

    bot.send_message(chat_id, "¿Cuántos registros desea recibir?", reply_markup=markup)

def fetch_convocatorias(chat_id):
    global convocatorias_notificadas
    
    url = "https://sistemas.undc.edu.pe/bienesyservicios/"
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        rows = soup.select("div.container table tbody tr")  # Buscar todas las filas de la tabla
        
        if rows:
            count = 0
            for index, row in enumerate(rows):
                if num_registros and count >= num_registros:
                    break
                codigo_elem = row.select_one("td:nth-of-type(1)")
                if codigo_elem:
                    codigo = codigo_elem.text.strip()

                    descripcion_elem = row.select_one("td:nth-of-type(2)")
                    descripcion = descripcion_elem.text.strip()

                    link_tdr_elem = row.select_one("td:nth-of-type(3) a")
                    link_tdr = link_tdr_elem['href'] if link_tdr_elem else "No disponible"

                    publicado_elem = row.select_one("td:nth-of-type(4)")
                    publicado = publicado_elem.text.strip()

                    vence_elem = row.select_one("td:nth-of-type(5)")
                    vence = vence_elem.text.strip()

                    estado_elem = row.select_one("td:nth-of-type(6) span")
                    estado = estado_elem.text.strip()

                    if estado_convocatoria and estado != estado_convocatoria:
                        continue

                    link_trabajo = f"https://sistemas.undc.edu.pe/bienesyservicios/?pub={codigo}"

                    mensaje = f"<b>Código del bien/servicio:</b> {codigo}\n\n"\
                                f"<b>Descripción:</b> {descripcion}\n"\
                                f"<b>Link del TDR:</b> <a href='{link_tdr}'>{link_tdr}</a>\n"\
                                f"<b>Publicado:</b> {publicado}\n"\
                                f"<b>Vence:</b> {vence}\n"\
                                f"<b>Estado:</b> {estado}\n"\
                                f"<b>Link de trabajo:</b> <a href='{link_trabajo}'>{link_trabajo}</a>"

                    if codigo not in convocatorias_notificadas:
                        enviar_notificacion(chat_id, mensaje)
                        convocatorias_notificadas.append(codigo)

                    count += 1
                else:
                    bot.send_message(chat_id, "No se encontraron los datos de la convocatoria en la página.")
        else:
            bot.send_message(chat_id, "No se encontraron filas en la tabla de datos en la página.")
    else:
        bot.send_message(chat_id, f"Error al obtener la página: {response.status_code}")

if __name__ == '__main__':
    bot.polling(none_stop=True)
