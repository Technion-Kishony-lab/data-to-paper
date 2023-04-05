import uuid
from django.shortcuts import render
import zipfile
from .forms import UploadFileForm
import os


def index(request, experiment_id=None):
    experiment_id = uuid.uuid4().hex
    return render(request, "scientistgpt_app/index.html", {"experiment_id": experiment_id, "upload_data": None})


def handle_uploaded_file(file, experiment_id):
    # check if file is valid zip file
    # if yes, create experiment folder and data folder in it and extract zip file to data folder
    # if no, return error
    try:
        with zipfile.ZipFile(file, 'r') as zip_ref:
            data_folder = os.path.join('data_for_analysis', experiment_id, 'data')
            os.makedirs(data_folder, exist_ok=True)
            zip_ref.extractall(data_folder)
    except zipfile.BadZipFile:
        return False
    return True


def upload_data(request, experiment_id):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            if handle_uploaded_file(request.FILES['data_file'], experiment_id):
                return render(request, "scientistgpt_app/index.html", {"experiment_id": experiment_id, "upload_data": True})
    return render(request, "scientistgpt_app/index.html", {"experiment_id": experiment_id, "upload_data": False})
