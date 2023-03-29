import openai

# Set up the OpenAI API client
openai.api_key = "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"

# Set up the model and prompt
model_engine = "gpt-3.5-turbo"

conversation = [
    {'role': 'system',
     'content': 'You are a helpful assistant.'},
]

while True:
    user_input = input('')
    conversation.append({'role': 'user',
                         'content': user_input})
    response = openai.ChatCompletion.create(
        model=model_engine,
        messages=conversation,
    )
    response_message = response['choices'][0]['message']['content']
    conversation.append({
        'role': 'assistant',
        'content': response_message})
    print('\n' + response_message + '\n')
