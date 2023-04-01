from django.db import models


# Create your models here.
class Experiment(models.Model):
    data_description = models.TextField()
    goal_description = models.TextField()
    conversation = models.TextField()