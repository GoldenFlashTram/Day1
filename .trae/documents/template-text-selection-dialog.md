# Plan: 模板表格文字框选 → 提取到对话框处理

## Summary

在模板表格编辑器（ProcessTableEditor）中新增文字框选功能：用户选中单元格内文字后弹出浮动按钮，点击后打开"选区处理弹窗"（SelectionDialog），在弹窗中可查看、修改选中的文字，并执行发送给AI、替换原文、复制等操作。严格遵循 CONTRIBUTING.md 协作规范，走 feature 分支 + PR 流程。

## Current State Analysis

### 已有机制（Markdown 模式）
- `useSelection` hook 仅支持 Tiptap 编辑器（读取 ProseMirror state）
- `MarkdownTiptapEditor` 中有浮动"📎 贴入送给AI"按钮
- `WorkspacePage` 本地 state `_selectedText` → `AIChatPanel` 的 `selectedText` prop
- `AIChatPanel` 已有 📎 引用标签（显示字数+40字预览）+ 2000字符硬上限 + 引用块拼装

### 缺失（模板模式）
- `ProcessTableEditor` 使用原生 `contentEditable` 的 `<td>`，**无任何选区捕获**
- `TemplateContentEditor` 不接受/转发 `onPasteToChat` 等选区回调
- 模板模式下 `MarkdownTiptapEditor` 被卸载，选区功能完全不可用
- 无"选区处理弹窗"组件——用户无法在发送前修改选中的文字

