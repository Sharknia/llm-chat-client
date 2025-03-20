from openai import OpenAI

from models import GrokModels

model = GrokModels()

client = OpenAI(
  api_key=model.get_api_key(),
  base_url="https://api.x.ai/v1",
)


completion = client.chat.completions.create(
    model=model.grok2,
    messages=[
        {
            "role": "system",
            "content": "You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy."
        },
        {
            "role": "user",
            "content": "What is the meaning of life, the universe, and everything?"
        },
    ],
)

print(completion.choices[0].message.content)
