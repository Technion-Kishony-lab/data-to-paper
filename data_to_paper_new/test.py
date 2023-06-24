from data_to_paper_new.chatgpt_client.chatgpt_models import ModelEngine
from data_to_paper_new.chatgpt_client.gpt_client import ChatGptClient
from data_to_paper_new.converser.converser import Conversor, RequestHistoryTypes
from data_to_paper_new.roles.scientist import Scientist

print("The test starts")
print("Create gpt client")
gpt_client = ChatGptClient(ModelEngine.GPT35_TURBO)
role = Scientist()
conversor = Conversor("test chat", role, gpt_client)


answer1 = conversor.query_chatgpt(RequestHistoryTypes.NO_HISTORY, "What is the square root of 1882")
print(answer1)

answer = conversor.query_chatgpt(RequestHistoryTypes.ALL_CHAT_HISTORY, "Can you repeat that in hebrew?")
print(answer)


print("Creating a new conversation")


