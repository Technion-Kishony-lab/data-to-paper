from data_to_paper_new.chatgpt_client.chatgpt_models import ModelEngine
from data_to_paper_new.chatgpt_client.gpt_client import ChatGptClient
from data_to_paper_new.converser.converser import Conversor, RequestHistoryTypes
from data_to_paper_new.roles.scientist import Scientist


print("This is a test of what a converser sub type could look like?")
print("Create gpt client")

gpt_client = ChatGptClient(ModelEngine.GPT35_TURBO)
role = Scientist()
conversor = Conversor("test chat", role, gpt_client)


answer = conversor.query_chatgpt(RequestHistoryTypes.NO_HISTORY, "Please Explain about the fibonacci sequence")
print(answer)
print("================")

answer1 = conversor.query_chatgpt(RequestHistoryTypes.ALL_CHAT_HISTORY, "Can you back it up with quotes?")
print(answer1)
print("================")

answer2 = conversor.regenerate_last_response()
print(answer2)
print("================")


conversor.replace_last_response("I dont know how")
answer3 = conversor.query_chatgpt(RequestHistoryTypes.ALL_CHAT_HISTORY, "Are you sure?")
print(answer3)
print("================")





