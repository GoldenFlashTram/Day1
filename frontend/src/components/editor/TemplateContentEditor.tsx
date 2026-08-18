/**
 * TemplateContentEditor — Main template-driven editor component
 *
 * Renders structured template data as editable tables.
 * Uses ProcessTableEditor for proper process document table layout.
 */
import { useCallback } from 'react'
import { Empty, Typography } from 'antd'
import type { TemplateSection, CellInfo } from '../../types/template'
import ProcessTableEditor from './ProcessTableEditor'

const { Title } = Typography

interface Props {
  sections: TemplateSection[]
  onChange: (sections: TemplateSection[]) => void
  onPasteToChat?: (text: string, cells: CellInfo[]) => void
}

const TemplateContentEditor: React.FC<Props> = ({ sections, onChange, onPasteToChat }) => {
  const handleSectionChange = useCallback(
    (index: number, updated: TemplateSection) => {
      const next = [...sections]
      next[index] = updated
      onChange(next)
    },
    [sections, onChange],
  )

  if (!sections || sections.length === 0) {
    return <Empty description="暂无模板数据" />
  }

  return (
    <div style={{ padding: '8px 0' }}>
      {sections.map((section, idx) => (
        <div
          key={section.section_id}
          style={{ marginBottom: 32 }}
        >
          <Title level={4} style={{ marginBottom: 12 }}>
            {section.title}
          </Title>

          <ProcessTableEditor
            section={section}
            sectionIndex={idx}
            onChange={(s) => handleSectionChange(idx, s)}
            onPasteToChat={onPasteToChat}
          />
        </div>
      ))}
    </div>
  )
}

export default TemplateContentEditor
