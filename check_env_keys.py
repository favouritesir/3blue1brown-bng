import os

for k in ['GEMINI_API_KEY', 'GOOGLE_API_KEY', 'OPENAI_API_KEY', 'MISTRAL_API_KEY']:
    val = os.environ.get(k)
    print(f"{k}: {'SET (len ' + str(len(val)) + ')' if val else 'NOT SET'}")
