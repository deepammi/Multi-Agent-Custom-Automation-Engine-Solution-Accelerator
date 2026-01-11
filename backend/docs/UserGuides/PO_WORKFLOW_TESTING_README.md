# PO Workflow End-to-End Testing Suite

This testing suite demonstrates the complete "Where is my PO" workflow using the new LangGraph Orchestrator Simplification system. It shows exactly how tasks are processed, which agents are executed, and what messages are shared with users.

## 🎯 What This Demonstrates

The new LangGraph orchestrator provides:
- **AI-driven agent selection** - Intelligent workflow planning
- **Linear execution** - No infinite loops or complex routing
- **Real-time communication** - WebSocket messages for user updates
- **Error handling** - Graceful failure recovery
- **Performance monitoring** - Detailed execution tracking

## 📁 Test Files

### 1. `demo_po_workflow.py` - Interactive Demonstration
**Best for: Understanding the complete workflow**

```bash
python3 demo_po_workflow.py
```

**What it shows:**
- Step-by-step workflow execution with timestamps
- Mock AI responses for predictable results
- WebSocket message flow
- Error scenario handling
- Architecture summary

**Sample Output:**
```
🧪 PO WORKFLOW DEMONSTRATION - MOCK AI
======================================================================
 1. [18:54:58] TASK_SUBMISSION
    User submits PO inquiry
    • Task: Where is my PO-2024-001? I need to check the status and delivery date.

 2. [18:54:58] AI_PLANNING
    AI Planner analyzes task and generates agent sequence
    • Sequence: planner → zoho → salesforce
    • Duration: 45s

 3. [18:54:58] WORKFLOW_START
    Beginning linear agent execution
    📡 WebSocket → agent_message
```

### 2. `test_real_po_workflow.py` - Real AI Testing
**Best for: Testing with actual LLM services**

```bash
python3 test_real_po_workflow.py
```

**What it tests:**
- Real AI Planner responses
- Actual LLM service integration
- Live agent sequence generation
- Production-like execution

**Requirements:**
- LLM service configured (OpenAI, Anthropic, etc.)
- API keys set in environment variables
- Network connectivity

### 3. `test_po_workflow_e2e.py` - Comprehensive Test Suite
**Best for: Automated testing and validation**

```bash
# Run specific tests
python3 -m pytest test_po_workflow_e2e.py::TestPOWorkflowE2E::test_po_workflow_step_by_step_analysis -v -s

# Run all tests
python3 -m pytest test_po_workflow_e2e.py -v -s
```

**Test Coverage:**
- Mock AI workflow execution
- Step-by-step analysis
- Error scenario testing
- Real AI integration (if configured)

### 4. `run_po_tests.py` - Interactive Test Runner
**Best for: Guided testing experience**

```bash
python3 run_po_tests.py
```

**Features:**
- Interactive menu system
- Multiple test scenarios
- Detailed result analysis
- Error handling guidance

## 🔄 Workflow Execution Flow

### Phase 1: Task Submission
```
User Request: "Where is my PO-2024-001?"
    ↓
Plan ID Generated: abc123...
Session ID Generated: def456...
```

### Phase 2: AI Planning
```
AI Planner Analysis:
    ↓
Task Complexity: medium
Required Systems: [zoho, salesforce]
Agent Sequence: [planner, zoho, salesforce]
Estimated Duration: 45s
```

### Phase 3: Graph Creation
```
LinearGraphFactory.create_graph_from_sequence()
    ↓
Graph Type: ai_driven
HITL Enabled: true
Linear Connections: planner → zoho → salesforce → END
```

### Phase 4: Sequential Agent Execution
```
1. Planner Agent:
   • Extract PO number: PO-2024-001
   • Analyze requirements
   • WebSocket: "Analyzing PO tracking request..."

2. Zoho Agent:
   • Query ERP system
   • Find PO status: "In Transit"
   • Get tracking: TRK123456789
   • WebSocket: "Found PO in ERP system..."

3. Salesforce Agent:
   • Check vendor communications
   • Find delivery updates
   • Confirm timeline
   • WebSocket: "Vendor confirms delivery date..."
```

### Phase 5: Result Compilation
```
Final Result:
    ↓
PO Number: PO-2024-001
Status: In Transit
Tracking: TRK123456789
Expected Delivery: January 25, 2024
    ↓
WebSocket: Final formatted result to user
```

## 📊 Sample Test Results

### Mock AI Test Results
```
✅ Mock test completed successfully!
   Final status: completed
   Agent Sequence: planner → zoho → salesforce
   Workflow Steps: 14
   WebSocket Messages: 4
   Execution Time: <1s
```

