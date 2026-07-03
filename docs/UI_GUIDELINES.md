# Pocket — UI Design Guidelines

> **Version:** 1.0.0
> **Last Updated:** 2026-07-03
> **Status:** Authoritative
> **Audience:** Claude Code, development agents

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Technology Stack](#2-technology-stack)
3. [Color System](#3-color-system)
4. [Typography](#4-typography)
5. [Spacing & Layout](#5-spacing--layout)
6. [Motion & Animation](#6-motion--animation)
7. [Component Library](#7-component-library)
8. [Interaction Patterns](#8-interaction-patterns)
9. [Page Templates](#9-page-templates)
10. [States](#10-states)
11. [Icons](#11-icons)
12. [Accessibility](#12-accessibility)
13. [Responsive Design](#13-responsive-design)
14. [Code Conventions](#14-code-conventions)

---

## 1. Design Philosophy

### 1.1 Design References

Pocket's UI draws inspiration from:

| Reference | What to Take |
|-----------|-------------|
| **Linear** | Issue tracker layout, keyboard-first UX, transitions |
| **Cursor** | IDE-grade split views, command palette, dark theme |
| **Raycast** | Command palette design, instant search, minimal chrome |
| **Claude** | Conversation UI, clean message bubbles, markdown rendering |
| **Vercel Dashboard** | Dashboard metrics, card layouts, subtle gradients |
| **Notion** | Block editor, sidebar navigation, page hierarchy |
| **Obsidian** | Graph view, markdown-first, local-first feel |

### 1.2 Core Principles

| Principle | Rule |
|-----------|------|
| **Developer-first** | Designed for power users. Keyboard shortcuts for everything. |
| **Minimal** | Every pixel must justify its existence. No decorative clutter. |
| **Pixel-perfect** | Consistent alignment, spacing, and typography across all views. |
| **Dark mode first** | Design in dark mode, then adapt to light. Not the other way around. |
| **Keyboard-first** | Every action reachable via keyboard. Mouse is optional. |
| **Extremely responsive** | UI must feel instant. < 100ms for interactions, < 300ms for transitions. |
| **No admin templates** | Build from primitives (shadcn/ui), not pre-built admin dashboards. |
| **No Material Design** | No MD components, elevation system, or FABs. |

### 1.3 What Pocket UI is NOT

- ❌ Not an admin panel
- ❌ Not a form-heavy CRUD app
- ❌ Not a colorful consumer product
- ❌ Not a Material Design app
- ❌ Not a Bootstrap template
- ❌ Not a dashboard-first tool

### 1.4 What Pocket UI IS

- ✅ A professional tool that feels like a native desktop app
- ✅ A keyboard-driven, minimal workspace
- ✅ A dark, focused environment for deep work
- ✅ A responsive, instant-feedback interface
- ✅ A context-aware, intelligent assistant

---

## 2. Technology Stack

### 2.1 Frontend Framework & Libraries

| Technology | Purpose |
|-----------|---------|
| **Next.js (App Router)** | Framework, routing, SSR/SSG |
| **React** | UI library |
| **TypeScript (strict)** | Type safety |
| **Tailwind CSS** | Utility-first styling, CSS variables for theming |
| **shadcn/ui** | Component primitives (built on Radix UI) |
| **Radix UI** | Accessible unstyled primitives |
| **Lucide React** | Icon library |
| **@monaco-editor/react** | Code/markdown editor |
| **react-markdown + remark-gfm + rehype-highlight** | Markdown rendering |
| **@xyflow/react (ReactFlow)** | Context graph visualization |
| **TanStack Query** | Server state management |
| **React Hook Form + Zod** | Form handling + validation |
| **Framer Motion** | Animations and transitions |

### 2.2 Font Loading

```css
/* Self-hosted fonts for performance */
@font-face {
  font-family: 'Geist Sans';
  src: url('/fonts/GeistVF.woff2') format('woff2-variations');
  font-weight: 100 900;
  font-display: swap;
}

@font-face {
  font-family: 'Geist Mono';
  src: url('/fonts/GeistMonoVF.woff2') format('woff2-variations');
  font-weight: 100 900;
  font-display: swap;
}
```

Fallback: `Inter`, `system-ui`, `-apple-system`, `BlinkMacSystemFont`, `'Segoe UI'`, `sans-serif`.

---

## 3. Color System

### 3.1 Design Approach

- **Dark mode is the primary design mode.** Light mode is secondary.
- Colors are defined as **CSS custom properties** on `:root` and `[data-theme="light"]`.
- Tailwind references these variables for seamless theme switching.
- Color palette is **neutral-focused** with a single accent color.

### 3.2 Color Tokens

#### Dark Mode (Default)

```css
:root {
  /* Backgrounds */
  --bg-primary: #09090B;         /* Main app background */
  --bg-secondary: #18181B;       /* Panels, sidebars, cards */
  --bg-tertiary: #27272A;        /* Elevated surfaces, dropdowns */
  --bg-hover: #2D2D30;           /* Hover state backgrounds */
  --bg-active: #3F3F46;          /* Active/selected state */

  /* Text */
  --text-primary: #FAFAFA;       /* Primary text */
  --text-secondary: #A1A1AA;     /* Secondary/muted text */
  --text-tertiary: #71717A;      /* Placeholder, disabled text */
  --text-inverse: #09090B;       /* Text on light backgrounds */

  /* Borders */
  --border-default: #27272A;     /* Default borders */
  --border-subtle: #1F1F23;      /* Subtle/light borders */
  --border-strong: #3F3F46;      /* Strong borders, dividers */
  --border-focus: #3B82F6;       /* Focus ring color */

  /* Accent (Primary actions, links, CTAs) */
  --accent-primary: #3B82F6;     /* Blue-600: primary buttons, links */
  --accent-primary-hover: #2563EB; /* Blue-700: hover state */
  --accent-primary-subtle: rgba(59, 130, 246, 0.1); /* Background for accent areas */

  /* Semantic Colors */
  --success: #22C55E;            /* Green-500 */
  --success-subtle: rgba(34, 197, 94, 0.1);
  --warning: #EAB308;            /* Yellow-500 */
  --warning-subtle: rgba(234, 179, 8, 0.1);
  --error: #EF4444;              /* Red-500 */
  --error-subtle: rgba(239, 68, 68, 0.1);
  --info: #3B82F6;               /* Blue-500 */
  --info-subtle: rgba(59, 130, 246, 0.1);

  /* Context Type Colors (for badges/indicators) */
  --ctx-persona: #8B5CF6;       /* Violet */
  --ctx-role: #06B6D4;          /* Cyan */
  --ctx-instruction: #3B82F6;   /* Blue */
  --ctx-knowledge: #22C55E;     /* Green */
  --ctx-constraint: #EAB308;    /* Yellow */
  --ctx-example: #F97316;       /* Orange */
  --ctx-reference: #EC4899;     /* Pink */
  --ctx-snippet: #6366F1;       /* Indigo */

  /* Prompt Score Colors */
  --score-excellent: #22C55E;   /* 0.8 - 1.0 */
  --score-good: #3B82F6;        /* 0.6 - 0.8 */
  --score-fair: #EAB308;        /* 0.4 - 0.6 */
  --score-poor: #EF4444;        /* 0.0 - 0.4 */
}
```

#### Light Mode

```css
[data-theme="light"] {
  /* Backgrounds */
  --bg-primary: #FFFFFF;
  --bg-secondary: #F8FAFC;
  --bg-tertiary: #F1F5F9;
  --bg-hover: #E2E8F0;
  --bg-active: #CBD5E1;

  /* Text */
  --text-primary: #0F172A;
  --text-secondary: #64748B;
  --text-tertiary: #94A3B8;
  --text-inverse: #FAFAFA;

  /* Borders */
  --border-default: #E2E8F0;
  --border-subtle: #F1F5F9;
  --border-strong: #CBD5E1;
  --border-focus: #3B82F6;

  /* Accent (same as dark) */
  --accent-primary: #3B82F6;
  --accent-primary-hover: #2563EB;
  --accent-primary-subtle: rgba(59, 130, 246, 0.08);

  /* Semantic (same as dark) */
}
```

### 3.3 Tailwind Configuration

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class", "[data-theme='dark']"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "var(--bg-primary)",
          secondary: "var(--bg-secondary)",
          tertiary: "var(--bg-tertiary)",
          hover: "var(--bg-hover)",
          active: "var(--bg-active)",
        },
        text: {
          primary: "var(--text-primary)",
          secondary: "var(--text-secondary)",
          tertiary: "var(--text-tertiary)",
        },
        border: {
          DEFAULT: "var(--border-default)",
          subtle: "var(--border-subtle)",
          strong: "var(--border-strong)",
          focus: "var(--border-focus)",
        },
        accent: {
          DEFAULT: "var(--accent-primary)",
          hover: "var(--accent-primary-hover)",
          subtle: "var(--accent-primary-subtle)",
        },
        success: "var(--success)",
        warning: "var(--warning)",
        error: "var(--error)",
        info: "var(--info)",
      },
      fontFamily: {
        sans: ["Geist Sans", "Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["Geist Mono", "JetBrains Mono", "Fira Code", "monospace"],
      },
    },
  },
};
```

---

## 4. Typography

### 4.1 Font Stack

| Use | Font | Fallback |
|-----|------|----------|
| **UI (primary)** | Geist Sans | Inter, system-ui |
| **Code & Editor** | Geist Mono | JetBrains Mono, Fira Code, monospace |

### 4.2 Type Scale

| Name | Size | Weight | Line Height | Tracking | Usage |
|------|------|--------|-------------|----------|-------|
| `h1` | 3rem (48px) | 800 (Extra Bold) | 1.1 | -0.02em (tight) | Page titles |
| `h2` | 2.25rem (36px) | 700 (Bold) | 1.2 | -0.02em (tight) | Section headers |
| `h3` | 1.5rem (24px) | 600 (Semi-bold) | 1.3 | -0.01em | Subsection headers |
| `h4` | 1.25rem (20px) | 600 (Semi-bold) | 1.4 | normal | Card titles |
| `body` | 1rem (16px) | 400 (Regular) | 1.75 (relaxed) | normal | Body text |
| `body-sm` | 0.875rem (14px) | 400 (Regular) | 1.5 | normal | Secondary text, table cells |
| `small` | 0.875rem (14px) | 500 (Medium) | 1.5 | normal | Tags, badges, labels |
| `caption` | 0.75rem (12px) | 500 (Medium) | 1.5 | 0.02em | Timestamps, metadata |
| `code` | 0.875rem (14px) | 400 (Regular) | 1.6 | normal | Inline code |
| `code-block` | 0.8125rem (13px) | 400 (Regular) | 1.7 | normal | Code blocks, editor |

### 4.3 CSS Implementation

```css
/* Typography scale */
.h1 { font-size: 3rem; font-weight: 800; line-height: 1.1; letter-spacing: -0.02em; }
.h2 { font-size: 2.25rem; font-weight: 700; line-height: 1.2; letter-spacing: -0.02em; }
.h3 { font-size: 1.5rem; font-weight: 600; line-height: 1.3; letter-spacing: -0.01em; }
.h4 { font-size: 1.25rem; font-weight: 600; line-height: 1.4; }
.body { font-size: 1rem; font-weight: 400; line-height: 1.75; }
.body-sm { font-size: 0.875rem; font-weight: 400; line-height: 1.5; }
.small { font-size: 0.875rem; font-weight: 500; line-height: 1.5; }
.caption { font-size: 0.75rem; font-weight: 500; line-height: 1.5; letter-spacing: 0.02em; }
```

---

## 5. Spacing & Layout

### 5.1 Spacing Scale (4px Grid)

All spacing values are multiples of 4px:

| Token | Value | Usage |
|-------|-------|-------|
| `space-0` | 0px | Reset |
| `space-0.5` | 2px | Hairline gaps |
| `space-1` | 4px | Tight inner padding, icon gaps |
| `space-1.5` | 6px | Badge padding |
| `space-2` | 8px | Small padding, gap between inline items |
| `space-3` | 12px | Standard padding, card inner padding |
| `space-4` | 16px | Standard gap, section padding |
| `space-5` | 20px | Card padding |
| `space-6` | 24px | Section gaps |
| `space-8` | 32px | Large section gaps |
| `space-10` | 40px | Page margins |
| `space-12` | 48px | Large page gaps |
| `space-16` | 64px | Extreme spacing |

### 5.2 Layout Dimensions

```
┌──────────────────────────────────────────────────────┐
│ Sidebar (240px fixed)  │   Main Content              │
│                        │                              │
│ ┌────────────────────┐ │ ┌─── Header (56px) ────────┐│
│ │ Workspace Switcher │ │ │ Breadcrumb     Actions   ││
│ │ (48px)             │ │ └──────────────────────────┘│
│ ├────────────────────┤ │                              │
│ │                    │ │ ┌─── Content ──────────────┐│
│ │  Navigation        │ │ │                          ││
│ │  Items             │ │ │  max-width: 1200px       ││
│ │                    │ │ │  padding: 24px            ││
│ │                    │ │ │                          ││
│ │                    │ │ └──────────────────────────┘│
│ │                    │ │                              │
│ ├────────────────────┤ │                              │
│ │ Favorites (opt.)   │ │                              │
│ ├────────────────────┤ │                              │
│ │ Settings / Theme   │ │                              │
│ └────────────────────┘ │                              │
└──────────────────────────────────────────────────────┘
```

| Element | Dimension |
|---------|-----------|
| **Sidebar width** | 240px (collapsible to 48px icon-only) |
| **Header height** | 56px |
| **Content max-width** | 1200px (centered) |
| **Content padding** | 24px |
| **Card border-radius** | 8px |
| **Button border-radius** | 6px |
| **Input border-radius** | 6px |
| **Badge border-radius** | 4px (or `9999px` for pill) |
| **Modal border-radius** | 12px |

### 5.3 Grid System

Use CSS Grid and Flexbox. No grid framework.

```css
/* Dashboard grid */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

/* Two-column layout (editor + preview) */
.split-view {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px; /* Border effect */
  background: var(--border-default);
}

/* Three-column layout (list + detail + preview) */
.triple-view {
  display: grid;
  grid-template-columns: 300px 1fr 400px;
  height: calc(100vh - 56px);
}
```

---

## 6. Motion & Animation

### 6.1 Timing Principles

| Duration | Usage | Easing |
|----------|-------|--------|
| **100ms** | Micro-interactions: hover, focus, active | `ease-out` |
| **150ms** | Button press, toggle, checkbox | `ease-out` |
| **200ms** | Dropdown open/close, tooltip show | `ease-in-out` |
| **250ms** | Sidebar collapse/expand, panel slide | `ease-in-out` |
| **300ms** | Modal open, page transitions | `cubic-bezier(0.16, 1, 0.3, 1)` |
| **400ms** | Complex layout shifts, graph animations | `cubic-bezier(0.16, 1, 0.3, 1)` |

### 6.2 Framer Motion Variants

```typescript
// src/lib/motion.ts

export const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  transition: { duration: 0.2 },
};

export const slideUp = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 8 },
  transition: { duration: 0.25, ease: [0.16, 1, 0.3, 1] },
};

export const slideIn = {
  initial: { opacity: 0, x: -12 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -12 },
  transition: { duration: 0.25, ease: [0.16, 1, 0.3, 1] },
};

export const scaleIn = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.95 },
  transition: { duration: 0.2, ease: [0.16, 1, 0.3, 1] },
};

export const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.05,
    },
  },
};

export const staggerItem = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.2 },
};

