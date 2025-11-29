# How to Set Your OpenAI API Key

You have two options:

## Option 1: Add to .env file (Recommended)

Edit `backend/.env` and uncomment/update this line:

```bash
# Change this:
# OPENAI_API_KEY=sk-your-key-here

# To this (with your actual key):
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

Also set:
```bash
USE_MOCK_LLM=false
```

Then run the test:
```bash
cd backend
python test_openai_quick.py
```

## Option 2: Set as environment variable

In your terminal:

```bash
export OPENAI_API_KEY=sk-proj-your-actual-key-here
cd backend
python test_openai_quick.py
```

## Verify it's set

```bash
cd backend
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Key:', os.getenv('OPENAI_API_KEY', 'NOT SET')[:15] + '...')"
```

You should see something like:
```
Key: sk-proj-abc123...
```

## Get an API Key

If you don't have an OpenAI API key:

1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-proj-` or `sk-`)
5. Add it to your `.env` file

## Test with Mock Mode First

If you want to test without API costs first:

```bash
# In backend/.env
USE_MOCK_LLM=true
```

Then start the server and test via the frontend.