### Real AI Test Results (when configured)
```
✅ Real AI test completed!
   Final status: completed
   AI Planning: successful
   Generated Sequence: planner → analysis → zoho
   Confidence Score: 0.87
   Total Duration: 23s
```

## 🛠️ Configuration Requirements

### For Mock Testing (Always Works)
No configuration needed - uses mock responses.

### For Real AI Testing
Set environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Or configure in .env file
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

## 🔍 What to Look For

### ✅ Success Indicators
- **Linear Execution**: Agents execute in sequence without loops
- **AI Planning**: Intelligent agent selection based on task
- **WebSocket Flow**: Real-time messages to user
- **Error Handling**: Graceful failure recovery
- **Performance**: Fast execution with caching

### ⚠️ Potential Issues
- **LLM Service**: May not be configured for real AI tests
- **Network**: Connectivity issues with AI APIs
- **Dependencies**: Missing Python packages
- **Permissions**: File access or execution permissions

## 📈 Performance Metrics

The tests track several performance metrics:

### Execution Metrics
- **Total Duration**: End-to-end workflow time
- **Agent Duration**: Time per individual agent
- **AI Planning Time**: Task analysis and sequence generation
- **Graph Compilation**: Linear graph creation time

### System Metrics
- **Cache Hit Rate**: Graph caching effectiveness
- **Memory Usage**: Resource consumption
- **WebSocket Messages**: Communication efficiency
- **Error Rate**: Failure frequency

### Sample Performance Data
```
📊 Performance Summary:
   Workflows: 5 completed
   Avg Duration: 12.3s
   Cache Hit Rate: 85%
   Graph Compilations: 2
   Memory Usage: 45.2 MB
```

## 🚀 Running the Tests

### Quick Start
```bash
# 1. Run the interactive demonstration
python3 demo_po_workflow.py

# 2. Test with real AI (if configured)
python3 test_real_po_workflow.py

# 3. Run comprehensive test suite
python3 -m pytest test_po_workflow_e2e.py -v -s
```

### Interactive Testing
```bash
# Use the guided test runner
python3 run_po_tests.py

# Select from menu:
# 1. Mock AI Test
# 2. Real AI Test  
# 3. Detailed Analysis
# 4. Error Scenarios
# 5. Run All Tests
```

## 🎯 Expected Outcomes

After running these tests, you should see:

1. **Complete Workflow Execution**: From task submission to final result
2. **AI-Driven Planning**: Intelligent agent sequence generation
3. **Linear Agent Flow**: Sequential execution without loops
4. **Real-Time Updates**: WebSocket messages throughout execution
5. **Error Resilience**: Graceful handling of various failure scenarios
6. **Performance Insights**: Detailed metrics and timing information

## 📝 Test Scenarios

### Standard PO Inquiry
- **Input**: "Where is my PO-2024-001?"
- **Expected**: Status lookup with delivery information
- **Agents**: planner → zoho → salesforce

### Complex PO Investigation  
- **Input**: "PO-2024-001 is late, what happened?"
- **Expected**: Multi-system investigation
- **Agents**: planner → zoho → salesforce → gmail

### Error Scenarios
- **Invalid PO**: "Where is PO-INVALID-999?"
- **System Down**: Zoho ERP unavailable
- **Partial Data**: Missing vendor information

## 🔧 Troubleshooting

### Common Issues

**"LLM service not configured"**
- Set API keys in environment variables
- Check .env file configuration
- Verify network connectivity

**"Import errors"**
- Install required dependencies: `pip install -r requirements.txt`
- Check Python path configuration

**"Permission denied"**
- Make scripts executable: `chmod +x *.py`
- Check file permissions

**"Tests fail with real AI"**
- This is expected without proper configuration
- Use mock tests to see workflow structure
- Configure LLM service for real testing

### Getting Help

1. **Check the logs**: Look for detailed error messages
2. **Run mock tests first**: Verify basic functionality
3. **Validate configuration**: Ensure API keys are set
4. **Test connectivity**: Check network access to AI services

## 🎉 Success Criteria

The tests are successful when you can see:

- ✅ Complete workflow execution from start to finish
- ✅ AI-generated agent sequences that make sense
- ✅ Linear execution without infinite loops
- ✅ Real-time WebSocket communication
- ✅ Proper error handling and recovery
- ✅ Performance metrics within expected ranges

This demonstrates that the LangGraph Orchestrator Simplification is working correctly and ready for production use!