### 架构层判定
本次改动**不触碰架构层**（agents/**, hierarchical_context.py, knowledge_graph.py, database.py, agent.py 主链, ARCHITECTURE.md）。纯前端功能，走普通 `feature/` 分支。

## Proposed Changes

### 1. 新建 `useTableSelection` hook
**文件**: `frontend/src/hooks/useTableSelection.ts`（新建）

检测 `contentEditable` 表格单元格内的文字选中。与 `useSelection`（Tiptap 专用）并行，不修改原 hook。

**职责**:
- 监听容器元素的 `mouseup` 和 `selectionchange` 事件
- 读取 `window.getSelection()`，验证选区锚点在 `td[contenteditable]` 内
- 提取选中文本、计算浮动按钮位置（`getRangeAt(0).getBoundingClientRect()`）
- 长度限制：超过 `maxLength`（默认 500 字）时截断并提示
- 防抖 150ms，blur 延迟 200ms 隐藏（与 `useSelection` 一致）
- 返回 `{ selection: { text, cellInfo } | null, position: { top, left } | null, isVisible: boolean }`

**关键设计**:
- `cellInfo` 包含 `{ sectionIndex, rowIndex, colKey }`，用于后续"替换原文"操作定位单元格
- 通过 `data-row-index`（已有，`ProcessTableEditor.tsx:251`）和 `data-col-key`（新增）定位
- `onMouseDown preventDefault` 模式避免抢焦点（参照 `CellMergeButton` 的 `line 377`）

### 2. 新建 `SelectionDialog` 组件
**文件**: `frontend/src/components/editor/SelectionDialog.tsx`（新建）

Ant Design Modal 弹窗，展示和处理选中的文字。

**UI 结构**:
```
┌─────────────────────────────────────┐
│  选区处理                              │
├─────────────────────────────────────┤
│  原文（只读，灰底）：                    │
│  ┌─────────────────────────────────┐ │
│  │ 选中文字内容（最多500字）          │ │
│  └─────────────────────────────────┘ │
│  字数：123/500                         │
│                                       │
│  编辑后文字：                           │
│  ┌─────────────────────────────────┐ │
│  │ TextArea（可编辑，预填原文）       │ │
│  └─────────────────────────────────┘ │
│                                       │
│  [发送给AI对话] [替换原文] [复制]       │
│  [AI润色]     [AI审查]                │
│                     [关闭]            │
├─────────────────────────────────────┤
```

**Props**:
```ts
interface SelectionDialogProps {
  open: boolean
  selectedText: string          // 原始选中文本
  cellInfo: { sectionIndex: number; rowIndex: number; colKey: string } | null
  maxLength: number             // 限制长度，默认 500
  onClose: () => void
  onSendToChat: (text: string) => void      // 发送给 AIChatPanel
  onReplaceCell: (cellInfo, newText) => void // 替换单元格原文
  onPolish: (text: string) => void          // AI 润色（走 /api/tasks/review 或 quick-actions）
  onReview: (text: string) => void          // AI 审查
}
```

**功能**:
- 原文区只读展示，显示字数 `N/maxLength`，超限红色
- 编辑区 `TextArea`（Ant Design），预填原文，用户可修改
- **发送给AI对话**：调用 `onSendToChat(editedText)` → 写入 `_selectedText` → AIChatPanel 显示 📎 标签，用户继续在对话框输入指令
- **替换原文**：调用 `onReplaceCell(cellInfo, editedText)` → 定位单元格 → 更新 section rows → `onChange` 持久化
- **复制**：`navigator.clipboard.writeText(editedText)` + message.success
- **AI润色**：调用 `onPolish(editedText)` → fetch `/api/assistant/quick-actions` (action=polish) → 结果填入编辑区
- **AI审查**：调用 `onReview(editedText)` → fetch `/api/tasks/review` → 结果以 message 或折叠面板展示

### 3. 修改 `ProcessTableEditor`
**文件**: `frontend/src/components/editor/ProcessTableEditor.tsx`

**改动**:
- 新增 props: `onPasteToChat?: (text: string, cellInfo: CellInfo) => void`
- 新增 `sectionIndex` prop（用于定位 section）
- 数据单元格 `<td>` 添加 `data-col-key={col.key}` 属性（line 264 附近）
- 调用 `useTableSelection(tableRef, { maxLength: 500 })` 检测选区
- 选区可见时渲染浮动按钮"📎 处理选区"（`position: fixed`，参照 `MarkdownTiptapEditor.tsx:281-310`）
- 点击浮动按钮 → 调用 `onPasteToChat(text, cellInfo)` 打开 SelectionDialog

**注意事项**:
- 浮动按钮使用 `onMouseDown preventDefault` 避免触发 cell blur（参照 CellMergeButton line 377）
- 不干扰现有 `handleBlur` → `parseTableToRows` → `onChange` 数据流

### 4. 修改 `TemplateContentEditor`
**文件**: `frontend/src/components/editor/TemplateContentEditor.tsx`

**改动**:
- 新增 props: `onPasteToChat?: (text: string, cellInfo: CellInfo) => void`
- 将 `onPasteToChat` 和 `sectionIndex={index}` 透传给每个 `ProcessTableEditor`

### 5. 修改 `WorkspacePage`
**文件**: `frontend/src/pages/WorkspacePage.tsx`

**改动**:
- 新增 state: `selectionDialogOpen`、`selectionDialogText`、`selectionDialogCellInfo`
- `TemplateContentEditor` 传入 `onPasteToChat` 回调（line 872-875），回调打开 SelectionDialog
- 渲染 `<SelectionDialog>` 组件
- `onSendToChat`：调用 `_setSelectedText(text)` → 复用现有 AIChatPanel 📎 引用流程
- `onReplaceCell`：定位 `templateSections[cellInfo.sectionIndex]`，更新 `rows[rowIndex][colKey]`，调用 `handleTemplateSectionsChange`
- `onPolish` / `onReview`：fetch 对应 API，结果回填或展示

### 6. 类型定义
**文件**: `frontend/src/types/template.ts`

新增:
```ts
export interface CellInfo {
  sectionIndex: number
  rowIndex: number
  colKey: string
}
```

## 文件变更清单

| 文件 | 操作 | 改动量 |
|------|------|--------|
| `frontend/src/hooks/useTableSelection.ts` | 新建 | ~80 行 |
| `frontend/src/components/editor/SelectionDialog.tsx` | 新建 | ~180 行 |
| `frontend/src/components/editor/ProcessTableEditor.tsx` | 修改 | +~30 行 |
| `frontend/src/components/editor/TemplateContentEditor.tsx` | 修改 | +~5 行 |
| `frontend/src/pages/WorkspacePage.tsx` | 修改 | +~50 行 |
| `frontend/src/types/template.ts` | 修改 | +~6 行 |

**不触碰**: 后端任何文件、AIChatPanel（已有 selectedText 消费逻辑直接复用）、ARCHITECTURE.md

## Assumptions & Decisions

1. **选区长度限制 500 字**：模板单元格内容通常较短（工序描述/参数），500 字足够。比 Markdown 模式的 2000 字更保守。弹窗中显示 `N/500` 计数器。
2. **浮动按钮文案**："📎 处理选区"（与 Markdown 模式的"📎 贴入送给AI"区分，因为本功能先弹窗再操作）
3. **不修改 AIChatPanel**：现有的 `selectedText` → 📎 标签 → 引用块拼装链路直接复用，无需改动
4. **替换原文**：直接覆盖整个单元格内容（非局部替换），因为 contentEditable 的局部替换需 Range API 且易与 onBlur 冲突
5. **AI润色/审查**：复用现有 `/api/assistant/quick-actions` 和 `/api/tasks/review` 端点，不新增后端接口
6. **分支命名**: `feature/template-text-selection-dialog`
7. **Commit 规范**: `feat(editor): template cell text selection → dialog processing`

## Verification Steps

1. **TypeScript 编译**: `cd frontend && npx tsc --noEmit` — 0 错误
2. **功能测试**:
   - 模板模式下选中单元格文字 → 浮动按钮出现
   - 点击浮动按钮 → 弹窗打开，显示选中文本
   - 编辑文字 → 点"发送给AI对话" → AIChatPanel 出现 📎 标签
   - 点"替换原文" → 单元格内容更新
   - 点"复制" → 剪贴板获取文字
   - 选中超 500 字 → 截断 + 红色提示
   - generate/fill 模式下选区不拼入（现有守卫 line 458 自动生效）
3. **不回归**:
   - Markdown 模式选区功能不受影响
   - 表格编辑（增删行/合并/拆分）不受影响
   - onBlur → parseTableToRows 数据流不破坏
4. **现有测试**: `npm test` 通过

## Git 协作流程（遵循 CONTRIBUTING.md）

```bash
# 1. 从最新 main 切分支
git checkout main && git pull
git checkout -b feature/template-text-selection-dialog

# 2. 开发 + 提交
git add <files>
git commit -m "feat(editor): template cell text selection → dialog processing"

# 3. 推送
git push -u origin feature/template-text-selection-dialog

# 4. 开 PR (base=main)，填模板：
#    - 改动概述: 模板表格文字框选→弹窗处理（查看/编辑/发送AI/替换/复制/润色/审查）
#    - 是否触碰架构层: 否
#    - 自测结果: tsc 0错 + 功能测试通过 + 无回归

# 5. 等 review → 改 → merge
```
