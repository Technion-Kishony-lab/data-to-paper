from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path("ws/scientistgpt/", consumers.ScientistGPTConsumer.as_asgi()),
]