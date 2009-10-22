from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from api.decorators import api_error, allowed_methods
from library.auth.decorators import auth_required
from library.models import Image


@auth_required
@api_error
def browser_post(request):
    if request.method == "GET":
        return render_to_response(
            'library/upload_image.html',
            {},
            context_instance=RequestContext(request),
        )
    elif request.method != "POST":
        return HttpResponse("Invalid method %r" % request.method,
            content_type='text/plain',
            status=405)

    if 'image' not in request.FILES:
        return HttpResponse("No uploaded file 'image' found?",
            content_type='text/plain',
            status=400)

    upload = request.FILES['image']
    extension = upload.name.split('.')[-1]

    i = Image(content=upload.read(), content_type="image/%s" % extension)
    i.save()

    url = reverse('library.views.images.get',
        kwargs={'key': i.key(), 'ext': extension})
    return HttpResponseRedirect(url)


@auth_required
@api_error
@allowed_methods("POST")
def raw_post(request):
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
