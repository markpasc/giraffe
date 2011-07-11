#!/usr/bin/env python

import base64
from functools import wraps
import json
import logging
from os.path import join

import httplib2
import oauth2 as oauth
from termtool import Termtool, subcommand, argument


def authd(fn):
    @wraps(fn)
    def moo(self, args):
        if not all((args.consumer, args.access_token)):
            logging.error("Not configured to use Tumblr API yet; try 'configure' command first")
            sys.exit(1)

        consumer = oauth.Consumer(*args.consumer.split(':', 1))
        access_token = oauth.Token(*args.access_token.split(':', 1))

        return fn(self, args, consumer, access_token)
    return moo


@argument('--consumer')
@argument('--access-token')
class BeeExport(Termtool):

    def request(self, consumer, access_token, url, method='GET'):
        oauth_request = oauth.Request.from_consumer_and_token(consumer, access_token,
            http_method=method, http_url=url)
        oauth_sign_method = oauth.SignatureMethod_HMAC_SHA1()
        oauth_request.sign_request(oauth_sign_method, consumer, access_token)

        http = httplib2.Http()
        http.follow_redirects = False
        return http.request(oauth_request.normalized_url, oauth_request.method, headers=oauth_request.to_header())

    def export_posts(self, consumer, access_token, outdir):
        offset = 0
        while True:
            url = 'http://www.bestendtimesever.com/api/asset/offset=%d' % offset
            logging.info('Grabbing assets %r', url)
            resp, content = self.request(consumer, access_token, url)
            posts = json.loads(content)
            if not posts:
                break

            for post in posts:
                key = post['key']
                logging.info('Exporting post %s', key)
                with open(join(outdir, key + '.json'), 'w') as f:
                    f.write(json.dumps(
                        post,
                        sort_keys=True,
                        indent=4,
                    ))

            offset += 30

    def export_images(self, consumer, access_token, outdir):
        offset = 0
        while True:
            url = 'http://www.bestendtimesever.com/api/image/offset=%d' % offset
            logging.info('Grabbing images %r', url)
            resp, content = self.request(consumer, access_token, url)
            images = json.loads(content)
            if not images:
                break

            for image in images:
                key = image['key']
                ext = image['content_type'].split('/')[-1]
                logging.info('Exporting %s image %s', ext, key)
                with open(join(outdir, '%s.%s' % (key, ext)), 'wb') as f:
                    f.write(base64.b64decode(image['content_b64']))

            offset += 30

    @argument('dir')
    @subcommand(help='export the bee blog')
    @authd
    def export(self, args, consumer, access_token):
        self.export_posts(consumer, access_token, args.dir)
        self.export_images(consumer, access_token, args.dir)
        print "Export complete!"


if __name__ == '__main__':
    BeeExport().run()
