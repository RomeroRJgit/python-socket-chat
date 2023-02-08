import logging
from enum import Enum

logging.basicConfig(level=logging.INFO)


class Events(Enum):
    OPEN_CHAT = 0
    SERVER_SEND = 1
    CLIENT_SEND = 2
    QUIT = 3


events = dict()


def register(evt: Events, target=None, context=None, args=None, kwargs=None):
    if kwargs is None:
        kwargs = dict()
    if args is None:
        args = [()]
    evt_id = id(target)
    events[(evt, evt_id)] = (target, (args, kwargs))

    logging.info(f"Registered Event: {evt} {f' from {context}' if context is not None else ''}")


def deregister(evt: Events, target=None):
    evt_id = id(target)
    del events[(evt, evt_id)]

    logging.info(f"Deregistered Event: {evt}")


def broadcast(evt: Events):
    for v in events.values():
        v[0](*v[1][0], **v[1][1])
