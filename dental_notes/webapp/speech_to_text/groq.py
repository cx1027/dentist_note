from groq import Groq

client = Groq()
completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "system",
            "content": "you are an assisitant. user will enter text about converstation, please create summary of the conversation"
        },
        {
            "role": "user",
            "content": "hello, my name is X. hello, my name is Y"
        },
        {
            "role": "assistant",
            "content": "Summary: Two individuals, X and Y, have introduced themselves to each other. The conversation has just begun with a mutual greeting and exchange of names."
        }
    ],
    temperature=1,
    max_completion_tokens=1024,
    top_p=1,
    stream=True,
    stop=None,
)

print(completion.choices[0].message.content)

for chunk in completion:
    print(chunk.choices[0].delta.content or "", end="")
