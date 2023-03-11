import vk_api
from vkbottle import API
from vkbottle.bot import Bot
import multiprocessing, threading # Добавить многопоточность
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import time
from get_mail import search_imap
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, mapped_column, Mapped


class Base(DeclarativeBase):
    pass


class Person(Base):
    __tablename__ = "people"

    vkid: Mapped[int] = mapped_column(primary_key=True)
    firstname: Mapped[str]
    lastname: Mapped[str]
    gender: Mapped[int]
    age: Mapped[str]
    is_subscribed: Mapped[bool] = mapped_column(nullable=True)
    mail: Mapped[str] = mapped_column(nullable=True)
    mail_password: Mapped[str] = mapped_column(nullable=True)

    def __init__(self, vkid, fisrtname, lastname, gender, age, is_subscribed, mail, mail_password):
        self.vkid = vkid
        self.firstname = fisrtname
        self.lastname = lastname
        self.gender = gender
        self.age = age
        self.is_subscribed = is_subscribed
        self.mail = mail
        self.mail_password = mail_password
        
    def __repr__(self):
        return f"{self.vkid} {self.firstname} {self.lastname} {self.gender} {self.age}"
engine = create_engine("sqlite:///mydb.db", echo=True)
Base.metadata.create_all(bind=engine)


token = "*vk_bot_token*"
bot = Bot(token=token)
vk_session = vk_api.VkApi(token=token)
longpoll = VkLongPoll(vk_session)
vk = vk_session.get_api()


def send_message(msg, id):
    # try:
        vk.messages.send(  # Отправляем сообщение
            user_id=id,
            message=msg,
            random_id='0'
        )

def send_keyboard(keyboard_name, id):
    vk.messages.send(
        user_id=id,
        keyboard=keyboard_name.get_keyboard(),
        random_id='0'
    )
    # except vk_api.exceptions.ApiError:
    #     print("[!] Failed to send to: ", id)
    #     pass


# Ceate new unread mail

# port = 465  # For SSL
# smtp_server = get_mail.server
# sender_email = get_mail.login  # Enter your address
# receiver_email = ""  # Enter receiver address
# password = get_mail.password
# message = """\
# Subject: test

# this is a test stay where you are"""
# send_unseen = 0
# context = ssl.create_default_context()
# if send_unseen != 0:
#     with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
#         server.login(sender_email, password)
#         server.sendmail(sender_email, receiver_email, message)
#         time.sleep(3)


# while True:
#     try:
#         send_message(get_mail.search_imap(), ids[0])
#     except:
#         pass
#     time.sleep(10)

Session = sessionmaker(bind=engine)
session = Session()

keyboard1=VkKeyboard(one_time=True, inline=False)
keyboard1.add_callback_button(label='Указать почту')


for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
        user_id = event.user_id
        text = event.text.lower()
        try:
            session.query(Person.mail).filter_by(vkid=user_id).first()[0]
            mail_status =1
        except:
            mail_status=0
        # Слушаем longpoll, если пришло сообщение то:
        if event.from_user:
            # Getting data from user's message
            name_from_vk=vk.users.get(user_id=user_id)[0]['first_name']
            lastname_from_vk=vk.users.get(user_id=user_id)[0]['last_name']
            gender_from_vk=vk.users.get(user_id=user_id, fields='sex')[0]['sex']
            bdate_from_vk=vk.users.get(user_id=user_id, fields='bdate')[0]['bdate']
            subscription_status = None
            # m = "a402b15@voenmeh.ru"
            m = None
            m_p = "bbFHHkaA"
            # 1 - female, 2 - male
            # Printing data in console (debug feature)
            print(event.message, name_from_vk, lastname_from_vk, gender_from_vk, bdate_from_vk,   
                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), event.attachments)
            person = Person(event.user_id, name_from_vk,lastname_from_vk, gender_from_vk,
                            bdate_from_vk, subscription_status, m, m_p)
                # session.rollback()               
        if mail_status == 0:
            while mail_status == 0:
                send_message("Укажи почту в ответном сообщении", user_id)

        # Указывание почты из вк в базу
        personn = session.query(Person).filter_by(vkid=user_id).first()
        personn.mail = "mail from vk"
        session.commit()
        if mail_status == 1:
            mail = session.query(Person).filter_by(vkid=user_id).first().mail
            mail_password = session.query(Person).filter_by(vkid=user_id).first().mail_password
        if text == "unseen" and mail_status==1:
            try:
                send_message(search_imap(mail, mail_password), user_id)
            except:
                send_message("У Вас нет непрочитанных сообщений", user_id)
        try:
            session.add(person)
            session.commit()
        except:
            pass
        print("End")