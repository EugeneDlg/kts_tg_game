import enum


class Status(enum.StrEnum):
    registered = "registered"
    active = "active"
    finished = "finished"
    # waiting status
    thinking = "thinking"
    captain = "captain"
    answer = "answer"
    expired = "expired"
    wait_ok = "ok"
    top = "top"


class Command(enum.Enum):
    help = {"command": "/help"}
    hello = {"command": "/hello"}
    scores = {"command": "/scores"}
    finish = {"command": "/finish"}
    start = {"command": "start",
             "label": "Начать игру"}
    register = {"command": "register",
                "label": "Присоединиться к игре"}
    again = {"command": "again",
             "label": "Играть ещё"}
    speaker = {"command": "speaker"}
    top = {"command": "top",
           "label": "Крутить волчок"}

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return str(self) == str(other)

    def __getitem__(self, item):
        return self.value[item]


class UpdateType(enum.StrEnum):
    vk_request = "vk_user_request"
    message_event = "message_event"
    new_message = "message_new"
