# Manual Testing Checklist

## ✅ Completed Tests

- [x] OpenAI API integration working
- [x] Streaming responses functional
- [x] Mock mode working
- [x] Prompt building correct
- [x] Provider configuration working

## Remaining Manual Tests

### Mock Mode Tests

- [ ] **Test 1**: Submit invoice task with `USE_MOCK_LLM=true`
  - Expected: Instant response with hardcoded text
  - Verify: Backend logs show `🎭 Mock mode is ENABLED`

- [ ] **Test 2**: Check response time
  - Expected: < 100ms
  - Verify: No API calls in logs

### Real API Mode Tests (OpenAI)

- [x] **Test 3**: Submit invoice task with OpenAI
  - Expected: AI-generated response streams in real-time
  - Verify: Backend logs show `🤖 Invoice Agent calling LLM`

- [ ] **Test 4**: Verify streaming in browser
  - Open browser DevTools → Network → WS
  - Expected: See `agent_stream_start`, `agent_message_streaming`, `agent_stream_end`

- [ ] **Test 5**: Test with different models
  - Try `gpt-4o-mini` (faster/cheaper)
  - Try `gpt-3.5-turbo` (cheapest)
  - Verify: Different response styles

### Error Handling Tests

- [ ] **Test 6**: Invalid API key
  - Set `OPENAI_API_KEY=sk-invalid`
  - Expected: Clear error message about authentication
  - Verify: Logs show `❌ Authentication failed`

- [ ] **Test 7**: Timeout
  - Set `LLM_TIMEOUT=1`
  - Expected: Timeout error after 1 second
  - Verify: Logs show `❌ LLM call timed out`

- [ ] **Test 8**: Rate limit (if possible)
  - Make many rapid requests
  - Expected: Automatic retry with backoff
  - Verify: Logs show `⏳ Rate limit hit, retrying`

### Logging Tests

- [ ] **Test 9**: Check log format
  - Submit a task
  - Verify logs contain:
    - `[plan_id=...]`
    - `[agent=Invoice]`
    - `[duration=...s]`
    - `[response_length=... chars]`

- [ ] **Test 10**: API key sanitization
  - Check all logs
  - Verify: No API keys visible (should see `[REDACTED]`)

### Provider Switching Tests

- [ ] **Test 11**: Switch to Anthropic
  - Set `LLM_PROVIDER=anthropic`
  - Add `ANTHROPIC_API_KEY`
  - Expected: Works with Claude
  - Verify: Logs show Anthropic initialization

- [ ] **Test 12**: Switch to Ollama (if installed)
  - Set `LLM_PROVIDER=ollama`
  - Expected: Works with local model
  - Verify: No API costs

### Integration Tests

- [ ] **Test 13**: Full workflow
  - Submit task → Approve plan → Get AI response
  - Expected: Complete end-to-end flow works
  - Verify: All WebSocket messages received

- [ ] **Test 14**: Other agents still work
  - Submit closing task
  - Submit audit task
  - Expected: Planner routes correctly
  - Verify: Other agents use mock responses (not updated yet)

### Frontend Tests

- [ ] **Test 15**: Response displays correctly
  - Submit invoice task
  - Expected: Response appears in chat
  - Verify: Formatting is preserved

- [ ] **Test 16**: Streaming visible
  - Watch response appear
  - Expected: Token-by-token streaming visible
  - Verify: Smooth animation

- [ ] **Test 17**: Error messages
  - Trigger an error (invalid key)
  - Expected: User-friendly error message
  - Verify: No technical details exposed

## Test Results

### Environment
- OS: macOS
- Python: 3.11
- Backend: FastAPI
- Frontend: React + Vite

### Test Date: [Fill in]

### Notes
- OpenAI test successful ✅
- Streaming working ✅
- Mock mode working ✅
- [Add more notes as you test]

## Issues Found

| Issue | Severity | Status | Notes |
|-------|----------|--------|-------|
| - | - | - | - |

## Sign-off

- [ ] All critical tests passed
- [ ] Documentation reviewed
- [ ] Ready for production use

Tested by: _______________
Date: _______________
