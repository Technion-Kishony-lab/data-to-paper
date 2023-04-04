import uuid
from django.shortcuts import render


def index(request, experiment_id=None):
    experiment_id = uuid.uuid4().hex
    return render(request, "scientistgpt_app/index.html", {"experiment_id": experiment_id})