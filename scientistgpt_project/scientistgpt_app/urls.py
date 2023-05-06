from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    # in the tutorial, this is the example: path("<str:room_name>/", views.room, name="room"),
    path("<str:experiment_id>/", views.index, name="scientistgpt"),
    path('upload_data/<str:experiment_id>/', views.upload_data, name='upload_data'),
]