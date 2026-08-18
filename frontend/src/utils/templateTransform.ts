import type { StructuredDocument, TemplateSection } from '../types/template'

function mapTableType(tableType: string): TemplateSection['content_type'] {
  const mapping: Record<string, TemplateSection['content_type']> = {
    single_row_list: 'table',
    process_card: 'table',
    assembly_card: 'table',
    dual_list: 'dual_table',
    flow_chart: 'flow_chart',
    fields: 'fields',
  }
  return mapping[tableType] || 'text'
}

/**
 * Convert a backend StructuredDocument (template_data) to the editor's
 * TemplateSection[] shape. Shared by WorkspacePage (rendering) and
 * AIChatPanel (snapshot capture for feedback diff). feedback-rules 节点4a.
 */
export function structuredDocToSections(doc: StructuredDocument): TemplateSection[] {
  return doc.chapters.map((ch) => {
    const allKeys = [
      ...(ch.fill_sources?.structured || []),
      ...(ch.fill_sources?.unstructured || []),
    ]
    return {
      section_id: ch.chapter_code,
      title: ch.chapter_title,
      content_type: mapTableType(ch.table_type),
      columns: allKeys,
      column_keys: allKeys,
      rows: ch.filled_data || [],
      left_data: ch.left_data,
      right_data: ch.right_data,
      flow_steps: ch.flow_steps,
      field_values: ch.field_values,
      fill_sources: ch.fill_sources,
      review_passed: true,
      source: 'template_generated',
      table_type: ch.table_type,
    }
  })
}

/**
 * Write edited TemplateSection[] back into a StructuredDocument.
 *
 * Matches chapters by section_id === chapter_code and updates only the
 * mutable data fields (filled_data / left_data / right_data / flow_steps /
 * field_values). Chapter metadata (title, table_type, fill_sources...) and
 * doc-level fields are preserved as-is. Unmatched chapters pass through
 * untouched. Immutable — returns a new doc.
 */
export function applySectionsToDoc(
  doc: StructuredDocument,
  sections: TemplateSection[],
): StructuredDocument {
  const sectionsById = new Map(sections.map((s) => [s.section_id, s]))
  return {
    ...doc,
    chapters: doc.chapters.map((ch) => {
      const section = sectionsById.get(ch.chapter_code)
      if (!section) return ch
      return {
        ...ch,
        filled_data: section.rows ?? ch.filled_data,
        ...(section.left_data !== undefined && { left_data: section.left_data }),
        ...(section.right_data !== undefined && { right_data: section.right_data }),
        ...(section.flow_steps !== undefined && { flow_steps: section.flow_steps }),
        ...(section.field_values !== undefined && { field_values: section.field_values }),
      }
    }),
  }
}
