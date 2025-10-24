# Agent OS Upload Help - In-App UI Guide

## 🎯 What's New

When you select an **Agent OS** type knowledge base and go to the **KB Management** tab, you'll now see an **in-app help box** that tells you exactly which files to upload and in what order.

## 📍 Where to Find It

1. Open Code-Forge UI: http://localhost:5173
2. Select an **Agent OS** knowledge base from the left sidebar
3. Click the **"KB Management"** tab
4. Look for the blue help box at the top of the "Upload Documents" section

## 📋 What It Says

The help box shows three upload priorities:

### 1️⃣ CRITICAL (Upload First)
```
product/mission.md
product/tech-stack.md
standards/global/*
```
These files give Claude CLI the core understanding of your project.

### 2️⃣ DOMAIN (Upload Second)
```
standards/backend/* (if building APIs)
OR
standards/frontend/* (if building UI)
```
Upload the domain-specific standards based on what you're working on.

### 3️⃣ EXAMPLES (Upload Last)
```
specs/* files
```
Real implementation examples so Claude CLI learns your patterns.

## 🎨 Design Details

The help box includes:
- **Blue icon** (ℹ️) to indicate information
- **Robot emoji** (🤖) to indicate it's for Agent OS
- **Clear step numbers** (1️⃣ 2️⃣ 3️⃣) for priority
- **Link to documentation** for the complete checklist
- **Smooth animation** when the component loads

## 📁 For Your Pistn Project

When you create an "Agent OS" knowledge base for Pistn, the help box will guide you to upload in this order:

**CRITICAL (10 files):**
- product/mission.md
- product/tech-stack.md
- product/roadmap.md
- standards/global/conventions.md
- standards/global/coding-style.md
- standards/global/tech-stack.md
- standards/global/error-handling.md
- standards/global/validation.md
- config.yml
- roles/implementers.yml

**DOMAIN (Choose backend or frontend - 4 files):**
- standards/backend/api.md
- standards/backend/models.md
- standards/backend/queries.md
- standards/backend/migrations.md

OR

- standards/frontend/components.md
- standards/frontend/css.md
- standards/frontend/accessibility.md
- standards/frontend/responsive.md

**EXAMPLES (7 files):**
- specs/2025-10-14-account-users-devise/requirements.md
- specs/2025-10-14-account-users-devise/IMPLEMENTATION.md
- specs/2025-10-15-group-account-rendering/spec.md
- specs/2025-10-15-group-account-rendering/SUMMARY.md
- specs/2025-10-15-group-account-rendering/tasks.md
- specs/2025-10-15-group-account-rendering/CODE_REVIEW.md
- specs/2025-10-15-group-account-rendering/VERIFICATION_SUMMARY.md

## 🔄 How This Works

The UI component (`KBManagement.tsx`) now:

1. **Receives the KB type** from the parent component (MainApp)
2. **Checks if it's "AGENT_OS"** type
3. **Displays the help box** only for Agent OS KBs
4. **Shows prioritized upload guidance** with clear examples
5. **Links to UPLOAD_CHECKLIST.md** for the full detailed list

## 📝 Code Behind It

The help text is in `frontend/src/components/KBManagement.tsx`:

```tsx
{kbType === 'AGENT_OS' && (
  <motion.div className="mb-6 p-4 bg-cool-blue/20 border border-cool-blue/50 rounded-lg">
    {/* Help content here */}
  </motion.div>
)}
```

It only shows when `kbType === 'AGENT_OS'`, so other KB types don't see it.

## 🚀 For Other Users

If someone creates a different KB type (GENERIC, CODE, DOCUMENTATION), they won't see this help box - keeping the UI clean and relevant.

## 💡 Integration with Documentation

The in-app help box works together with:
- **UPLOAD_CHECKLIST.md** - Full prioritized list with copy-paste paths
- **AGENT_OS_SETUP_GUIDE.md** - Complete Agent OS guide
- **PISTN_QUERY_GUIDE.md** - How to query efficiently

Users can:
1. See quick guidance **in the UI**
2. Get the full detailed checklist **from the markdown files**
3. Understand the entire workflow **from the guides**

## 📊 User Experience Flow

```
User: "I want to upload Pistn files"
      ↓
User: Creates "Agent OS" KB type
      ↓
User: Sees blue help box in UI saying upload CRITICAL → DOMAIN → EXAMPLES
      ↓
User: "I need the exact file paths"
      ↓
User: Checks UPLOAD_CHECKLIST.md for copy-paste ready paths
      ↓
User: Successfully uploads files in the right order
      ↓
Claude CLI: Has all the context it needs to be amazing! 🚀
```

---

**The help text is now contextual, in-app, and guides users to the right files without overwhelming the UI!** 🎯