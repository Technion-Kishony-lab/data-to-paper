from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("ws/scientistgpt/", views.ScientistGPT, name="scientistgpt"),
]