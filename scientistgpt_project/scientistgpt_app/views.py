import uuid

from django.http import JsonResponse
from django.shortcuts import render
import zipfile
from .forms import UploadFileForm
import os
from django.conf import settings


def index(request, experiment_id=None):
    experiment_id = uuid.uuid4().hex
    return render(request, "scientistgpt_app/index.html", {"experiment_id": experiment_id})


def handle_uploaded_file(file, experiment_id):
    """
    check if file is valid zip file
    if yes, create experiment folder and data folder in it and extract zip file to data folder
    if no, return raise error
    """
    try:
        with zipfile.ZipFile(file, 'r') as zip_ref:
            data_folder = os.path.join(settings.BASE_DIR, experiment_id, 'data')
            os.makedirs(data_folder, exist_ok=True)
            zip_ref.extractall(data_folder)
    except zipfile.BadZipFile:
        return False
    return True


# def upload_data(request, experiment_id):
#     if request.method == 'POST':
#         if 'data_file' not in request.FILES:
#             # Return an error response
#             return JsonResponse({'error': 'No file was uploaded.'}, status=400)
#         form = UploadFileForm(request.POST, request.FILES)
#         if form.is_valid():
#             if handle_uploaded_file(request.FILES['data_file'], experiment_id):
#                 return render(request, "scientistgpt_app/index.html", {"experiment_id": experiment_id, "upload_data": 'true'})
#     return render(request, "scientistgpt_app/index.html", {"experiment_id": experiment_id, "upload_data": 'false'})


def upload_data(request, experiment_id):
    if request.method == 'POST':
        if 'data_file' not in request.FILES:
            # Return an error response
            return JsonResponse({'error': 'No file was uploaded.'}, status=400)
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            if handle_uploaded_file(request.FILES['data_file'], experiment_id):
                return JsonResponse({'message': 'File uploaded successfully! You can now enter data and goal description and start the experiment.'})
            else:
                return JsonResponse({'error': 'There was a problem uploading the file. Please check the file format and size.'}, status=400)
        else:
            return JsonResponse({'error': 'Invalid form data. Please check your input.'}, status=400)
    return JsonResponse({'error': 'Invalid request method.'}, status=405)