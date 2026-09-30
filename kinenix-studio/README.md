# kinenix-studio

The Developer Studio, Step Inspector, and Live Debugger for **kinenix**.

---

## 1. Vision & Core Philosophy

In traditional RPA platforms, workflow authoring relies heavily on tedious visual node-dragging (drag-and-drop canvases), which often results in messy "spaghetti node" diagrams and high development overhead. 

With the emergence of modern AI and Large Language Models, developers no longer need to manually drag 50 boxes to build a workflow. Instead, **kinenix-studio** is designed around an **AI-Assisted, Developer-First Paradigm**:

- **AI-Accelerated Flow Authoring:** Plain-text prompt bar generates or updates `flow.json` workflows in seconds.
- **Linear Step Timeline:** Clean, vertical sequence of steps (like Postman or GitHub Actions) rather than complex 2D wire-connecting graphs.
- **Precision Element Inspector:** Point-and-click overlay on live browser pages to capture robust, multi-layer selectors (Role/Text, CSS, XPath).
- **Persistent Session & "Run Only This Step":** Keep browser contexts open in memory to test and tune individual step selectors in sub-second feedback loops without restarting flows from step 1.
- **Root-Cause Traceability:** Instant error diagnosis pairing failed steps with runtime variable snapshots and millisecond-accurate error screenshots.
- **Zero Heavy Electron Bloat:** Built as a modern Single-Page Application (SPA) powered by a lightweight FastAPI Python backend and a blazing-fast React/TypeScript frontend.

---

## 2. System Architecture & Tech Stack

Kinenix Studio operates as an interactive development layer running locally on the developer's PC, directly communicating with `kinenix-core`:

```text
+-------------------------------------------------------------------------+
|                        Kinenix Studio (Frontend SPA)                        |
|             React 18/19 + TypeScript + Vite + Tailwind CSS             |
|                                                                         |
|  [ AI Prompt Bar ]  [ Steps Timeline ]  [ Inspector ]  [ Live Debugger ] |
+-----------------------------------+-------------------------------------+
                                    |
                         REST APIs & WebSockets
                                    |
+-----------------------------------+-------------------------------------+
|                      Kinenix Studio Server (Backend)                        |
|                  FastAPI + WebSocket Event Hub                          |
+-----------------------------------+-------------------------------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
            v                                               v
+-----------------------+                       +-----------------------+
|       Kinenix Core        |                       |   Playwright Engine   |
| Flow Engine & Actions |                       | Persistent Context &  |
| (Interpreter, Models) |                       | Element Picker Hook   |
+-----------------------+                       +-----------------------+
```

### Technology Selection

> **Current state:** The frontend uses React 18, TypeScript, Vite, `lucide-react`, and plain CSS (`src/index.css`). Tailwind CSS, shadcn/ui, `react-resizable-panels`, Monaco, WebSockets, and the persistent Playwright context below are planned.

| Tier | Technology | Purpose & Rationale |
| :--- | :--- | :--- |
| **Backend Engine** | **FastAPI (Python 3.10+)** | Native async runtime, bi-directional WebSockets, and zero-friction integration with `kinenix-core` Pydantic models. |
| **Frontend Framework** | **React + Vite (TypeScript)** | Industry-standard developer experience, fast Hot Module Replacement (HMR), and strict type safety for flow definitions. |
| **Styling & UI Kit** | **Tailwind CSS + shadcn/ui** | Modern, accessible dark-mode UI components (Tabs, Collapsibles, Dialogs, Badges) tailored for developer tools. |
| **Panel Management** | **`react-resizable-panels`** | Smooth, collapsible multi-column layout for customizable workspace widths. |
| **Code & Expression Editor** | **`@monaco-editor/react`** | Embedded VS Code editor for syntax-highlighted JSON editing and dynamic expression preview (`${var.prop}`). |
| **Browser Controller** | **Playwright Persistent Context** | Live DOM inspection, screenshot streaming, and isolated single-step execution. |

---

## 3. UI Workspace Composition (3-Column Layout)

Kinenix Studio organizes the developer experience into three coordinated panels:

```text
+----------------------------------------------------------------------------------------------------+
| Top Bar: [Flow: rpachallenge] [Env: staging v]  [ > Run All ]  [ || Debug Step ]  [ Reset Session ]|
+------------------------------------+--------------------------------+------------------------------+
| 1. Step Timeline (Left)            | 2. Step Inspector (Center)     | 3. Live Debugger (Right)     |
|                                    |                                |                              |
| - Vertical execution order         | - Dynamic action parameter     | - Live Variable Pool         |
| - Status pills (Pending, Running,  |   form (Schema-driven)         |   (${config}, ${vars})       |
|   Success, Failed)                 | - Multi-layer Selector Picker  | - Real-time execution logs   |
| - Breakpoint toggling              |   ([Pick from Page] [Test])    | - Error screenshot viewer    |
| - Drag-to-reorder steps            | - Timeout & retry tuning       | - Local AI root-cause        |
| - Add step via AI prompt           | - [ Run Only This Step ]       |   diagnosis and quick-fix    |
+------------------------------------+--------------------------------+------------------------------+
```

### Key Workflow Capabilities
1. **Interactive Element Picker:** Clicking `[ Pick from Page ]` overlays a visual crosshair on the active Playwright browser. Clicking any element automatically generates and validates candidates:
   - Primary: `role=button[name="Submit"]`
   - Secondary CSS: `button.btn-primary#submit-form`
   - XPath: `//button[@type='submit' and text()='Submit']`
2. **Step-by-Step Interactive Debugging:** Set breakpoints on any step. Step over actions one at a time while observing variables mutate live in the right-hand panel.
3. **Isolated Action Execution:** Tweak a selector or timeout in the inspector and immediately execute only that step against the running browser session without resetting state.
4. **Environment Configuration Switcher:** Toggle between `dev`, `staging`, and `production` to dynamically load corresponding `config.json` files and test environment overrides.

---

## 4. Directory Layout

Files marked `(planned)` do not exist yet.

```text
kinenix-studio/
├── README.md
├── pyproject.toml                      # Python package (CLI entry point: kinenix-studio)
├── kinenix-studio/
│   ├── cli.py                          # CLI runner
│   ├── server.py                       # FastAPI application and REST routes
│   ├── websocket.py                    # (planned) WebSocket event dispatcher
│   ├── session.py                      # (planned) Persistent browser session manager
│   └── picker.py                       # (planned) Element inspection and selector generator
├── tests/
└── frontend/                           # React + TypeScript + Vite
    ├── package.json
    ├── vite.config.ts
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx                     # 3-column layout shell
        ├── types.ts
        ├── index.css
        └── components/
            ├── Header.tsx              # Top bar, flow selector, controls
            ├── Timeline.tsx            # Step sequence
            ├── Inspector.tsx           # Step parameter editor
            └── ContextPanel.tsx        # Variables and documentation panel
```

---

## 5. Roadmap

Milestone status for Studio is tracked in [docs/roadmap.md](../docs/roadmap.md#phase-2-studio-kinenix-studio---in-progress). The planned GitOps deployment model is described in [docs/architecture.md](../docs/architecture.md#6-gitops-deployment-planned).
