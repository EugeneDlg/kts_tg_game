from dataclasses import dataclass


@dataclass
class Message:
    user_id: int
    peer_id: int
    text: str
    keyboard: dict = None


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
    id: str
    user_id: int
    peer_id: int
    command: str


@dataclass
class Event:
    user_id: int
    peer_id: int
    command: str


@dataclass
class Update:
    type: str
    object: MessageUpdateObject | EventUpdateObject
