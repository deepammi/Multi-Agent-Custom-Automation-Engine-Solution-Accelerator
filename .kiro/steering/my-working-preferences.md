---
inclusion: always
---

# My Working Preferences

## Documentation Guidelines

- **NEVER create summary documentation files** (like `*_SUMMARY.md`, `*_COMPLETE.md`, `*_GUIDE.md`) without explicitly asking first
- These files clutter the workspace and are rarely useful
- If you need to summarize work, do it in the chat response only
- Exception: Only create documentation if I specifically request it

## Command Execution

- **Always use `python3` instead of `python`** when running Python scripts
- This ensures the correct Python version is used on macOS
- Example: `python3 script.py` NOT `python script.py`

## Code Changes

- Focus on minimal, targeted changes
- Don't refactor code unless asked
- Preserve working code patterns
- When debugging, make small incremental changes

## Communication Style

- Be concise and direct
- Don't repeat information unnecessarily
- Get to the point quickly
- Ask clarifying questions when needed

## Testing

- Run tests after making changes
- Use existing test patterns
- Don't create excessive test files

## General Approach

- Follow existing code patterns in the project
- Read documentation when provided
- Make minimal changes to achieve the goal
- Test changes before declaring success
