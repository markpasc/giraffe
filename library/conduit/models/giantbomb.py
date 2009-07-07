from cgi import parse_qs
from datetime import datetime
import time
from urllib import urlencode
from urlparse import urljoin, urlparse, urlunparse

from django.conf import settings
from remoteobjects import RemoteObject, fields

from library.conduit.models.base import Conduit
from library.models import Asset


class Bombdate(fields.Field):

    timestamp_format = '%Y-%m-%d %H:%M:%S'

    def decode(self, value):
        try:
            return datetime(*(time.strptime(value, self.timestamp_format))[0:6])
        except ValueError:
            raise TypeError('Value to decode %r is not a valid date time stamp' % (value,))

    def encode(self, value):
        if not isinstance(value, datetime):
            raise TypeError('Value to encode %r is not a datetime' % (value,))
        if value.tzinfo is not None:
            raise TypeError("Value to encode %r is a datetime, but it has timezone information and we don't want to deal with timezone information" % (value,))
        return value.replace(microsecond=0).strftime(self.timestamp_format)


class Bombject(RemoteObject):

    content_types = ('application/json', 'text/javascript')

    @classmethod
    def get(cls, url, **kwargs):
        if not urlparse(url)[1]:
            url = urljoin('http://api.giantbomb.com/', url)

        self = super(Bombject, cls).get(url, **kwargs)
        self = self.filter(api_key=settings.GIANT_BOMB_KEY, format='json')
        return self

    def filter(self, **kwargs):
        url = self._location
        parts = list(urlparse(url))
        query = parse_qs(parts[4])
        query = dict([(k, v[0]) for k, v in query.iteritems()])

        query.update(kwargs)

        parts[4] = urlencode(query)
        url = urlunparse(parts)
        return super(Bombject, self).get(url)


class Game(Bombject):

    id = fields.Field()
    name = fields.Field()
    api_detail_url = fields.Field()
    site_detail_url = fields.Field()

    summary = fields.Field(api_name='deck')
    description = fields.Field()
    image = fields.Field()
    published = Bombdate(api_name='date_added')
    updated = Bombdate(api_name='date_last_updated')

    characters = fields.Field()
    concepts = fields.Field()
    developers = fields.Field()
    platforms = fields.Field()
    publishers = fields.Field()

    @classmethod
    def get(cls, url, **kwargs):
        res = GameResult.get(url)
        return res.results[0]

    def as_asset(self):
        return Asset(
            object_type=Asset.object_types.game,
            title=self.name,
            content=self.summary,
            content_type='text/markdown',
            privacy_groups=['public'],
            published=self.published,
            updated=self.updated,
        )


class GameResult(Bombject):

    status_code = fields.Field()
    error = fields.Field()
    total = fields.Field(api_name='number_of_total_results')
    count = fields.Field(api_name='number_of_page_results')
    limit = fields.Field()
    offset = fields.Field()
    results = fields.List(fields.Object(Game))

    def update_from_dict(self, data):
        if not isinstance(data['results'], list):
            data = dict(data)
            data['results'] = [data['results']]
        super(GameResult, self).update_from_dict(data)


class GiantBomb(Conduit):

    def lookup(self, id):
        obj = Game.get('/game/%s/' % (id,))
        return obj.as_asset()

    def search(self, query=None, **kwargs):
        assert query is not None
        obj = GameResult.get('/search/').filter(resources='game')
        obj = obj.filter(query=query)
        return [game.as_asset() for game in obj.results]
