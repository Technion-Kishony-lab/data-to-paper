from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.http import HttpResponse
from .models import Experiment
from scientistgpt import ScientistGPT, ScientistGPT_ANALYSIS_PLAN


def index(request):
    if request.method == "POST":
        data_description = request.POST["data_description"]
        goal_description = request.POST["goal_description"]

        # Initialize ScientistGPT and run the analysis plan
        scientist_gpt = ScientistGPT(run_plan=ScientistGPT_ANALYSIS_PLAN,
                                     data_description=data_description,
                                     goal_description=goal_description)
        scientist_gpt.run_all(annotate=True)


        # Save the conversation to the database
        experiment = Experiment(data_description=data_description, goal_description=goal_description, conversation=str(scientist_gpt.conversation))
        experiment.save()

        return HttpResponse("Experiment successfully submitted!")

    return render(request, "scientistgpt_app/index.html")