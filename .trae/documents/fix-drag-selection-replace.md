# 修复框选后"替换原文"不生效 + 框选交互缺陷

## Summary

框选功能（PR #63 引入）存在核心数据流断链：用户在选区弹窗点"替换原文"后，表格内容纹丝不动（但 toast 却提示成功）。根因是**双数据源竞争**——替换结果只写入 per-project 的 `editorContent`，而表格渲染优先读全局 `editorTemplateData`（AI 生成模板时设置、localStorage 持久化），后者从不被更新，遮蔽了替换结果。同时伴生 3 个交互缺陷：浮动按钮恒出现在屏幕左上角、多格框选只替换第一格、单击单元格误触发选区且阻止正常聚焦编辑。

本次修复统一数据源 + 修正交互，共改 7 个文件，纯前端，不触碰架构层（§4）。

## Current State Analysis（探索结论）

### 数据流现状（断链点标注 ⛔）

```
ProcessTableEditor (useDragSelection 框选)
  └─ 点击「📎 处理选区」→ onPasteToChat(text, cellInfo)
       └─ TemplateContentEditor 纯透传
            └─ WorkspacePage 952-961 行: set 三个 state → SelectionDialog 打开
                 └─ 「替换原文」→ handleSelectionReplaceCell (104-115 行)
                      └─ handleTemplateSectionsChange (90-96 行)
                           └─ setEditorContent(projectId, JSON)   ← 只写 editorContent
                                └─ templateSections 派生 (72-88 行):
                                     1. editorTemplateData 非空 → structuredDocToSections(旧数据)  ⛔ 永远读到旧值
                                     2. editorContent JSON.parse → 仅当 editorTemplateData 为 null 才走到
```

- `editorTemplateData` 只有两处变化：AIChatPanel.tsx:708（AI 生成时赋值）、WorkspacePage.tsx:268（切项目置 null）。**全代码库不存在"编辑写回"路径** —— 这就是断链根因。
- creationStore 的 persist 无 partialize，`editorTemplateData` 刷新页面后仍存活于 localStorage，fallback 路径（editorContent）几乎不会被走到。
- 直接编辑单元格（contentEditable onBlur → handleSectionChange → 同一个 handleTemplateSectionsChange）也走这条断链 —— 即直接编辑同样不生效，本修复一并解决。

### 伴生缺陷

| # | 缺陷 | 位置 | 原因 |
|---|---|---|---|
| 1 | 浮动按钮恒在屏幕左上角 | ProcessTableEditor.tsx:381-382 | mouseup 时 `setDragRect(null)`（useDragSelection.ts:166）先于 setSelection 执行，按钮定位 `dragRect?.startY ?? 100` 恒回退 |
| 2 | 多格框选只替换第一格 | useDragSelection.ts:184 | `cellInfo = hitCells[0].cellInfo`，text 却是多格拼接 |
| 3 | 单击单元格误触发选区、无法聚焦编辑 | useDragSelection.ts:113,124 | 零面积矩形也命中（rectOverlaps 点相交返回 true）+ mousedown `preventDefault` 阻止聚焦 |

### 关键类型（types/template.ts）

- `CellInfo { sectionIndex, rowIndex, colKey }`（91-96 行）
- `ChapterData { chapter_code, chapter_title, table_type, filled_data, left_data?, right_data?, flow_steps?, field_values?, fill_sources? }`（41-54 行）
- `StructuredDocument { template_id, template_name, chapters, footer_values }`（56-61 行）
- `structuredDocToSections` 正向转换已有（templateTransform.ts:20-43），反向"写回"不存在

## Proposed Changes

### 1. `frontend/src/utils/templateTransform.ts` — 新增写回函数

新增 `applySectionsToDoc(doc: StructuredDocument, sections: TemplateSection[]): StructuredDocument`：
- 按 `section_id === chapter_code` 匹配 chapter，只更新可变数据字段：`filled_data = section.rows`、`left_data`、`right_data`、`flow_steps`、`field_values`。
- **chapters 的元数据（chapter_title/table_type/fill_sources 等）与 doc 顶层字段原样保留**（不可变更新：map 生成新数组/新对象）。
- 匹配不到的 chapter 保持原样（当前不存在新增章节路径，不做 append）。

### 2. `frontend/src/hooks/useDragSelection.ts` — 多格 cells + 交互修正

- `DragSelectionInfo`：`cellInfo: CellInfo` → `cells: CellInfo[]`（按命中顺序），`text` 仍为多格 `\n` 拼接（弹窗展示用）。
- **单击阈值**：mousedown 记录起点；mouseup 时若位移 `|dx| < 4 && |dy| < 4` 视为单击 → 不产生选区，并对 `e.target as HTMLElement` 调 `.focus()` 恢复单元格编辑能力，清空 dragRect 后 return。
- **保留最终选框**：mouseup 产生选区后**不再** `setDragRect(null)`——蓝色矩形保留作为选区高亮（正好符合 Windows 框选直觉），下次 mousedown 或 `clearSelection()` 时清除。
- mouseup 后需要强制一次重绘矩形（start/end 已是最终坐标，无需额外处理）。

### 3. `frontend/src/components/editor/ProcessTableEditor.tsx` — 签名与按钮修正

