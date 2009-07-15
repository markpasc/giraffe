from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseRedirect

from api.decorators import api_error, allowed_methods
from library.auth.decorators import auth_required
from library.models import Image


@auth_required
@api_error
@allowed_methods("POST")
def post(request):
    content_type = request.META['CONTENT_TYPE']
    assert content_type.startswith('image/')
    extension = content_type.split('/', 2)[1]

    i = Image(content=request.raw_post_data, content_type=content_type)
    i.save()

    url = reverse('library.views.images.get',
        kwargs={'key': i.key(), 'ext': extension})
    return HttpResponseRedirect(url)


def get(request, key, ext):
    image = Image.get(key)
    if image is None:
        raise Http404

    return HttpResponse(image.content, content_type=image.content_type)
