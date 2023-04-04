from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/scientistgpt/(?P<experiment_id>\w+)/$", consumers.ScientistGPTConsumer.as_asgi()),
]