- Props：`onPasteToChat?: (text: string, cells: CellInfo[]) => void`（复数）。
- `handlePasteSelection`：传 `dragSelection.cells`；点击后调 `clearSelection()` 清掉选框与浮钮。
- 浮动按钮定位：继续用 `dragRect`（修复 2 后 mouseup 不再置 null，定位自然生效）；单格/多格提示文案：显示 `{originalLength}字 · {cells.length}格`。

### 4. `frontend/src/components/editor/TemplateContentEditor.tsx` — 纯透传签名同步

`onPasteToChat` 类型从 `(text, cellInfo: CellInfo)` 改为 `(text, cells: CellInfo[])`。

### 5. `frontend/src/components/editor/SelectionDialog.tsx` — 多格按行分布替换

- Props：`cellInfo: CellInfo | null` → `cells: CellInfo[]`；`onReplaceCell: (cells: CellInfo[], newText: string) => void`。
- `handleReplaceCell` **按行分布回写**（用户已确认方案）：
  - `editedText.split('\n')` 得到行数组；
  - 行数 === cells.length → 逐格回填；
  - 行数 < 格数 → 前 N 行填前 N 格，剩余格**保持原内容不动**；
  - 行数 > 格数 → 前 cells.length-1 格各填一行，**多余行用 `\n` 连接填入最后一格**；
  - 全部空行（trim 后）跳过该格不写。
- 弹窗信息 Tag：多格时显示 `{cells.length} 格选中`，单格保留 `colKey · 第N行`。

### 6. `frontend/src/pages/WorkspacePage.tsx` — 核心断链修复

- **`handleTemplateSectionsChange`（90-96 行）补一行**：
  ```tsx
  const handleTemplateSectionsChange = useCallback((sections: TemplateSection[]) => {
    if (!currentProjectId) return
    setEditorContent(currentProjectId, JSON.stringify(sections))
    // ⭐ 同步写回 editorTemplateData，消除双源竞争（含直接编辑单元格路径）
    const doc = useCreationStore.getState().editorTemplateData
    if (doc) setEditorTemplateData(applySectionsToDoc(doc, sections))
  }, [currentProjectId, setEditorContent, setEditorTemplateData])
  ```
  说明：用 `getState()` 取最新值避免闭包陈旧引用；`editorTemplateData` 为 null（fallback 路径）时跳过，此时 editorContent 渲染路径本来就通。
- `handleSelectionReplaceCell` → `handleSelectionReplaceCells(cells: CellInfo[], newText: string)`：遍历 cells 写 `rows[rowIndex][colKey] = 对应行`，边界校验（sectionIndex/rowIndex 越界跳过该格），一次性组装 next 后调 `handleTemplateSectionsChange`（只调一次，避免中间态）。
- 状态：`selectionDialogCellInfo: CellInfo | null` → `selectionDialogCells: CellInfo[]`；952-961 行回调传 `cells`；1094-1106 行 SelectionDialog props 同步。
- `onPasteToChat` 内联回调签名同步为 `(text, cells)`。

### 7. 不改的部分（明确排除）

- `creationStore.ts` 的 persist/partialize —— 本次不动（影响面大，另立 PR）。
- G19a FlowChartEditor / FallbackTable 分支不接框选（用户已确认只修核心链路）。
- `useTableSelection.ts`（备用 hook，未被引用）不删不改。
- AI 回调（polish/review/fill/proofread）逻辑不动 —— 它们只改弹窗内 editedText，替换入口唯一。

## Assumptions & Decisions

1. **多格替换语义 = 按行分布**（用户已确认）；行/格数不匹配采用宽容策略（多余格不动 / 多余行并入末格）。
2. **修复范围 = 核心链路**（用户已确认），不扩 FallbackTable/G19a。
3. 单击阈值 4px（px 级经验值，无需配置化）。
4. 替换后 toast 保持在 SelectionDialog 内（链路修通后 toast 不再是假成功）。
5. `applySectionsToDoc` 放 templateTransform.ts（与正向转换同文件，内聚）。
6. 本次不持久化到后端（现状也没有保存调用，保持一致，不扩大范围）。

## Verification

1. **类型检查**：`cd frontend && npx tsc --noEmit` → 0 错误。
2. **构建**：`npm run build` 通过。
3. **手动冒烟**（用户本地执行，沙箱无浏览器）：
   - AI 生成模板（使 editorTemplateData 非 null，复现断链前置条件）；
   - 拖拽 ≥4px 框选单元格 → 蓝色矩形保留 + 浮钮出现在**选区旁**（非左上角）；
   - 点「处理选区」→ 弹窗 → 手动编辑文字 → 「替换原文」→ **表格单元格立即更新**（本轮修复的核心验收点）；
   - 多格框选 → 弹窗显示"N 格选中" → 编辑为多行 → 替换 → 各格按行更新；
   - 单击（<4px）单元格 → 无选区弹窗、单元格可聚焦直接编辑；编辑后 onBlur → 表格内容保持（写回链路同样生效）；
   - 再次拖拽 → 旧选框清除、新选框生效。
4. **回归**：AI 润色/审查/补齐/校对按钮行为不变；「发送给AI对话」「复制」不变。
