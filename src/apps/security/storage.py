"""Local media URLs must pass application authorization before being opened."""
from django.core.files.storage import FileSystemStorage
from django.urls import reverse


def private_file_url(name):
    return reverse('private_file', kwargs={'name': name})


class PrivateFileStorage(FileSystemStorage):
    def url(self, name):
        return private_file_url(name)
