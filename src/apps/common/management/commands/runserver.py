"""Use a dedicated default port for the IHRMS development server."""
from django.contrib.staticfiles.management.commands.runserver import Command as StaticFilesRunserverCommand


class Command(StaticFilesRunserverCommand):
    default_port = "8001"
