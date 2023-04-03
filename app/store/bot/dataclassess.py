from dataclasses import dataclass


@dataclass
class Message:
    peer_id: int
    text: str
    user_id: int = None
    keyboard: dict = None
    event_id: int = None
    event_data: dict = None

    def serialize(self):
        return {
            "text": self.text,
            "user_id": self.user_id,
            "peer_id": self.peer_id,
            "keyboard": self.keyboard,
            "event_id": self.event_id,
            "event_data": self.event_data
        }


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
class Update:
    type: str
    object: MessageUpdateObject | EventUpdateObject
