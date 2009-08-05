from django import forms


class CommentForm(forms.Form):
    pass


class PostForm(forms.Form):

    title = forms.CharField(required=False)
    slug = forms.RegexField(required=False, regex=r'^[\w-]*$')
    content = forms.CharField()
    content_type = forms.RegexField(regex=r'^\w+/[\w+-]+$')
