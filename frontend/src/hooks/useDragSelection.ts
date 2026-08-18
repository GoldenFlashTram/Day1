/**
 * useDragSelection — Windows-style drag-to-select rectangle.
 *
 * User presses mouse down on the table container, drags to draw a
 * rectangle, and on mouse-up all text inside the rectangle is extracted.
 * Unlike native text selection, this captures text by bounding-box overlap,
 * works across cells, and draws a visible selection rectangle.
 *
 * Interaction rules:
 *  - Drag < 4px = plain click: no selection, cell regains focus for editing.
 *  - Drag ≥ 4px = selection: rectangle stays visible (as highlight) until
 *    the next mousedown or clearSelection().
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import type { CellInfo } from '../types/template'

export interface DragSelectionInfo {
  text: string
  /** All hit cells in traversal order (multi-cell selections supported). */
  cells: CellInfo[]
  originalLength: number
  isTruncated: boolean
}

/** Movement below this many px counts as a click, not a drag. */
const CLICK_THRESHOLD_PX = 4

interface UseDragSelectionOptions {
  maxLength?: number
}

interface UseDragSelectionReturn {
  selection: DragSelectionInfo | null
  isVisible: boolean
  /** Current drag rectangle (screen coords), null when idle. Kept after mouseup as selection highlight. */
  dragRect: { startX: number; startY: number; endX: number; endY: number } | null
  clearSelection: () => void
}

interface CellTextHit {
  text: string
  cellInfo: CellInfo
  rect: DOMRect
}

/**
 * Collect all contentEditable <td> cells in the container with their
 * text content + bounding rect.
 */
function collectCells(
  container: HTMLElement,
  sectionIndex: number,
): CellTextHit[] {
  const tds = container.querySelectorAll<HTMLTableCellElement>(
    'td[contenteditable][data-col-key]',
  )
  const hits: CellTextHit[] = []
  tds.forEach((td) => {
    const tr = td.closest('tr')
    if (!tr) return
    const rowAttr = tr.getAttribute('data-row-index')
    if (rowAttr === null) return
    const colKey = td.getAttribute('data-col-key')
    if (!colKey) return
    const text = td.textContent?.trim() || ''
    if (!text) return
    hits.push({
      text,
      rect: td.getBoundingClientRect(),
      cellInfo: {
        sectionIndex,
        rowIndex: parseInt(rowAttr, 10),
        colKey,
      },
    })
  })
  return hits
}

/**
 * Check if a cell's bounding rect overlaps with the drag rectangle.
 */
function rectOverlaps(
  cell: DOMRect,
  x1: number,
  y1: number,
  x2: number,
  y2: number,
): boolean {
  const rx1 = Math.min(x1, x2)
  const rx2 = Math.max(x1, x2)
  const ry1 = Math.min(y1, y2)
  const ry2 = Math.max(y1, y2)
  return !(
    cell.right < rx1 ||
    cell.left > rx2 ||
    cell.bottom < ry1 ||
    cell.top > ry2
  )
}

export function useDragSelection(
  containerRef: React.RefObject<HTMLElement | null>,
  sectionIndex: number,
  options: UseDragSelectionOptions = {},
): UseDragSelectionReturn {
  const { maxLength = 200 } = options
  const [selection, setSelection] = useState<DragSelectionInfo | null>(null)
  const [isVisible, setIsVisible] = useState(false)
  const [dragRect, setDragRect] = useState<
    { startX: number; startY: number; endX: number; endY: number } | null
  >(null)
  const isDraggingRef = useRef(false)
  const startPosRef = useRef<{ x: number; y: number } | null>(null)

  const handleMouseDown = useCallback(
    (e: MouseEvent) => {
      const container = containerRef.current
      if (!container) return

      // Only start drag if clicking inside the table area (not on buttons/toolbars)
      const target = e.target as HTMLElement
      if (!target.closest('td[contenteditable]')) return

      // Don't interfere with normal text editing (double-click select, etc.)
      // Only activate drag-select on plain mousedown without Ctrl/Cmd
      if (e.ctrlKey || e.metaKey) return

      // Starting a new gesture clears any previous selection highlight
      setSelection(null)
      setIsVisible(false)

      isDraggingRef.current = true
      startPosRef.current = { x: e.clientX, y: e.clientY }
      setDragRect({ startX: e.clientX, startY: e.clientY, endX: e.clientX, endY: e.clientY })

      // Prevent native text selection while dragging
      e.preventDefault()
    },
    [containerRef],
  )

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDraggingRef.current || !startPosRef.current) return
      setDragRect({
        startX: startPosRef.current.x,
        startY: startPosRef.current.y,
        endX: e.clientX,
        endY: e.clientY,
      })
    },
    [],
  )

  const handleMouseUp = useCallback(
    (e: MouseEvent) => {
      if (!isDraggingRef.current) {
        return
      }
      isDraggingRef.current = false
      const start = startPosRef.current
      startPosRef.current = null

      const container = containerRef.current
      if (!container || !start) {
        setDragRect(null)
        return
      }

      const dx = e.clientX - start.x
      const dy = e.clientY - start.y

      // Plain click (< threshold): treat as normal cell click — restore
      // focus so the contentEditable cell can be edited directly.
      if (Math.abs(dx) < CLICK_THRESHOLD_PX && Math.abs(dy) < CLICK_THRESHOLD_PX) {
        setDragRect(null)
        setSelection(null)
        setIsVisible(false)
        const target = e.target as HTMLElement
        const td = target.closest?.('td[contenteditable]') as HTMLElement | null
        if (td) td.focus()
        return
      }

      // Collect all cells
      const cells = collectCells(container, sectionIndex)

      // Find cells overlapping with drag rectangle
      const hitCells = cells.filter((c) =>
        rectOverlaps(c.rect, start.x, start.y, e.clientX, e.clientY),
      )

      if (hitCells.length === 0) {
        setDragRect(null)
        setSelection(null)
        setIsVisible(false)
        return
      }

      // Single cell: full cell text. Multiple cells: join with newline.
      // All hit cells are recorded so replace can distribute lines back.
      const text = hitCells.map((c) => c.text).join('\n')

      const isTruncated = text.length > maxLength
      const truncated = isTruncated ? text.slice(0, maxLength) : text

      // Keep dragRect as the persistent selection highlight (cleared on next
      // mousedown / clearSelection). The floating action button anchors to it.
      setSelection({
        text: truncated,
        cells: hitCells.map((c) => c.cellInfo),
        originalLength: text.length,
        isTruncated,
      })
      setIsVisible(true)
    },
    [containerRef, sectionIndex, maxLength],
  )

  const clearSelection = useCallback(() => {
    setSelection(null)
    setIsVisible(false)
    setDragRect(null)
  }, [])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    container.addEventListener('mousedown', handleMouseDown)
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      container.removeEventListener('mousedown', handleMouseDown)
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [containerRef, handleMouseDown, handleMouseMove, handleMouseUp])

  return { selection, isVisible, dragRect, clearSelection }
}
