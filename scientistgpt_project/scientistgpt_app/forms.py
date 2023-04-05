from django import forms
from django.core.exceptions import ValidationError


def file_size(value):
    limit = 50 * 1024 * 1024
    if value.size > limit:
        raise ValidationError('File too large. Size should not exceed 50 MiB.')


class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField(required=True, validators=[file_size])
