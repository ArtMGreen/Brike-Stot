import vk_api
import os
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import random
import requests
import redis


class BrikeStot:
    def __init__(self):
        self.vk_session = vk_api.vk_api.VkApiGroup(token=os.environ['BRIKE_STOT_TOKEN'])
        self.warns = redis.from_url(os.environ.get("REDIS_URL"))
        self.vk = self.vk_session.get_api()
        self.commands = {'пред': self.warn, 'не понял': self.unwarn, 'кик': self.kick,
                         'че там': self.check, 'чё там': self.check, 'амнистия': self.pardon}
        self.settings = {2000000001: {'no_bots': 1, 'fun': 0, 'no_bombs': 1, 'is_channel': 0},  # админский чат
                         2000000002: {'no_bots': 1, 'fun': 0, 'no_bombs': 1, 'is_channel': 0},  # шуетологи
                         2000000003: {'no_bots': 0, 'fun': 0, 'no_bombs': 0, 'is_channel': 0},  # чат-боты
                         2000000004: {'no_bots': 1, 'fun': 0, 'no_bombs': 1, 'is_channel': 1},  # чат уведомлений
                         2000000005: {'no_bots': 1, 'fun': 0, 'no_bombs': 1, 'is_channel': 0}}  # чат по правилам

    def warn(self, warned_id, peer_id, admin_id):
        hashtag = ''
        if warned_id in (-190805980, -190699373):
            return
        elif warned_id > 0:
            hashtag = f'user{warned_id}'
        elif warned_id < 0:
            hashtag = f'group{abs(warned_id)}'
        if not self.warns.exists(f"warns_{warned_id}_{peer_id}"):
            self.warns.set(f"warns_{warned_id}_{peer_id}", 1)
        else:
            self.warns.set(f"warns_{warned_id}_{peer_id}", self.warns.get(f"warns_{warned_id}_{peer_id}") + 1)
        current_warns = self.warns.get(f"warns_{warned_id}_{peer_id}")
        if current_warns < 3:
            self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                                  peer_id=peer_id,
                                  message=f'Вам вынесено предупреждение ({current_warns} из 3). '
                                          f'Старайтесь общаться более культурно, '
                                          f'иначе придется с вами попрощаться. '
                                          f'#{hashtag}')
        else:
            self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                                  peer_id=peer_id,
                                  message=f'Мы неоднократно выносили предупреждения, которые вы игнорировали. '
                                          f'Теперь придется попрощаться. #{hashtag}')
            self.vk.messages.removeChatUser(chat_id=peer_id - 2000000000,
                                            member_id=warned_id)
            self.send_notification(peer_id, 'chat_kick_user', admin_id, warned_id)

    def unwarn(self, warned_id, peer_id, admin_id):
        hashtag = ''
        if warned_id in (-190805980, -190699373):
            return
        elif warned_id > 0:
            hashtag = f'user{warned_id}'
        elif warned_id < 0:
            hashtag = f'group{abs(warned_id)}'
        if not self.warns.exists(f"warns_{warned_id}_{peer_id}"):
            self.warns.set(f"warns_{warned_id}_{peer_id}", 0)
        else:
            current_warns = self.warns.get(f"warns_{warned_id}_{peer_id}")
            if current_warns > 0:
                current_warns -= 1
                self.warns.set(f"warns_{warned_id}_{peer_id}", current_warns)
                self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                                      peer_id=peer_id,
                                      message=f'Извини, был не прав, снимаю тебе пред. '
                                              f'({current_warns} из 3) #{hashtag}')

    def kick(self, kicked_id, peer_id, admin_id):
        hashtag = ''
        if kicked_id in (-190805980, -190699373):
            return
        elif kicked_id > 0:
            hashtag = f'user{kicked_id}'
        elif kicked_id < 0:
            hashtag = f'group{abs(kicked_id)}'
        self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                              peer_id=peer_id,
                              message=f'Увы, нам пора прощаться. #{hashtag}')
        self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                              peer_id=peer_id,
                              sticker_id=57681)
        self.vk.messages.removeChatUser(chat_id=peer_id - 2000000000,
                                        member_id=kicked_id)
        self.send_notification(peer_id, 'chat_kick_user', admin_id, kicked_id)

    def check(self, checked_id, peer_id, admin_id):
        hashtag = ''
        if checked_id in (-190805980, -190699373):
            return
        elif checked_id > 0:
            hashtag = f'user{checked_id}'
        elif checked_id < 0:
            hashtag = f'group{abs(checked_id)}'
        if not self.warns.exists(f"warns_{checked_id}_{peer_id}"):
            self.warns.set(f"warns_{checked_id}_{peer_id}", 0)
        self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                              peer_id=peer_id,
                              message=f'Вынесено {self.warns.get(f"warns_{checked_id}_{peer_id}")} '
                                      f'из 3 предупреждений. #{hashtag}')

    def pardon(self, pardon_id, peer_id, admin_id):
        hashtag = ''
        tag = ''
        if pardon_id in (-190805980, -190699373):
            return
        elif pardon_id > 0:
            hashtag = f'user{pardon_id}'
            tag = f'@id{pardon_id}'
        elif pardon_id < 0:
            hashtag = f'group{abs(pardon_id)}'
            tag = f'@club{abs(pardon_id)}'
        if not self.warns.exists(f"warns_{pardon_id}_{peer_id}"):
            self.warns.set(f"warns_{pardon_id}_{peer_id}", 0)
        else:
            if self.warns.get(f"warns_{pardon_id}_{peer_id}") > 0:
                self.warns.set(f"warns_{pardon_id}_{peer_id}", 0)
                self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                                      peer_id=peer_id,
                                      message=f'Извини, {tag}. #{hashtag}')

    def send_exception(self, ex):
        ex = str(ex)
        if 'key=' in ex:
            ex = ex[:ex.find('key=') + 4] + '<hidden>'
        self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                              peer_id=2000000004,
                              message=f'Выброшено исключение!\n{ex}')

    def send_notification(self, peer_id, action_type, author_id, member_id):
        chat_req = self.vk.messages.getConversationsById(peer_ids=[peer_id])
        chat_name = chat_req["items"][0]["chat_settings"]["title"]
        if author_id > 0:
            author_req = self.vk.users.get(user_ids=[author_id],
                                           name_case='nom')
            authors_name = f'@id{author_id} ({author_req[0]["first_name"]} {author_req[0]["last_name"]})'
        else:
            authors_name = f'@club{abs(author_id)} ' \
                           f'({self.vk.groups.getById(group_id=str(abs(author_id)))[0]["name"]})'
        if member_id > 0:
            members_req = self.vk.users.get(user_ids=[member_id],
                                            name_case='acc')
            members_name = f'@id{member_id} ' \
                           f'({members_req[0]["first_name"]} {members_req[0]["last_name"]})'
        elif member_id < 0:

            members_name = f'сообщество «@club{abs(member_id)} ' \
                           f'({self.vk.groups.getById(group_id=str(abs(member_id)))[0]["name"]})»'
        # перебор типов действий
        if action_type == 'chat_invite_user':
            # оповещение о возвращении в чат
            if member_id == author_id:
                self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                                      peer_id=2000000004,
                                      message=f'{authors_name} вернулся(-лась) в беседу «{chat_name}»',
                                      disable_mentions=1)
            # оповещение о приглашении в чат
            else:
                self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                                      peer_id=2000000004,
                                      message=f'{authors_name} пригласил(а) {members_name} '
                                              f'в беседу «{chat_name}»',
                                      disable_mentions=1)
            # если запрещены боты
            if member_id < 0 and self.settings[peer_id]['no_bots']:
                self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                                      peer_id=peer_id,
                                      message='Этот чат слишком тесен для стольких ботов.')
                self.kick(member_id, peer_id, -190805980)
        elif action_type == 'chat_kick_user':
            # оповещение о выходе из чата
            if member_id == author_id:
                self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                                      peer_id=2000000004,
                                      message=f'{authors_name} вышел(-шла) из беседы «{chat_name}»',
                                      disable_mentions=1)
            # оповещение о кике из чата
            else:
                self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                                      peer_id=2000000004,
                                      message=f'{authors_name} исключил(а) {members_name} '
                                              f'из беседы «{chat_name}»',
                                      disable_mentions=1)
        elif action_type == 'chat_invite_user_by_link':
            # оповещение о вступлении по ссылке
            self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                                  peer_id=2000000004,
                                  message=f'{authors_name} присоединился(-лась) к '
                                          f'беседе «{chat_name}» по ссылке',
                                  disable_mentions=1)

    def fun_warn(self, has_reply, peer_id):
        if has_reply:
            self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                                  peer_id=peer_id, expire_ttl=60,
                                  message=f'Извини, был не прав, снимаю тебе пред. '
                                          f'(0 из {random.randint(-10, 0)})')
        else:
            self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                                  peer_id=peer_id, expire_ttl=60,
                                  message='пред')

    def fun_unwarn(self, has_reply, peer_id):
        if has_reply:
            self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                                  peer_id=peer_id, expire_ttl=60,
                                  message=f'Вам вынесено предупреждение ({random.randint(0, 10)} из 0). '
                                          f'Старайтесь общаться более культурно, перечитайте правила беседы, '
                                          f'иначе придется с вами попрощаться.')
        else:
            self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                                  peer_id=peer_id, expire_ttl=60,
                                  message='Что ты не понял?')

    def zhalomba(self, has_reply, peer_id):
        if has_reply:
            self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                                  peer_id=peer_id, expire_ttl=60,
                                  message=random.choice(('пред', 'кик')))
        else:
            self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                                  peer_id=peer_id, expire_ttl=60,
                                  message=random.choice(('жалаба', 'жолоба', 'жаломба', 'жаба',
                                                         'жожоба', 'Замечание Вам.')))

    def fun_check(self, has_reply, peer_id):
        if has_reply:
            self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                                  peer_id=peer_id, expire_ttl=60,
                                  message=random.choice(('Вынесено 28 предупреждений.',
                                                         'Вынесено 0 из 28 предупреждений.',
                                                         '10 из 10 предупреждений!')))
        else:
            self.vk.messages.send(random_id=random.randint(0, 2 ** 64),
                                  peer_id=peer_id, expire_ttl=60,
                                  message=random.choice(('че там с деньгами?',
                                                         'ничё и не там!')))

    def listen(self):
        longpoll = VkBotLongPoll(self.vk_session, 190805980)
        for event in longpoll.listen():
            if event.type in (VkBotEventType.MESSAGE_NEW, VkBotEventType.MESSAGE_REPLY):  # если это сообщение
                message = event.obj.get('message', event.obj)
                peer_id = message['peer_id']
                # если сообщение пришло не из чата Контактов:
                if peer_id not in self.settings.keys():
                    continue
                # если это сервисное сообщение
                if message.get('action'):
                    action_type = message['action']['type']
                    member_id = message['action'].get('member_id', 0)
                    author_id = message['from_id']
                    self.send_notification(peer_id, action_type, author_id, member_id)
                # если сообщение с админки
                elif message['from_id'] == -190699373:
                    if message['text'].lower() in self.commands.keys():  # если это команда
                        admin_id = message['admin_author_id']
                        if message.get('reply_message'):
                            subject_id = message['reply_message']['from_id']
                            self.commands[message['text'].lower()](subject_id, peer_id, admin_id)
                        elif message.get('fwd_messages'):
                            for i in range(len(message['fwd_messages'])):
                                subject_id = message['fwd_messages'][i]['from_id']
                                self.commands[message['text'].lower()](subject_id, peer_id, admin_id)
                # если запрещены исчезающие сообщения или это чат-канал
                elif ((self.settings[peer_id]['no_bombs'] and message.get('expire_ttl') or
                       self.settings[peer_id]['is_channel'])):
                    self.vk.messages.delete(delete_for_all=1,
                                            peer_id=peer_id,
                                            conversation_message_ids=[message['conversation_message_id']])
                # если включены игровые команды
                elif self.settings[peer_id]['fun'] and message['from_id'] > 0:
                    if message['text'].lower() == 'не понял':
                        self.fun_unwarn(bool(message.get('reply_message')), peer_id)
                    elif message['text'].lower() == 'пред':
                        self.fun_warn(bool(message.get('reply_message')), peer_id)
                    elif message['text'].lower() in ('#жалоба', '#жалаба', '#жолоба', '#жаломба',
                                                     '#жаба', '#жожоба', 'жалоба', 'жалаба',
                                                     'жолоба', 'жаломба', 'жаба', 'жожоба'):
                        self.zhalomba(bool(message.get('reply_message')), peer_id)
                    elif message['text'].lower() in ('че там', 'чё там'):
                        self.fun_check(bool(message.get('reply_message')), peer_id)


while True:
    try:
        try:
            brike_stot = BrikeStot()
            brike_stot.listen()
        except requests.exceptions.ReadTimeout:
            del brike_stot
        except Exception as e:
            brike_stot.send_exception(e)
            del brike_stot
    except Exception as e:
        print(e)
