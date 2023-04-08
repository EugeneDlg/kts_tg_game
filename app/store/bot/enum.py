import enum


class BaseEnum(enum.Enum):
    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return str(self) == str(other)


class Status(BaseEnum):
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


class Command(BaseEnum):
    start = {"command": "start", "label": "Начать игру"}
    register = {"command": "register",
                "label": "Присоединиться к игре"}
    hello = {"command": "hello"}
    again = {"command": "again",
             "label": "Играть ещё"}
    speaker = {"command": "speaker"}
    top = {"command": "top",
           "label": "Крутить волчок"}


class UpdateType(BaseEnum):
    vk_request = "vk_user_request"
    message_event = "message_event"
    new_message = "message_new"