// Modal overlay
export const overlayVariants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
  transition: { duration: 0.15 },
};

// Modal content
export const modalVariants = {
  initial: { opacity: 0, scale: 0.95, y: 10 },
  animate: { opacity: 1, scale: 1, y: 0 },
  exit: { opacity: 0, scale: 0.95, y: 10 },
  transition: { duration: 0.25, ease: [0.16, 1, 0.3, 1] },
};
```

### 6.3 Animation Rules

| Rule | Detail |
|------|--------|
| **Prefer transforms** | Use `transform` and `opacity` only. Never animate `width`, `height`, `margin`. |
| **Reduce motion** | Respect `prefers-reduced-motion`. Disable all non-essential animations. |
| **No bounce** | No spring/bounce effects. Use smooth ease curves. |
| **Subtle is better** | Small movements (4-12px). Never large, distracting animations. |
| **Purpose-driven** | Every animation must communicate state change. No decoration. |
| **Consistent timing** | Same type of animation always uses same duration. |

### 6.4 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

```typescript
// In React components
import { useReducedMotion } from "framer-motion";

function Component() {
  const shouldReduceMotion = useReducedMotion();
  return (
    <motion.div
      animate={{ opacity: 1, y: shouldReduceMotion ? 0 : 8 }}
    />
  );
}
```

---

## 7. Component Library

### 7.1 Base Components (shadcn/ui)

Install and customize these shadcn/ui components:

| Component | Customization |
|-----------|--------------|
| `Button` | Sizes: `sm` (32px), `default` (36px), `lg` (40px). Variants: `default`, `secondary`, `ghost`, `destructive`, `outline`. |
| `Input` | Height: 36px. Border: `var(--border-default)`. Focus: `var(--border-focus)` ring. |
| `Select` | Same height as Input. Custom dropdown with search. |
| `Dialog` | Centered modal. Overlay: `rgba(0,0,0,0.5)`. Max-width: 480px default. |
| `DropdownMenu` | Width: 200px min. Items: 32px height. Separator between groups. |
| `Tooltip` | Delay: 500ms show, 0ms hide. Dark background even in light mode. |
| `Badge` | Height: 22px. Pill shape. Semantic colors for context types. |
| `Skeleton` | Pulse animation. Match exact dimensions of content being loaded. |
| `Toast` | Bottom-right position. Auto-dismiss: 5s. Variants: success, error, info. |
| `Tabs` | Bottom border style (not boxed). Active: accent color underline. |
| `Separator` | 1px `var(--border-default)`. |
| `ScrollArea` | Custom thin scrollbar. Auto-hide. |
| `Popover` | Same style as DropdownMenu. Trigger on click. |
| `Command` | Full command palette component. See interaction patterns. |
| `Sheet` | Side panel (right). Width: 400px. Overlay. |

### 7.2 Custom Components

#### Sidebar Navigation

```
┌────────────────────┐
│ 🔲 Workspace ▾     │ ← Workspace Switcher (dropdown)
├────────────────────┤
│ 🏠 Dashboard       │ ← Navigation items
│ 📚 Contexts        │
│ 📝 Templates       │
│ { } Variables      │
│ 🔨 Builder         │
│ 🕸️ Graph           │
│ 💬 Conversations   │
│ 📊 Analytics       │
│ 📓 Journals        │
├────────────────────┤
│ ★ Favorites        │ ← Collapsible section
│   └── Context A    │
│   └── Template B   │
├────────────────────┤
│ ⚙️ Settings        │ ← Bottom-pinned
│ 🌙/☀️ Theme Toggle │
└────────────────────┘
```

- Width: 240px (collapsible to 48px)
- Background: `var(--bg-secondary)`
- Border-right: `var(--border-default)`
- Active item: `var(--bg-active)` background + accent left border (2px)
- Hover: `var(--bg-hover)` background
- Keyboard: Arrow keys navigate, Enter selects
- Collapse: `Cmd+\` or `Ctrl+\`

#### Command Palette

```
┌──────────────────────────────────────────────┐
│ 🔍 Type a command or search...              │
├──────────────────────────────────────────────┤
│ Recently Used                                │
│   📚 Go to Contexts              ⌘ + 1      │
│   🔨 Open Prompt Builder         ⌘ + B      │
│   💬 New Conversation            ⌘ + N      │
├──────────────────────────────────────────────┤
│ Actions                                      │
│   ➕ Create Context              ⌘ + Shift + C │
│   ➕ Create Template             ⌘ + Shift + T │
│   🔍 Search Everywhere          ⌘ + Shift + F │
│   🤖 AI Enhance                              │
│   🤖 AI Critique                             │
├──────────────────────────────────────────────┤
│ Switch Workspace                             │
│   📁 SoftwareONE                             │
│   📁 Personal                                │
└──────────────────────────────────────────────┘
```

- Trigger: `Cmd+K` / `Ctrl+K`
- Width: 560px, centered
- Max height: 400px (scrollable)
- Search: Fuzzy match, instant results
- Keyboard: Arrow keys navigate, Enter executes, Esc closes
- Groups: Recently Used, Navigation, Actions, Workspaces
- Animation: `scaleIn` variant (fade + scale from 95%)

#### Context Card

```
┌─────────────────────────────────────────────┐
│ 🟣 persona   ★                    ⋯ (menu) │ ← Badge (colored by type) + favorite + action menu
│                                             │
│ Senior Python Developer                     │ ← Title (h4, semi-bold)
│                                             │
│ Expert Python developer focused on          │ ← Content preview (2 lines, muted)
│ clean architecture and type safety...       │
│                                             │
│ python  architecture  clean-code            │ ← Tags (badges)
│                                             │
│ 🔢 1,240 tokens  |  📊 42 uses  |  2h ago │ ← Metadata footer (caption)
└─────────────────────────────────────────────┘
```

- Background: `var(--bg-secondary)`
- Border: `var(--border-default)`, 1px
- Border-radius: 8px
- Padding: 16px
- Hover: `var(--bg-hover)` background, subtle scale (1.005)
- Active/selected: `var(--accent-primary-subtle)` background + accent border-left
- Type badge: colored by `--ctx-{type}` variable

#### Token Counter

```
┌─────────────────────────────────────────────┐
│ Tokens: 12,450 / 128,000 (9.7%)            │
│ ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│ Est. Cost: $0.0124                           │
└─────────────────────────────────────────────┘
```

- Progress bar colored by utilization:
  - < 50%: `var(--success)`
  - 50-80%: `var(--warning)`
  - > 80%: `var(--error)`
- Updates in real-time as content changes (debounced 300ms)

#### Prompt Score Indicator

```
┌──────────┐
│    85    │ ← Large number, colored by score
│  /100    │ ← Caption
│ ████████ │ ← Color bar
│  Good    │ ← Label
└──────────┘
```

- Score colors:
  - 80-100: `var(--score-excellent)` — "Excellent"
  - 60-79: `var(--score-good)` — "Good"
  - 40-59: `var(--score-fair)` — "Fair"
  - 0-39: `var(--score-poor)` — "Poor"

#### Chat Message Bubble

```
┌─────────────────────────────────────────────┐
│ 👤 You                            10:32 AM │
│                                             │
│ Explain the architecture of Pocket's AI     │
│ pipeline.                                    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ 🤖 Assistant           gpt-4.1   10:32 AM │
│                                             │
│ The AI pipeline in Pocket consists of 18    │
│ sequential steps...                          │
│                                             │
│ ```python                                    │
│ class PipelineOrchestrator:                  │
│     ...                                      │
│ ```                                          │
│                                             │
│ 📊 1,240 tokens  |  $0.0035  |  2.1s       │
│                                             │
│ 📝 Copy  |  🔄 Regenerate  |  👍 👎       │
└─────────────────────────────────────────────┘
```

- User messages: `var(--bg-tertiary)` background, right-aligned context
- Assistant messages: `var(--bg-secondary)` background
- Markdown rendered with `react-markdown` + `rehype-highlight`
- Code blocks: `var(--bg-primary)` background with syntax highlighting
- Actions on hover: Copy, Regenerate, Feedback

---

## 8. Interaction Patterns

### 8.1 Global Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd/Ctrl + K` | Open Command Palette |
| `Cmd/Ctrl + \` | Toggle Sidebar |
| `Cmd/Ctrl + 1` | Go to Dashboard |
| `Cmd/Ctrl + 2` | Go to Contexts |
| `Cmd/Ctrl + 3` | Go to Templates |
| `Cmd/Ctrl + 4` | Go to Conversations |
| `Cmd/Ctrl + B` | Open Prompt Builder |
| `Cmd/Ctrl + N` | New Conversation |
| `Cmd/Ctrl + Shift + C` | Create Context |
| `Cmd/Ctrl + Shift + T` | Create Template |
| `Cmd/Ctrl + Shift + F` | Search Everywhere |
| `Cmd/Ctrl + S` | Save Current |
| `Cmd/Ctrl + Z` | Undo |
| `Cmd/Ctrl + Shift + Z` | Redo |
| `Escape` | Close Modal/Panel/Palette |
| `/` | Focus Search (when not in editor) |

### 8.2 Implementation

```typescript
// src/hooks/use-keyboard.ts

