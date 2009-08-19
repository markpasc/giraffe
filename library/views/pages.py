import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from api.decorators import allowed_methods
from library import forms
from library.auth.decorators import auth_required, admin_only
from library.models import Person, Asset, Action


def stream(request, openid, template=None, content_type=None, empty_ok=False):
    try:
        me = Person.all().filter(openid=openid)[0]
    except IndexError:
        if not empty_ok:
            raise Http404
        me = None
        actions = list()
    else:
        blog = Action.all().filter(person=me, verb=Action.verbs.post)
        blog.filter(privacy_groups="public")
        blog.order('-when')
        actions = blog[0:10]

    return render_to_response(
        template or 'library/stream.html',
        {
            'blogger': me,
            'actions': actions,
        },
        context_instance=RequestContext(request),
        mimetype=content_type or settings.DEFAULT_CONTENT_TYPE,
    )


def profile(request, slug, template=None, content_type=None):
    person = Person.get(slug=slug)
    if person is None:
        raise Http404

    profile = Action.all().filter(person=person)
    profile.order('-when')
    actions = profile[0:10]

    return render_to_response(
        template or 'library/profile.html',
        {
            'person': person,
            'actions': actions,
        },
        context_instance=RequestContext(request),
        mimetype=content_type or settings.DEFAULT_CONTENT_TYPE,
    )


def asset(request, slug):
    asset = Asset.get(slug=slug)
    if asset is None:
        raise Http404

    actions = asset.actions.filter(person=asset.author, verb=Action.verbs.post)
    thread = asset.thread_members

    return render_to_response(
        'library/asset.html',
        {
            'asset': asset,
            'blogger': asset.author,
            'actions': actions,
            'thread': thread,
        },
        context_instance=RequestContext(request),
    )


def asset_redirect(request, slug):
    return HttpResponsePermanentRedirect(reverse('asset', kwargs={'slug': slug}))


@auth_required
@allowed_methods("POST")
def comment(request, slug):
    asset = Asset.get(slug=slug)
    if asset is None:
        raise Http404

    content = request.POST.get('content')

    comment = Asset(author=request.user, in_reply_to=asset)
    comment.content = content
    comment.content_type = 'text/markdown'
    if asset.thread:
        comment.thread = asset.thread
    else:
        comment.thread = comment.in_reply_to
    comment.save()

    act = Action(person=request.user, verb=Action.verbs.post, asset=comment, when=comment.published)
    act.save()

    return HttpResponseRedirect(asset.get_permalink_url())


def by_method(**kwargs):
    views_by_method = dict((k.lower(), v) for k, v in kwargs.items())
    @allowed_methods(*[meth.upper() for meth in views_by_method.keys()])
    def invoke(request, *args, **kwargs):
        view = views_by_method[request.method.lower()]
        return view(request, *args, **kwargs)
    return invoke


@admin_only
@allowed_methods("GET", "POST")
def post(request):
    if request.method == 'POST':
        form = forms.PostForm(request.POST)
        logging.debug('slug is %r', request.POST['slug'])
    else:
        form = forms.PostForm()

    if form.is_valid():
        post = Asset(author=request.user)
        post.content_type = form.cleaned_data['content_type']
        post.content = form.cleaned_data['content']

        if form.cleaned_data['title']:
            post.title = form.cleaned_data['title']

        if form.cleaned_data['slug']:
            post.slug = form.cleaned_data['slug']
        elif post.title:
            post.slug = re.sub(r'[\W_]+', '-', post.title.lower())

        post.save_and_post()
        return HttpResponseRedirect(reverse('home'))

    return render_to_response(
        'library/post.html',
        {
            'blogger': request.user,
            'form': form,
        },
        context_instance=RequestContext(request),
    )
