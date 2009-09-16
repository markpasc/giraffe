import cgi
from urllib import urlencode
from urlparse import urljoin, urlparse, urlunparse
from xml.etree import ElementTree

from django.conf import settings
from google.appengine.api.urlfetch import fetch
from google.appengine.api import images
from oauth import OAuthConsumer, OAuthRequest, OAuthSignatureMethod_HMAC_SHA1
from oauthclient import NetflixHttp
from remoteobjects import RemoteObject, fields

from library.conduit import conduits
from library.conduit.models.base import Conduit, Result
from library.models import Asset, Link


class Flixject(RemoteObject):

    content_types = ('text/xml', 'application/xml')

    @property
    def api_token(self):
        return settings.NETFLIX_KEY

    def get_request(self, headers=None, **kwargs):
        request = super(Flixject, self).get_request(headers=headers, **kwargs)
        method = request.get('method', 'GET')

        # Apply OAuthness.
        csr = OAuthConsumer(*self.api_token)
        orq = OAuthRequest.from_consumer_and_token(csr, http_method=method,
            http_url=request['uri'])

        # OAuthRequest will strip our query parameters, so add them back in.
        parts = list(urlparse(self._location))
        queryargs = cgi.parse_qs(parts[4], keep_blank_values=True)
        for key, value in queryargs.iteritems():
            orq.set_parameter(key, value[0])

        # Sign the request.
        osm = OAuthSignatureMethod_HMAC_SHA1()
        orq.set_parameter('oauth_signature_method', osm.get_name())
        orq.sign_request(osm, csr, None)

        if method == 'GET':
            request['uri'] = orq.to_url()
        else:
            request['headers'].update(orq.to_header())

        return request

    def update_from_tree(self, tree):
        data = dict((k, v(tree)) for k, v in self.decoder_ring.items())
        self.update_from_dict(data)
        return self

    def update_from_response(self, url, response, content):
        self.raise_for_response(url, response, content)

        tree = ElementTree.fromstring(content)
        self.update_from_tree(tree)


class Synopsis(Flixject):

    text = fields.Field()

    decoder_ring = {
        'text': lambda x: x.text,
    }


def findwith(trees, **kwargs):
    return [j for j in trees if reduce(lambda x,y: x and y, [j.get(k) == v for k,v in kwargs.items()])]


class Title(Flixject, Result):

    api_url = fields.Field()
    title   = fields.Field()
    link    = fields.Field()
    thumb   = fields.Field()
    synopsis = fields.Field()

    decoder_ring = {
        'title': lambda x: x.find('title').get('regular'),
        'link':  lambda x: findwith(x.findall('link'), rel='alternate')[0].get('href'),
        'thumb': lambda x: x.find('box_art').get('large'),
        'api_url': lambda x: x.find('id'),
        'synopsis': lambda x: Synopsis.get(findwith(x.findall('link'), rel='http://schemas.netflix.com/catalog/titles/synopsis')[0].get('href')),
    }

    def save_asset(self):
        asset = Asset(
            object_type=Asset.object_types.movie,
            title=self.title,
            content=self.synopsis.text,
            content_type='text/markdown',
            privacy_groups=['public'],
        )
        asset.save()

        link = Link(
            rel='alternate',
            content_type='text/html',
            href=self.link,
            asset=asset,
        )
        link.save()

        if self.thumb:
            resp = fetch(self.thumb)
            image = images.Image(resp.content)

            link = Link(
                rel='thumbnail',
                content_type='image/jpeg',
                href=self.thumb,
                width=image.width,
                height=image.height,
                asset=asset,
            )

        return asset


class Catalog(Flixject):

    results = fields.List(fields.Field())
    total   = fields.Field()
    offset  = fields.Field()
    limit   = fields.Field()

    decoder_ring = {
        'results': lambda x: [Title().update_from_tree(tree) for tree in x.findall('catalog_title')],
        'total':   lambda x: int(x.find('number_of_results').text),
        'offset':  lambda x: int(x.find('start_index').text),
        'limit':   lambda x: int(x.find('results_per_page').text),
    }


class Netflix(Conduit):

    @classmethod
    def lookup(cls, url):
        return Title.get(url)

    @classmethod
    def search(cls, query):
        cat = Catalog.get('http://api.netflix.com/catalog/titles').filter(term=query)
        return cat.results


conduits.add(Netflix)
