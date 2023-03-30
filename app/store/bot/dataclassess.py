from dataclasses import dataclass


@dataclass
class Message:
    peer_id: int
    text: str
    user_id: int = None
    event_id: int = None
    keyboard: dict = None
    event_data: dict = None



@dataclass
class UpdateMessage:
    from_id: int
    text: str
    id: int


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
