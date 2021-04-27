# Used for type hinting and not having to use annotations for the objects
from __future__ import annotations

import logging
import sys
from typing import Optional
import fastjsonschema

from . import HivenTypeObject, check_valid
from .. import utils
from ..exceptions import InvalidPassedDataError, InitializationError

# Only importing the Objects for the purpose of type hinting and not actual use
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import House, Room
    from .. import HivenClient

logger = logging.getLogger(__name__)

__all__ = ['Entity']


class Entity(HivenTypeObject):
    """ Represents a Hiven Entity inside a House which can contain Rooms """
    json_schema = {
        'type': 'object',
        'properties': {
            'id': {'type': 'string'},
            'name': {'type': 'string'},
            'type': {'type': 'integer', 'default': 1},
            'resource_pointers': {
                'anyOf': [
                    {'type': 'object'},
                    {'type': 'array'},
                    {'type': 'null'},
                ],
                'default': []
            },
            'house_id': {'type': 'string'},
            'house': {
                'anyOf': [
                    {'type': 'object'},
                    {'type': 'string'},
                    {'type': 'null'},
                ]
            },
            'position': {'type': 'integer'}
        },
        'additionalProperties': False,
        'required': ['id', 'name', 'position', 'resource_pointers', 'house_id']
    }
    json_validator = fastjsonschema.compile(json_schema)

    def __init__(self, data: dict, client: HivenClient):
        """
        Represents a Hiven Entity inside a House which can contain Rooms

        :param data: Data that should be used to create the object
        :param client: The HivenClient
        """
        try:
            super().__init__()
            self._type = data.get('type')
            self._position = data.get('position')
            self._resource_pointers = data.get('resource_pointers')
            self._name = data.get('name')
            self._id = data.get('id')
            self._house_id = data.get('house_id')
            self._house = data.get('house')

        except Exception as e:
            utils.log_traceback(
                msg=f"Traceback in function '{self.__class__.__name__}' Validation:",
                suffix=f"Failed to initialise {self.__class__.__name__} due to exception:\n"
                       f"{sys.exc_info()[0].__name__}: {e}!"
            )
            raise InitializationError(
                f"Failed to initialise {self.__class__.__name__} due to an exception occurring"
            ) from e
        else:
            self._client = client

    def __repr__(self) -> str:
        info = [
            ('name', self.name),
            ('id', self.id),
            ('position', self.position),
            ('type', self.type)
        ]
        return '<Entity {}>'.format(' '.join('%s=%s' % t for t in info))

    def get_cached_data(self) -> Optional[dict]:
        """ Fetches the most recent data from the cache based on the instance id """
        return self._client.storage['entities'].get(self.id)

    @classmethod
    @check_valid
    def format_obj_data(cls, data: dict) -> dict:
        """
        Validates the data and appends data if it is missing that would be required for the creation of an
        instance.

        ---

        Does NOT contain other objects and only their ids!

        :param data: Data that should be validated and used to form the object
        :return: The modified dictionary, which can then be used to create a new class instance
        """
        if not data.get('house_id') and data.get('house'):
            house = data.pop('house')
            if type(house) is dict:
                house_id = house.get('id')
            elif isinstance(house, HivenTypeObject):
                house_id = getattr(house, 'id', None)
            else:
                house_id = None

            if house_id is None:
                raise InvalidPassedDataError("The passed house is not in the correct format!", data=data)
            else:
                data['house_id'] = house_id

        data['house'] = data.get('house_id')
        data = cls.validate(data)
        return data

    @property
    def type(self) -> Optional[int]:
        return getattr(self, '_type', None)

    @property
    def resource_pointers(self) -> Optional[List[Room, dict]]:
        """ Objects contained inside the entity. If dict is returned it's a type that is not yet included in the lib """
        from . import Room
        if type(self._resource_pointers) is list and len(self._resource_pointers) > 0:
            resources_created = False
            for _ in self._resource_pointers:
                if type(_) is not dict:
                    resources_created = True

            if not resources_created:
                resource_pointers = []
                for d in self._resource_pointers:
                    if d['resource_type'] == "room":
                        data = self._client.storage['rooms']['house'][d['resource_id']]
                        resource_pointers.append(Room(data, client=self._client))
                    else:
                        resource_pointers.append(d)

                self._resource_pointers = resource_pointers
            return self._resource_pointers

        else:
            return None

    @property
    def name(self) -> str:
        return getattr(self, '_name', None)

    @property
    def id(self) -> str:
        return getattr(self, '_id', None)

    @property
    def house_id(self) -> str:
        return getattr(self, '_house_id', None)

    @property
    def position(self) -> int:
        return getattr(self, '_position', None)

    @property
    def house(self) -> Optional[House]:
        from . import House
        if type(self._house) is str:
            house_id = self._house
        elif type(self.house_id) is str:
            house_id = self.house_id
        else:
            house_id = None

        if house_id:
            data = self._client.storage['houses'].get(house_id)
            if data:
                self._house = House(data=data, client=self._client)
                return self._house
            else:
                return None

        elif type(self._house) is House:
            return self._house
        else:
            return None
