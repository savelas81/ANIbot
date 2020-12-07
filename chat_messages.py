import json

'''
This add on is made to reply to chat messages that bot sees on ladder games.
It saves every chat message from enemy.
Messages will be saved in data/messages.json file
To add replies for saved messages replace ----- with your reply
Bot replies after amount of iterations in self.chat_delay (chat_messages.py) since enemy LAST chat message.

you need to add following lines to your bot and data folder:

from chat_messages import ChatData as ChatData

__init__
    self._chat_data = ChatData()

on_step
    response = self._chat_data.find_response(opponent_chat_data=self.state.chat, my_id_from_proto = self.player_id)
    if response:
        await self._client.chat_send(response, team_only=False)

'''


class ChatData:

    def __init__(self):
        self.chat_delay = 60
        self.chat_messages = {}
        self.loadData()
        self.response = None
        self.chat_timer = 0
        self.no_response = " ----- "

    def saveData(self):
        try:
            with open('data/messages.json', 'w') as file:
                json.dump(self.chat_messages, file, indent=2)
        except (OSError, IOError) as e:
            print(str(e))

    def loadData(self):
        try:
            with open('data/messages.json', 'r') as file:
                self.chat_messages = json.load(file)
        except (OSError, IOError) as e:
            self.chat_messages = {"Enemy message": "My response"}
            print("No chat data found.")
            print(e)

    def find_response(self, opponent_chat_data, my_id_from_proto):

        if opponent_chat_data:
            id_from_chat = opponent_chat_data[0].player_id
            if my_id_from_proto == id_from_chat:
                return None

        if not opponent_chat_data:
            if self.response:
                self.chat_timer -= 1
                if self.chat_timer < 0:
                    response = self.response
                    self.response = None
                    return response
                else:
                    return None
            return None
        else:
            opponent_chat = opponent_chat_data[0].message
            if not self.chat_messages.get(opponent_chat):
                self.chat_messages.update({opponent_chat: self.no_response})
                self.saveData()
                return None
            else:
                response = self.chat_messages.get(opponent_chat)
                if response == self.no_response:
                    return None
                else:
                    self.response = response
                    self.chat_timer = self.chat_delay
                    return None