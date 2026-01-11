# 🚀 Gemini AI Quick Start Guide

## Step 1: Get Your API Key

1. **Visit Google AI Studio**: https://makersuite.google.com/app/apikey
2. **Sign in** with your Google account
3. **Click "Create API Key"**
4. **Copy the key** (starts with `AIza...`)

## Step 2: Set Environment Variables

```bash
# Set your API key (replace with your actual key)
export GOOGLE_API_KEY='AIzaSyABC123...'

# Configure Gemini as the LLM provider
export LLM_PROVIDER=gemini
export GEMINI_MODEL=gemini-pro
```

## Step 3: Test the Integration

### Quick Test
```bash
cd backend
python3 test_gemini_simple.py
```

### Full PO Workflow Test
```bash
python3 test_po_workflow_gemini.py
```

### Run E2E Tests with Gemini
```bash
python3 test_po_workflow_e2e.py
```

## Expected Output

When working correctly, you should see:

```
🧪 Simple Gemini AI Test
========================================
✅ API Key found: AIzaSyABC1...
✅ Gemini LLM initialized
🤖 Testing Gemini API call...
📡 agent_stream_start: 
📡 agent_message_streaming: {
📡 agent_message_streaming:   "task_type": "purchase_order_tracking",
📡 agent_message_streaming:   "complexity": "medium",
📡 agent_message_streaming:   "required_systems": ["ERP", "CRM"]
📡 agent_message_streaming: }
📡 agent_stream_end: 
✅ Gemini response received!
   Length: 156 characters
   Preview: {
  "task_type": "purchase_order_tracking",
  "complexity": "medium",
  "required_systems": ["ERP", "CRM"]
}

🎉 Gemini integration is working!
   You can now run: python3 test_po_workflow_gemini.py
```

## Troubleshooting

### "GOOGLE_API_KEY not set"
- Make sure you exported the environment variable
- Check: `echo $GOOGLE_API_KEY`

### "Authentication failed"
- Verify your API key is correct
- Make sure it starts with `AIza`
- Try creating a new key

### "Package not found"
- The required package should already be installed
- If not: `pip install langchain-google-genai`

## Benefits of Using Gemini

✅ **Free**: Generous free tier with no billing required  
✅ **Fast**: Quick response times  
✅ **Smart**: Excellent reasoning capabilities  
✅ **Easy**: Simple setup with just an API key  
✅ **Reliable**: Google's production AI service  

## Next Steps

Once Gemini is working:

1. **Test PO Workflow**: `python3 test_po_workflow_gemini.py`
2. **Run Full Tests**: `python3 test_po_workflow_e2e.py`
3. **Compare with Mock**: See the difference between mock and real AI responses

---

**Ready to start?** Get your API key and run the tests!