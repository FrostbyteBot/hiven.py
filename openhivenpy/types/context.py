# Used for type hinting and not having to use annotations for the objects
from __future__ import annotations

import datetime
import logging
from typing import Optional
# Only importing the Objects for the purpose of type hinting and not actual use
from typing import TYPE_CHECKING

import fastjsonschema

from . import DataClassObject
from .. import utils
from ..exceptions import InvalidPassedDataError, InitializationError

if TYPE_CHECKING:
    from . import House, User, TextRoom
    from .. import HivenClient

logger = logging.getLogger(__name__)

__all__ = ['Context']


class Context(DataClassObject):
    """ Represents a Command Context for a triggered command that was registered prior """
    json_schema = {
        'type': 'object',
        'properties': {
            'room': {'type': 'object'},
            'author': {'type': 'object'},
            'timestamp': {
                'anyOf': [
                    {'type': 'string'},
                    {'type': 'integer'}
                ],
            },
            'house': {
                'anyOf': [
                    {'type': 'object'},
                    {'type': 'null'}
                ]
            },
        },
        'additionalProperties': False,
        'required': ['room', 'author', 'timestamp']
    }
    json_validator = fastjsonschema.compile(json_schema)

    def __init__(self, data: dict, client: HivenClient):
        """
        Represents a Command Context for a triggered command that was registered prior

        :param data: Data that should be used to create the object
        :param client: The HivenClient
        """
        try:
            self._room = data.get('room')
            self._author = data.get('author')
            self._house = data.get('house')
            self._timestamp = data.get('timestamp')

        except Exception as e:
            raise InitializationError(f"Failed to initialise {self.__class__.__name__}") from e
        else:
            self._client = client

    @classmethod
    def format_obj_data(cls, data: dict) -> dict:
        """
        Validates the data and appends data if it is missing that would be required for the creation of an
        instance.

        ---

        Does NOT contain other objects and only their ids!

        :param data: Data that should be validated and used to form the object
        :return: The modified dictionary, which can then be used to create a new class instance
        """
        data = cls.validate(data)
        data['timestamp'] = utils.safe_convert(int, data.get('timestamp'))

        if not data.get('room_id') and data.get('room'):
            room = data.pop('room')
            if type(room) is dict:
                room = room.get('id', None)
            elif isinstance(room, DataClassObject):
                room = getattr(room, 'id', None)
            else:
                room = None

            if room is None:
                raise InvalidPassedDataError("The passed room is not in the correct format!", data=data)
            else:
                data['room_id'] = room

        if not data.get('house_id') and data.get('house'):
            house = data.pop('house')
            if type(house) is dict:
                house = house.get('id', None)
            elif isinstance(house, DataClassObject):
                house = getattr(house, 'id', None)
            else:
                house = None

            if house is None:
                raise InvalidPassedDataError("The passed house is not in the correct format!", data=data)
            else:
                data['house_id'] = house

        if not data.get('author_id') and data.get('author'):
            author = data.pop('author')
            if type(author) is dict:
                author = author.get('id', None)
            elif isinstance(author, DataClassObject):
                author = getattr(author, 'id', None)
            else:
                author = None

            if author is None:
                raise InvalidPassedDataError("The passed author is not in the correct format!", data=data)
            else:
                data['author_id'] = author

        data['room'] = data['room_id']
        data['author'] = data['author_id']
        data['house'] = data['house_id']
        return data

    @property
    def house(self) -> Optional[House]:
        from . import House
        if type(self._house) is str:
            data = self._client.storage['houses'].get(self._house)
            if data:
                self._house = House(data=data, client=self._client)
                return self._house
            else:
                return None

        elif type(self._house) is House:
            return self._house
        else:
            return None

    @property
    def room(self) -> Optional[TextRoom]:
        from . import TextRoom
        if type(self._room) is str:
            data = self._client.storage['rooms']['house'].get(self._room)
            if data:
                self._room = TextRoom(data=data, client=self._client)
                return self._room
            else:
                return None

        elif type(self._room) is TextRoom:
            return self._room
        else:
            return None

    @property
    def author(self) -> Optional[User]:
        from . import User
        if type(self._author) is str:
            data = self._client.storage['users'].get(self._author)
            if data:
                self._author = User(data=data, client=self._client)
                return self._author
            else:
                return None

        elif type(self._author) is User:
            return self._author
        else:
            return None

    @property
    def timestamp(self) -> Optional[datetime.datetime]:
        if utils.convertible(int, self._timestamp):
            # Converting to seconds because it's in milliseconds
            self._timestamp = datetime.datetime.fromtimestamp(utils.safe_convert(int, self._timestamp) / 1000)
            return self._timestamp
        elif type(self._timestamp) is datetime.datetime:
            return self._timestamp
        else:
            return None
