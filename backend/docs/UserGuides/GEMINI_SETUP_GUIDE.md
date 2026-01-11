# Gemini AI Setup Guide

This guide helps you set up Google's Gemini AI as the LLM provider for testing the PO workflow with real AI instead of OpenAI.

## 🚀 Quick Setup

### 1. Install Required Package

```bash
pip install langchain-google-genai
```

### 2. Get Google AI API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key (starts with `AIza...`)

### 3. Set Environment Variables

```bash
# Set the API key
export GOOGLE_API_KEY='your-api-key-here'

# Configure Gemini as the LLM provider
export LLM_PROVIDER=gemini
export GEMINI_MODEL=gemini-1.5-pro
export LLM_TEMPERATURE=0.7
```

Or add to your `.env` file:
```env
GOOGLE_API_KEY=your-api-key-here
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-1.5-pro
LLM_TEMPERATURE=0.7
```

## 🧪 Testing

### Automated Setup
```bash
cd backend
python3 setup_gemini.py
```

### Test Gemini Integration
```bash
python3 test_gemini_integration.py
```

### Test PO Workflow with Gemini
```bash
python3 test_po_workflow_gemini.py
```

### Run Full E2E Tests with Gemini
```bash
python3 test_po_workflow_e2e.py
```

## 📋 Available Models

Gemini supports several models:
- `gemini-1.5-pro` (recommended) - Most capable model
- `gemini-1.5-flash` - Faster, lighter model
- `gemini-pro` - Previous generation

Set via environment variable:
```bash
export GEMINI_MODEL=gemini-1.5-pro
```

## 🔧 Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `GOOGLE_API_KEY` | Required | Your Google AI API key |
| `LLM_PROVIDER` | `openai` | Set to `gemini` or `google` |
| `GEMINI_MODEL` | `gemini-1.5-pro` | Gemini model to use |
| `LLM_TEMPERATURE` | `0.7` | Response creativity (0.0-1.0) |
| `LLM_TIMEOUT` | `60` | Request timeout in seconds |

## 🎯 Expected Results

When working correctly, you should see:

```
🧪 Testing PO Workflow with Gemini AI
============================================================
✅ GOOGLE_API_KEY found: AIzaSyABC...
✅ LLM_PROVIDER set to: gemini
✅ GEMINI_MODEL set to: gemini-1.5-pro

1️⃣  Running Mock AI Test (baseline)...
✅ Mock test passed - proceeding with Gemini test

2️⃣  Running Real Gemini AI Test...
🎉 Gemini AI test SUCCESSFUL!
   Status: completed
   Agent Sequence: planner → zoho → salesforce
   AI Planning: ✅ Success
   Total Duration: 45.2s
```

## 🛠️ Troubleshooting

### API Key Issues
- **Error**: `GOOGLE_API_KEY environment variable is required`
- **Solution**: Make sure you've set the API key correctly
- **Check**: `echo $GOOGLE_API_KEY` should show your key

### Package Issues
- **Error**: `langchain-google-genai package is required`
- **Solution**: `pip install langchain-google-genai`
- **Check**: `python3 -c "import langchain_google_genai; print('OK')"`

### Authentication Issues
- **Error**: `Authentication failed`
- **Solution**: Verify your API key is valid and has proper permissions
- **Check**: Test with a simple API call

### Rate Limiting
- **Error**: `Rate limit exceeded`
- **Solution**: Wait a moment and try again
- **Note**: Gemini has generous free tier limits

## 🔄 Switching Between Providers

You can easily switch between different LLM providers:

```bash
# Use OpenAI
export LLM_PROVIDER=openai
export OPENAI_API_KEY=your-openai-key

# Use Anthropic
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=your-anthropic-key

# Use Gemini
export LLM_PROVIDER=gemini
export GOOGLE_API_KEY=your-google-key

# Use local Ollama
export LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434
```

## 📊 Performance Comparison

| Provider | Speed | Cost | Quality | Setup |
|----------|-------|------|---------|-------|
| Gemini 1.5 Pro | Fast | Free tier | Excellent | Easy |
| OpenAI GPT-4 | Medium | Paid | Excellent | Easy |
| Anthropic Claude | Medium | Paid | Excellent | Easy |
| Ollama (local) | Varies | Free | Good | Complex |

## 🎉 Benefits of Gemini

1. **Free Tier**: Generous free usage limits
2. **Fast**: Quick response times
3. **Capable**: Excellent reasoning and analysis
4. **Easy Setup**: Simple API key configuration
5. **No Billing**: No credit card required for testing

## 📚 Additional Resources

- [Google AI Studio](https://makersuite.google.com/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [LangChain Google GenAI Integration](https://python.langchain.com/docs/integrations/chat/google_generative_ai)

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your API key at [Google AI Studio](https://makersuite.google.com/)
3. Run the diagnostic tests: `python3 test_gemini_integration.py`
4. Check the logs for detailed error messages

---

**Ready to test?** Run `python3 test_po_workflow_gemini.py` to get started!