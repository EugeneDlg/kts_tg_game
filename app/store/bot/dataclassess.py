from dataclasses import dataclass


@dataclass
class Message:
    peer_id: int = None
    text: str = None
    user_id: int = None
    keyboard: dict = None
    event_id: int = None
    event_data: dict = None
    vk_user_request: int = None

    def serialize(self):
        obj = {}
        for key, value in self.__dict__.items():
            if value is not None:
                obj[key] = value
        return obj
        # return {
        #     "text": self.text,
        #     "user_id": self.user_id,
        #     "peer_id": self.peer_id,
        #     "keyboard": self.keyboard,
        #     "event_id": self.event_id,
        #     "event_data": self.event_data
        # }


@dataclass
class MessageUpdateObject:
    id: int
    user_id: int
    peer_id: int
    text: str


@dataclass
class EventUpdateObject:
    event_id: str
    user_id: int
    peer_id: int
    command: str


@dataclass
class Event:
    event_id: str
    user_id: int
    peer_id: int
    command: str


@dataclass
class InfoUpdateObject:
    user_id: int
    name: str
    last_name: str
    peer_id: int
    event_id: str


@dataclass
class Update:
    type: str
    object: MessageUpdateObject | EventUpdateObject | InfoUpdateObject
