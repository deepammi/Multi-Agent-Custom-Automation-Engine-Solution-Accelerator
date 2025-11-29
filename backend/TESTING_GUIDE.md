# LLM Integration Testing Guide

## Quick Start

The Invoice Agent now supports real AI API calls! You can toggle between mock mode (free) and real API mode.

## Test 1: Mock Mode (No API Costs)

This is the default mode - perfect for development and testing.

1. **Ensure mock mode is enabled** in `backend/.env`:
   ```bash
   USE_MOCK_LLM=true
   ```

2. **Start the backend server**:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

3. **Start the frontend** (in another terminal):
   ```bash
   cd src/frontend
   npm run dev
   ```

4. **Test via frontend**:
   - Open http://localhost:5173
   - Submit an invoice-related task: "Check invoice #12345 for accuracy"
   - You should see the hardcoded mock response instantly
   - Check the backend logs - you should see: `🎭 Mock mode is ENABLED`

## Test 2: Real API Mode with OpenAI

This will make actual API calls and incur costs.

1. **Add your OpenAI API key** to `backend/.env`:
   ```bash
   USE_MOCK_LLM=false
   OPENAI_API_KEY=sk-your-actual-key-here
   OPENAI_MODEL=gpt-4o
   ```

2. **Restart the backend server**:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

3. **Test via frontend**:
   - Submit an invoice task: "Analyze invoice #12345 from Acme Corp for $5,000. Check for any issues."
   - You should see the AI response streaming in real-time!
   - Check the backend logs - you should see: `🤖 Invoice Agent calling LLM (streaming mode)`

## Test 3: Real API Mode with Anthropic

1. **Switch to Anthropic** in `backend/.env`:
   ```bash
   USE_MOCK_LLM=false
   LLM_PROVIDER=anthropic
   ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
   ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
   ```

2. **Restart the backend** and test the same way

## Test 4: Local Ollama (Free, but requires Ollama installed)

1. **Install Ollama** (if not already installed):
   ```bash
   # macOS
   brew install ollama
   
   # Or download from https://ollama.ai
   ```

2. **Start Ollama**:
   ```bash
   ollama serve
   ```

3. **Pull a model**:
   ```bash
   ollama pull llama3
   ```

4. **Configure backend** in `backend/.env`:
   ```bash
   USE_MOCK_LLM=false
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3
   ```

5. **Install langchain-ollama**:
   ```bash
   cd backend
   pip install langchain-ollama
   ```

6. **Restart the backend** and test

## Verification Checklist

### Mock Mode
- [ ] Backend logs show `🎭 Mock mode is ENABLED`
- [ ] Response is instant (< 100ms)
- [ ] Response contains "Invoice Agent here. I've processed your request"
- [ ] No API calls are made (check logs)

### Real API Mode
- [ ] Backend logs show `🤖 Invoice Agent calling LLM (streaming mode)`
- [ ] Response streams in real-time (token by token)
- [ ] Response is AI-generated (different each time)
- [ ] Backend logs show completion time and response length
- [ ] WebSocket messages show `agent_stream_start`, `agent_message_streaming`, `agent_stream_end`

## Troubleshooting

### "No module named 'langchain_anthropic'"
```bash
cd backend
pip install langchain-anthropic
```

### "OPENAI_API_KEY environment variable is required"
- Make sure you've added your API key to `.env`
- Make sure you've restarted the backend server after adding the key

### "LLM call timed out"
- Increase the timeout in `.env`: `LLM_TIMEOUT=120`
- Check your internet connection
- Try a different model (e.g., gpt-3.5-turbo is faster)

### Response is still mock even with USE_MOCK_LLM=false
- Make sure you've restarted the backend server
- Check the backend logs to confirm mock mode is disabled
- Verify the .env file has `USE_MOCK_LLM=false` (not `true`)

## Cost Management

### Estimated Costs (as of Nov 2024)

**OpenAI GPT-4o**:
- Input: $2.50 per 1M tokens
- Output: $10.00 per 1M tokens
- Typical invoice task: ~$0.01-0.05 per request

**OpenAI GPT-3.5-turbo** (cheaper alternative):
- Input: $0.50 per 1M tokens
- Output: $1.50 per 1M tokens
- Typical invoice task: ~$0.001-0.01 per request

**Anthropic Claude 3.5 Sonnet**:
- Input: $3.00 per 1M tokens
- Output: $15.00 per 1M tokens
- Typical invoice task: ~$0.01-0.05 per request

**Ollama** (local):
- Free! But requires local compute resources

### Tips to Minimize Costs

1. **Use mock mode for development**: `USE_MOCK_LLM=true`
2. **Use cheaper models for testing**: `OPENAI_MODEL=gpt-3.5-turbo`
3. **Use Ollama for local testing**: Free and private
4. **Set up usage limits** in your OpenAI/Anthropic dashboard
5. **Monitor your usage** regularly

## Next Steps

Once you've verified the Invoice Agent works:

1. **Add error handling** (Task 5)
2. **Add logging** (Task 6)
3. **Extend to other agents** (Closing, Audit)
4. **Add retry logic** for rate limits
5. **Add response caching** to reduce costs

## Support

If you encounter issues:
1. Check the backend logs for error messages
2. Verify your API keys are valid
3. Test with mock mode first to isolate API issues
4. Check the browser console for WebSocket errors