import { useEffect } from "react";

interface Shortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  action: () => void;
  description: string;
}

const SHORTCUTS: Shortcut[] = [
  { key: "k", ctrl: true, action: () => openCommandPalette(), description: "Command Palette" },
  { key: "\\", ctrl: true, action: () => toggleSidebar(), description: "Toggle Sidebar" },
  { key: "1", ctrl: true, action: () => navigate("/"), description: "Dashboard" },
  { key: "2", ctrl: true, action: () => navigate("/contexts"), description: "Contexts" },
  // ... etc
];

export function useGlobalKeyboard() {
  useEffect(() => {
    function handler(e: KeyboardEvent) {
      const isCtrl = e.metaKey || e.ctrlKey;
      const isShift = e.shiftKey;

      // Don't capture when in input/textarea (unless it's a global shortcut)
      const target = e.target as HTMLElement;
      const isEditing = target.tagName === "INPUT" || target.tagName === "TEXTAREA" ||
                        target.isContentEditable;

      for (const shortcut of SHORTCUTS) {
        if (
          e.key === shortcut.key &&
          !!isCtrl === !!shortcut.ctrl &&
          !!isShift === !!shortcut.shift
        ) {
          // Allow global shortcuts even when editing
          if (isEditing && !shortcut.ctrl) continue;
          e.preventDefault();
          shortcut.action();
          return;
        }
      }
    }

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);
}
```

### 8.3 Drag & Drop

Used in:
- **Prompt Builder**: Drag contexts to reorder
- **Favorites**: Reorder favorite items
- **Sidebar**: Reorder navigation items

Implementation: Use HTML Drag and Drop API or `@dnd-kit/core` for complex cases.

### 8.4 Autosave

- Debounced save: 2 seconds after last change
- Visual indicator: Small "Saving..." → "Saved" text near title
- Implementation: `useEffect` with debounce on content changes

```typescript
function useAutosave(value: string, saveFunction: (v: string) => Promise<void>) {
  const [status, setStatus] = useState<"idle" | "saving" | "saved">("idle");
  const debouncedValue = useDebounce(value, 2000);

  useEffect(() => {
    if (debouncedValue) {
      setStatus("saving");
      saveFunction(debouncedValue)
        .then(() => setStatus("saved"))
        .catch(() => setStatus("idle"));
    }
  }, [debouncedValue]);

  return status;
}
```

### 8.5 Virtual Scrolling

For lists with 100+ items, use `@tanstack/react-virtual`:

```typescript
import { useVirtualizer } from "@tanstack/react-virtual";

function ContextList({ contexts }: { contexts: Context[] }) {
  const parentRef = useRef<HTMLDivElement>(null);
  const rowVirtualizer = useVirtualizer({
    count: contexts.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 120, // Estimated card height
    overscan: 5,
  });

  return (
    <div ref={parentRef} style={{ height: "100%", overflow: "auto" }}>
      <div style={{ height: rowVirtualizer.getTotalSize() }}>
        {rowVirtualizer.getVirtualItems().map((virtualItem) => (
          <ContextCard
            key={contexts[virtualItem.index].id}
            context={contexts[virtualItem.index]}
            style={{
              position: "absolute",
              top: virtualItem.start,
              height: virtualItem.size,
            }}
          />
        ))}
      </div>
    </div>
  );
}
```

---

## 9. Page Templates

### 9.1 Dashboard

```
┌──────────────────────────────────────────────────────┐
│ Dashboard                                    ⚙️ ⌘K   │
├──────────────────────────────────────────────────────┤
│                                                      │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│ │ Contexts │ │ Prompts  │ │ Tokens   │ │ Cost     ││
│ │   247    │ │   89     │ │  1.2M    │ │  $12.40  ││
│ │ +12 ↑    │ │ +5 ↑     │ │ +240K ↑  │ │ +$2.10 ↑ ││
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘│
│                                                      │
│ ┌────────────────────────────────────────────────┐   │
│ │ Weekly Usage Trend (line chart)                │   │
│ │                                                │   │
│ └────────────────────────────────────────────────┘   │
│                                                      │
│ ┌──────────────────┐ ┌──────────────────────────┐   │
│ │ Recent Activity  │ │ Top Contexts             │   │
│ │ • Created X...   │ │ 1. Python Senior Dev (42)│   │
│ │ • Used Y in...   │ │ 2. Code Review (38)      │   │
│ │ • Updated Z...   │ │ 3. Architecture (25)     │   │
│ └──────────────────┘ └──────────────────────────┘   │
│                                                      │
│ ┌──────────────────┐ ┌──────────────────────────┐   │
│ │ Dead Contexts    │ │ AI Suggestions            │   │
│ │ ⚠ 5 unused >90d │ │ 💡 3 new context ideas    │   │
│ └──────────────────┘ └──────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

### 9.2 Context Library

```
┌──────────────────────────────────────────────────────┐
│ Contexts                + New        🔍 Search   ⌘K  │
├──────────────────────────────────────────────────────┤
│ All  Persona  Role  Instruction  Knowledge  ...      │ ← Tab filters
├──────────────────────────────────────────────────────┤
│                                                      │
│ ┌─── List View ─────────────────────────────────────┐│
│ │ ┌─────────────────────────────────────────┐       ││
│ │ │ Context Card 1                          │       ││
│ │ └─────────────────────────────────────────┘       ││
│ │ ┌─────────────────────────────────────────┐       ││
│ │ │ Context Card 2                          │       ││
│ │ └─────────────────────────────────────────┘       ││
│ │ ┌─────────────────────────────────────────┐       ││
│ │ │ Context Card 3                          │       ││
│ │ └─────────────────────────────────────────┘       ││
│ └───────────────────────────────────────────────────┘│
│                                                      │
│ Showing 1-20 of 247                    < 1 2 3 ... > │
└──────────────────────────────────────────────────────┘
```

### 9.3 Context Editor (Detail View)

```
┌──────────────────────────────────────────────────────┐
│ ← Contexts / Senior Python Developer     💾 ⋯ menu  │
├──────────────────────────────────────────────────────┤
│ ┌─────── Editor (left) ──────┐┌─── Preview (right) ┐│
│ │                            ││                     ││
│ │ Monaco Editor              ││ Rendered Markdown   ││
│ │ (markdown mode)            ││ (react-markdown)    ││
│ │                            ││                     ││
│ │                            ││                     ││
│ │                            ││                     ││
│ │                            ││                     ││
│ └────────────────────────────┘└─────────────────────┘│
├──────────────────────────────────────────────────────┤
│ Type: persona ▾  │ Priority: 85 ▾  │ Tags: + add    │
│ Category: AI ▾   │ Tokens: 1,240   │ Version: 3     │
├──────────────────────────────────────────────────────┤
│ Dependencies: [Python Basics] [Clean Architecture]   │
│                                                      │
│ 🤖 AI Enhance  │  🤖 AI Critique  │  📊 Health: 92 │
└──────────────────────────────────────────────────────┘
```

### 9.4 Prompt Builder

```
┌──────────────────────────────────────────────────────┐
│ Prompt Builder                          ▶ Compile    │
├──────────────────────────────────────────────────────┤
│ ┌─── Context Selector (left) ──┐┌─── Preview (right)│
│ │ Available Contexts           ││                    │
│ │ 🔍 Search contexts...       ││ # System Prompt    │
│ │                              ││                    │
│ │ ☑ Senior Python Dev (85)    ││ ## Persona         │
│ │ ☑ Clean Architecture (80)   ││ You are a senior...│
│ │ ☐ Code Review (75)          ││                    │
│ │ ☑ TypeScript Strict (70)    ││ ## Knowledge       │
│ │ ☐ API Design (65)           ││ Clean architecture │
│ │                              ││ principles...      │
│ │                              ││                    │
│ │ Selected: 3 contexts         ││ ## Constraints     │
│ │ Tokens: 4,200                ││ - Use TypeScript   │
│ ├──────────────────────────────┤│ - Follow SOLID...  │
│ │ Template: ▾ None             ││                    │
│ │ Variables:                   ││ ──────────────     │
│ │  project: Pocket             ││ Tokens: 4,200     │
│ │  lang: Python                ││ Score: 82 (Good)   │
│ └──────────────────────────────┘└────────────────────│
├──────────────────────────────────────────────────────┤
│ Validation: ✅ Passed (2 warnings)                    │
│ ⚠ Missing output format  │  ⚠ Consider adding examples│
└──────────────────────────────────────────────────────┘
```

### 9.5 Graph Explorer

```
┌──────────────────────────────────────────────────────┐
│ Context Graph                     🔍  Zoom ▾  ⚙️     │
├──────────────────────────────────────────────────────┤
│                                                      │
│        ┌──────────┐                                  │
│        │ Persona  │──requires──→ ┌──────────┐       │
│        │ Py Dev   │              │ Knowledge │       │
│        └──────────┘              │ Clean Arc │       │
│              │                   └──────────┘       │
│         extends                       │              │
│              │                   complements         │
│              ▼                        ▼              │
│        ┌──────────┐         ┌──────────────┐        │
│        │ Role     │         │ Constraint   │        │
│        │ Reviewer │         │ SOLID        │        │
│        └──────────┘         └──────────────┘        │
│                                                      │
│ ReactFlow interactive graph with:                    │
│ - Zoom, pan, drag nodes                             │
│ - Click node to view context detail (side panel)     │
│ - Edge labels showing dependency type                │
│ - Color-coded by context_type                        │
│ - Mini-map in bottom-right                          │
└──────────────────────────────────────────────────────┘
```

---

## 10. States

### 10.1 Empty States

Every list/collection must have a designed empty state:

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│                    📚                                 │
│                                                      │
│          No contexts yet                             │
│                                                      │
│    Create your first context to start building       │
│    your knowledge library.                           │
│                                                      │
│           [+ Create Context]                         │
│                                                      │
└──────────────────────────────────────────────────────┘
```

- Icon: Related Lucide icon, `var(--text-tertiary)`, 48px
- Title: `h3`, `var(--text-primary)`
- Description: `body-sm`, `var(--text-secondary)`, max-width 400px centered
- CTA: Primary button

### 10.2 Loading States

**Skeleton screens** (not spinners) for initial page loads:

```typescript
function ContextListSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="rounded-lg border p-4">
          <Skeleton className="h-4 w-20 mb-2" />     {/* Badge */}
          <Skeleton className="h-5 w-3/4 mb-2" />    {/* Title */}
          <Skeleton className="h-4 w-full mb-1" />    {/* Content line 1 */}
          <Skeleton className="h-4 w-2/3 mb-3" />    {/* Content line 2 */}
          <div className="flex gap-2">
            <Skeleton className="h-5 w-16" />          {/* Tag */}
            <Skeleton className="h-5 w-20" />          {/* Tag */}
          </div>
        </div>
      ))}
    </div>
  );
}
```

**Inline loading** for actions (buttons):
- Button shows spinner icon + "Saving..." text
- Button is disabled during loading

**Search loading:**
- Debounced (300ms)
- No spinner for < 300ms
- Subtle pulse animation on results area

### 10.3 Error States

**Page-level error:**

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│                    ⚠️                                 │
│                                                      │
│          Something went wrong                        │
│                                                      │
│    Failed to load contexts. The server may be        │
│    unavailable.                                      │
│                                                      │
│           [Retry]   [Go Home]                        │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**Inline error (form fields):**
- Red border on input
- Error message below input in `var(--error)` color
- Shake animation (subtle, 200ms)

**Toast errors:**
- Bottom-right toast notification
- Red accent bar on left
- Auto-dismiss after 5s
- Dismiss button

### 10.4 Success States

- Toast notification with green accent
- Optimistic UI update (instant visual feedback)
- "Saved" indicator near save button

---

## 11. Icons

### 11.1 Icon Library

**Lucide React** is the sole icon library. No mixing with other icon sets.

### 11.2 Icon Sizing

| Context | Size | Usage |
|---------|------|-------|
| `xs` | 14px | Inside badges, inline text |
| `sm` | 16px | Input icons, button icons |
| `md` | 20px | Navigation items, card icons |
| `lg` | 24px | Page header icons |
| `xl` | 32px | Empty state icons |
| `2xl` | 48px | Large empty state or feature icons |

### 11.3 Icon Color

- Default: `var(--text-secondary)` (muted)
- Active/hover: `var(--text-primary)`
- Accent: `var(--accent-primary)` (for active nav items)
- Semantic: Use semantic colors (`--success`, `--error`, etc.)

### 11.4 Semantic Icon Map

| Concept | Icon |
|---------|------|
| Context | `BookOpen` |
| Template | `FileText` |
| Variable | `Braces` (`{ }`) |
| Workspace | `FolderOpen` |
| Conversation | `MessageSquare` |
| Prompt Builder | `Hammer` |
| Graph | `GitBranch` or `Network` |
| Analytics | `BarChart3` |
| Settings | `Settings` |
| Journal | `BookMarked` |
| Search | `Search` |
| Favorite | `Star` (filled when active) |
| AI Feature | `Sparkles` |
| Add | `Plus` |
| Edit | `Pencil` |
| Delete | `Trash2` |
| Close | `X` |
| Menu | `MoreHorizontal` |
| Drag handle | `GripVertical` |
| Expand | `ChevronDown` |
| Collapse | `ChevronRight` |
| External link | `ExternalLink` |
| Copy | `Copy` |
| Check | `Check` |
| Warning | `AlertTriangle` |
| Error | `AlertCircle` |
| Info | `Info` |

---

## 12. Accessibility

### 12.1 Requirements

| Requirement | Implementation |
|-------------|---------------|
| **Focus management** | All interactive elements focusable. Logical tab order. |
| **Focus visible** | Custom focus ring: `2px solid var(--border-focus)` with 2px offset |
| **ARIA labels** | All icon-only buttons have `aria-label`. |
| **ARIA roles** | Proper `role` attributes on custom components. |
| **Screen reader** | Critical actions announced with `aria-live`. |
| **Color contrast** | Minimum 4.5:1 for body text, 3:1 for large text. |
| **No color-only indicators** | Always pair color with icon or text. |
| **Reduced motion** | Honor `prefers-reduced-motion`. |
| **Keyboard navigation** | All functionality available via keyboard. |

### 12.2 Focus Ring

```css
/* Global focus style */
*:focus-visible {
  outline: 2px solid var(--border-focus);
  outline-offset: 2px;
  border-radius: 4px;
}

