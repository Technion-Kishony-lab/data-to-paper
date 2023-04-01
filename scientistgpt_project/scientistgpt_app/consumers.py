import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from .views import index

class ScientistGPTConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = "scientistgpt"
        self.room_group_name = "scientistgpt_room"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        data_description = text_data_json["data_description"]
        goal_description = text_data_json["goal_description"]

        await self.run_experiment_and_report_progress(data_description, goal_description)

    async def run_experiment_and_report_progress(self, data_description, goal_description):
        def display_step_status(status_message):
            asyncio.create_task(self.send(text_data=json.dumps({"message": status_message})))

        # Call the index function from views.py
        await index(data_description, goal_description, display_step_status)

    async def display_step_status(self, status_message):
        await self.send(text_data=json.dumps({
            "message": status_message,
        }))