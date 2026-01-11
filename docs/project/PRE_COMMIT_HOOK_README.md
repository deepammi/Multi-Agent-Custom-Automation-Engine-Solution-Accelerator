# Git Pre-Commit Hook

## Overview

A Git pre-commit hook has been installed to automatically run `npm run build` on the frontend before each commit. This ensures TypeScript compilation errors are caught before code is committed.

## What It Does

When you run `git commit`, the hook will:

1. ✅ Check if any files in `src/frontend/` have been modified
2. ✅ If frontend files changed, run `npm run build` in `src/frontend/`
3. ✅ If build succeeds, allow the commit to proceed
4. ❌ If build fails, block the commit and show the error

## Benefits

- **Catches TypeScript errors early** - No more committing code with type errors
- **Ensures code quality** - Only compilable code gets committed
- **Saves time** - Prevents broken builds from reaching the repository
- **Smart** - Only runs when frontend files are actually changed

## Example Output

### When frontend files are changed:
```bash
$ git commit -m "Update team selector"
🔍 Running pre-commit checks...

📦 Frontend files changed, running build...

🔨 Building frontend...
> Multi Agent frontend@0.1.0 build
> tsc && vite build

✓ 2487 modules transformed.
✓ built in 4.77s

✅ Frontend build successful!

✅ Pre-commit checks passed!

[main abc1234] Update team selector
 2 files changed, 10 insertions(+), 5 deletions(-)
```

### When no frontend files are changed:
```bash
$ git commit -m "Update backend routes"
🔍 Running pre-commit checks...

ℹ️  No frontend changes detected, skipping build.

✅ Pre-commit checks passed!

[main def5678] Update backend routes
 1 file changed, 5 insertions(+), 2 deletions(-)
```

### When build fails:
```bash
$ git commit -m "Add new feature"
🔍 Running pre-commit checks...

📦 Frontend files changed, running build...

🔨 Building frontend...
> Multi Agent frontend@0.1.0 build
> tsc && vite build

src/pages/PlanPage.tsx:123:45 - error TS2339: Property 'foo' does not exist...

❌ Frontend build failed! Please fix the errors before committing.
```

## Bypassing the Hook (Not Recommended)

If you absolutely need to commit without running the build (not recommended), you can use:

```bash
git commit --no-verify -m "Your message"
```

**⚠️ Warning:** Only use `--no-verify` in emergencies. It defeats the purpose of the hook.

## Hook Location

The hook is located at: `.git/hooks/pre-commit`

## Troubleshooting

### Hook not running?

1. Check if the hook file exists:
   ```bash
   ls -la .git/hooks/pre-commit
   ```

2. Check if it's executable:
   ```bash
   chmod +x .git/hooks/pre-commit
   ```

### Build taking too long?

The build typically takes 4-5 seconds. If it's taking longer:
- Check if `node_modules` is up to date: `cd src/frontend && npm install`
- Clear the build cache: `rm -rf src/frontend/build`

## Disabling the Hook

If you need to disable the hook temporarily:

```bash
# Rename the hook
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled

# To re-enable
mv .git/hooks/pre-commit.disabled .git/hooks/pre-commit
```

## Sharing with Team

**Note:** Git hooks are not committed to the repository. Each team member needs to set up the hook manually.

To set up on a new machine:
1. Copy the hook script from this README
2. Save it to `.git/hooks/pre-commit`
3. Make it executable: `chmod +x .git/hooks/pre-commit`

Or use the setup script (if created):
```bash
./setup-git-hooks.sh
```