/* Remove focus for mouse clicks */
*:focus:not(:focus-visible) {
  outline: none;
}
```

### 12.3 Skip Links

```tsx
function SkipLinks() {
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-4 focus:bg-bg-primary focus:text-text-primary"
    >
      Skip to main content
    </a>
  );
}
```

---

## 13. Responsive Design

### 13.1 Breakpoints

| Breakpoint | Width | Layout Change |
|-----------|-------|--------------|
| `sm` | ≥ 640px | Stack to single column |
| `md` | ≥ 768px | Sidebar overlay mode |
| `lg` | ≥ 1024px | Standard sidebar + content |
| `xl` | ≥ 1280px | Wide content, graph view |
| `2xl` | ≥ 1536px | Extra wide, three-column views |

### 13.2 Layout Behavior

| Screen | Sidebar | Content | Graph |
|--------|---------|---------|-------|
| `< 768px` | Overlay (hamburger trigger) | Full width | Full width |
| `768-1024px` | Collapsed (48px icons) | Full minus sidebar | Hidden (separate page) |
| `1024-1280px` | Full (240px) | Remaining | Split view |
| `> 1280px` | Full (240px) | Max 1200px centered | Split view |

### 13.3 Mobile Considerations

While Pocket is primarily a desktop app, it should be **usable** (not optimized) on tablets:

- Sidebar becomes an overlay drawer
- Split views become tabbed views
- Drag & drop replaced with move actions
- Command palette stays available
- Touch targets minimum 44px

---

## 14. Code Conventions

### 14.1 Component Structure

```typescript
// Standard component file structure
"use client"; // Only if needed (client interactivity)

