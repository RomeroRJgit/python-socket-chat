import logging
from enum import Enum

logging.basicConfig(level=logging.INFO)


class Events(Enum):
    START_CHAT = 0
    SEND_CHAT = 1
    RECEIVE_CHAT = 2
    QUIT = 3


events = dict()

def register(evt: Events, target=None, context=None):
    evt_id = id(target)
    print(target)
    events[(evt, evt_id)] = target

    logging.info(f"Registered Event: {evt} {f' from {context}' if context is not None else ''}")


def deregister(evt: Events, target=None):
    evt_id = id(target)
    del events[(evt, evt_id)]

    logging.info(f"Deregistered Event: {evt}")


def broadcast(evt: Events, *args, **kwargs):
    logging.info(f"Broadcasting Event: {evt}")

    for v in events.values():
        v[0](args, kwargs)

