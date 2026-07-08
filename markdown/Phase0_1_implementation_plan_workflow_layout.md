# Implementation Plan: Workflow Layout Optimization and Expanded Registry Modal Windows

Improve the user experience by resolving workflow diagram congestion (vertically centering nodes, utilizing layout helper auto-scaling, and expanding canvas dimension) and increasing window widths for all registry form modals.

---

## Proposed Changes

### 1. General Modals Layout Expansion

Increase modal widths globally to allow spacious, premium grid forms for all registry objects.

#### [MODIFY] [Modal.module.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/common/Modal.module.css)
- Increase max widths for modal size classes to give layout breathing room:
  - `sm`: Max width `350px` -> `450px`
  - `md`: Max width `500px` -> `680px`
  - `lg`: Max width `700px` -> `980px`
  - `xl`: Max width `1100px` -> `1500px` (affects all registry form modals).

---

### 2. Execution Dashboard Visuals & Helper

Wrap the monitoring React Flow canvas in a `ReactFlowProvider` and introduce a `FlowFitViewHelper` to guarantee that nodes are centered and zoomed correctly once the modal animation finishes.

#### [MODIFY] [ExecutionDashboardPage.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/ExecutionDashboardPage.tsx)
- Import `ReactFlowProvider` and `useReactFlow` from `@xyflow/react`.
- Create a `FlowFitViewHelper` sub-component to run `fitView` after a short timeout once nodes load.
- Adjust vertical placement of start, intermediate, and end process nodes from `y: 120` to `y: 220` to fit a taller canvas.
- Wrap React Flow in a `<ReactFlowProvider>`.

#### [MODIFY] [ExecutionDashboardPage.module.css](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/pages/ExecutionDashboardPage.module.css)
- Update `.modalContainer`:
  - Increase `height` from `600px` to `750px` to give vertical breathing room.
  - Adjust grid column ratio to `3.5fr 1.5fr` (or `3.4fr 1.6fr`) so the flow diagram gets a wider canvas.

---

### 3. Workflow Builder Canvas Improvements

Update the workflow builder canvas to occupy more space inside the expanded registry form modal.

#### [MODIFY] [WorkflowNodeCanvas.tsx](file:///c:/Users/aayus/Desktop/GuardianIQ--1/frontend/src/components/registry/WorkflowNodeCanvas.tsx)
- Import `ReactFlowProvider` and `useReactFlow` from `@xyflow/react`.
- Add the `FlowFitViewHelper` component inside the interactive canvas.
- Increase the container height from `520px` to `650px` for better visual layout.
- Vertically center canvas initial nodes from `y: 150` to `y: 250`.
- Wrap the canvas `<ReactFlow>` in a `<ReactFlowProvider>`.

---

## Verification Plan

### Automated Tests
- Run React/TypeScript compiler check:
  ```powershell
  npm run typecheck
  ```
- Run build verification:
  ```powershell
  npm run build
  ```

### Manual Verification
1. **Execution Dashboard:** Click "View Details" on an execution. Verify that the modal window is spacious, the React Flow canvas is vertically centered, and nodes are completely legible and not cut off or aligned to the bottom.
2. **Registry Forms:** Open registry edit modal windows (Agents, Tools, Workflows, etc.). Verify the window sizes are expanded to 1500px max width.
3. **Workflow Creator:** Open the workflow builder tab inside the Workflow Registry registration wizard. Confirm the builder canvas is tall (650px height) and auto-centers the steps.