import { useState } from "react";
import { motion } from "framer-motion";
import { BookOpen, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { Context } from "@/types/context";
import { cn } from "@/lib/utils";
import { slideUp } from "@/lib/motion";

interface ContextCardProps {
  context: Context;
  isSelected?: boolean;
  onSelect?: (id: string) => void;
  className?: string;
}

export function ContextCard({
  context,
  isSelected = false,
  onSelect,
  className,
}: ContextCardProps) {
  return (
    <motion.div
      {...slideUp}
      className={cn(
        "rounded-lg border border-border bg-bg-secondary p-4 cursor-pointer",
        "hover:bg-bg-hover transition-colors duration-100",
        isSelected && "border-accent bg-accent-subtle",
        className,
      )}
      onClick={() => onSelect?.(context.id)}
    >
      {/* Component content */}
    </motion.div>
  );
}
```

### 14.2 Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Components | PascalCase | `ContextCard`, `PromptBuilder` |
| Files | kebab-case | `context-card.tsx`, `prompt-builder.tsx` |
| Hooks | camelCase with `use` prefix | `useContexts`, `useKeyboard` |
| Types | PascalCase | `Context`, `PromptScore` |
| Constants | UPPER_SNAKE_CASE | `API_BASE`, `RANKING_WEIGHTS` |
| CSS variables | kebab-case with `--` prefix | `--bg-primary`, `--text-secondary` |
| CSS classes | kebab-case | `context-card`, `split-view` |
| Test files | `*.test.tsx` | `context-card.test.tsx` |

### 14.3 Component Rules

| Rule | Detail |
|------|--------|
| **No inline styles** | Use Tailwind classes or CSS variables. Exception: dynamic values from data. |
| **Use `cn()` utility** | For conditional class composition. |
| **Props interface always exported** | For reuse and testing. |
| **Default props in destructuring** | Not with `defaultProps` (deprecated). |
| **Memo sparingly** | Only when profiling shows render performance issues. |
| **No `any`** | Use proper types. `unknown` if truly unknown. |
| **No `index` as key** | Always use unique IDs for list items. |

---

*End of UI_GUIDELINES.md*
