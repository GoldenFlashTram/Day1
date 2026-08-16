# -*- coding: utf-8 -*-
"""
生成《AI编程上手与GitHub协作开发指南》Word文档
排版精美，适配A4打印
"""
from docx import Document
from docx.shared import Pt, Cm, Mm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import copy

# ============================================================
# 颜色定义（专业蓝主题）
# ============================================================
COLOR_PRIMARY = RGBColor(0x1A, 0x56, 0xDB)      # 主蓝
COLOR_DARK = RGBColor(0x1E, 0x29, 0x3B)          # 深色文字
COLOR_SECONDARY = RGBColor(0x4A, 0x55, 0x68)     # 次要文字
COLOR_ACCENT = RGBColor(0xE8, 0x6F, 0x1A)        # 橙色强调
COLOR_GREEN = RGBColor(0x2D, 0xA4, 0x4E)         # 绿色（正确/成功）
COLOR_RED = RGBColor(0xDC, 0x35, 0x45)           # 红色（错误/禁止）
COLOR_CODE_BG = "F5F7FA"                          # 代码块背景
COLOR_TIP_BG = "E8F4FD"                           # 提示框背景
COLOR_WARN_BG = "FFF3E0"                          # 警告框背景
COLOR_TABLE_HEADER = "1A56DB"                     # 表头背景

# ============================================================
# 创建文档与页面设置
# ============================================================
doc = Document()

# A4 页面设置
section = doc.sections[0]
section.page_width = Mm(210)
section.page_height = Mm(297)
section.top_margin = Cm(2.5)
section.bottom_margin = Cm(2.5)
section.left_margin = Cm(2.5)
section.right_margin = Cm(2.5)
section.header_distance = Cm(1.5)
section.footer_distance = Cm(1.5)

# ============================================================
# 默认样式
# ============================================================
style = doc.styles['Normal']
font = style.font
font.name = '微软雅黑'
font.size = Pt(11)
font.color.rgb = COLOR_DARK
style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
style.paragraph_format.line_spacing = 1.5
style.paragraph_format.space_after = Pt(4)

# ============================================================
# 辅助函数
# ============================================================

def set_cell_shading(cell, color_hex):
    """设置单元格背景色"""
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)

def set_run_font(run, name='微软雅黑', size=11, color=None, bold=False, italic=False):
    """设置文字格式"""
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = color
    run.element.rPr.rFonts.set(qn('w:eastAsia'), name)

def add_page_break():
    """添加分页符"""
    doc.add_page_break()

def add_heading_custom(text, level=1, color=None):
    """添加自定义标题"""
    if color is None:
        color = COLOR_PRIMARY
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18 if level == 1 else 14)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.keep_with_next = True

    if level == 1:
        # 一级标题：带底部边框线
        run = p.add_run(text)
        set_run_font(run, '微软雅黑', 18, color, bold=True)
        p.paragraph_format.border_bottom = True
        pPr = p._p.get_or_add_pPr()
        pBdr = parse_xml(
            f'<w:pBdr {nsdecls("w")}>'
            f'<w:bottom w:val="single" w:sz="12" w:space="4" w:color="1A56DB"/>'
            f'</w:pBdr>'
        )
        pPr.append(pBdr)
    elif level == 2:
        run = p.add_run(text)
        set_run_font(run, '微软雅黑', 15, color, bold=True)
    elif level == 3:
        run = p.add_run(text)
        set_run_font(run, '微软雅黑', 13, color, bold=True)
    else:
        run = p.add_run(text)
        set_run_font(run, '微软雅黑', 12, color, bold=True)
    return p

def add_body(text, size=11, color=None, bold=False, indent=False, space_after=6):
    """添加正文段落"""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.5
    if indent:
        p.paragraph_format.first_line_indent = Cm(0.75)
    run = p.add_run(text)
    set_run_font(run, '微软雅黑', size, color or COLOR_DARK, bold)
    return p

def add_bullet(text, level=0, size=11, color=None):
    """添加项目符号"""
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.left_indent = Cm(1.0 + level * 0.75)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.4
    run = p.add_run(text)
    set_run_font(run, '微软雅黑', size, color or COLOR_DARK)
    return p

def add_number(text, level=0, size=11, color=None):
    """添加编号列表"""
    p = doc.add_paragraph(style='List Number')
    p.paragraph_format.left_indent = Cm(1.0 + level * 0.75)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.4
    run = p.add_run(text)
    set_run_font(run, '微软雅黑', size, color or COLOR_DARK)
    return p

def add_code_block(code_text, language="bash"):
    """添加代码块（灰底等宽字体）"""
    # 创建单行单列表格作为代码块容器
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    set_cell_shading(cell, COLOR_CODE_BG)

    # 设置单元格边距
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="120" w:type="dxa"/>'
        f'<w:left w:w="160" w:type="dxa"/>'
        f'<w:bottom w:w="120" w:type="dxa"/>'
        f'<w:right w:w="160" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

    # 清除默认段落
    cell.paragraphs[0].text = ''
    lines = code_text.strip().split('\n')
    for i, line in enumerate(lines):
        if i == 0:
            p = cell.paragraphs[0]
        else:
            p = cell.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.line_spacing = 1.3
        run = p.add_run(line)
        set_run_font(run, 'Consolas', 9.5, RGBColor(0x33, 0x33, 0x33))

    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table

def add_tip_box(title, content, box_type="tip"):
    """添加提示框（蓝底提示/橙底警告/绿底正确/红底禁止）"""
    color_map = {
        "tip": ("E8F4FD", "1A56DB", "💡 提示"),
        "warn": ("FFF3E0", "E86F1A", "⚠ 注意"),
        "ok": ("E8F8ED", "2DA44E", "✅ 正确做法"),
        "no": ("FDE8E8", "DC3545", "❌ 错误做法"),
    }
    bg_color, text_color, default_title = color_map.get(box_type, color_map["tip"])
    title_text = title if title else default_title

    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    set_cell_shading(cell, bg_color)

    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="120" w:type="dxa"/>'
        f'<w:left w:w="160" w:type="dxa"/>'
        f'<w:bottom w:w="120" w:type="dxa"/>'
        f'<w:right w:w="160" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

    cell.paragraphs[0].text = ''
    p_title = cell.paragraphs[0]
    p_title.paragraph_format.space_after = Pt(4)
    run_title = p_title.add_run(title_text)
    set_run_font(run_title, '微软雅黑', 10.5, RGBColor(int(text_color[0:2],16), int(text_color[2:4],16), int(text_color[4:6],16)), bold=True)

    if isinstance(content, str):
        content = [content]
    for line in content:
        p = cell.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.4
        run = p.add_run(line)
        set_run_font(run, '微软雅黑', 10, COLOR_DARK)

    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table

def add_table_styled(headers, rows, col_widths=None):
    """添加美观表格"""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'

    # 表头
    for i, header in enumerate(headers):
        cell = table.cell(0, i)
        set_cell_shading(cell, COLOR_TABLE_HEADER)
        cell.paragraphs[0].text = ''
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.space_before = Pt(2)
        run = p.add_run(header)
        set_run_font(run, '微软雅黑', 10, RGBColor(0xFF, 0xFF, 0xFF), bold=True)

    # 数据行
    for r_idx, row in enumerate(rows):
        for c_idx, cell_data in enumerate(row):
            cell = table.cell(r_idx + 1, c_idx)
            if r_idx % 2 == 1:
                set_cell_shading(cell, "F5F7FA")
            cell.paragraphs[0].text = ''
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.line_spacing = 1.3
            run = p.add_run(str(cell_data))
            set_run_font(run, '微软雅黑', 9.5, COLOR_DARK)

    # 列宽
    if col_widths:
        for i, width in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Cm(width)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return table

def add_toc_entry(text, page_num, level=1):
    """添加目录条目"""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    if level == 1:
        p.paragraph_format.left_indent = Cm(0)
        run = p.add_run(text)
        set_run_font(run, '微软雅黑', 12, COLOR_PRIMARY, bold=True)
    elif level == 2:
        p.paragraph_format.left_indent = Cm(1.0)
        run = p.add_run(text)
        set_run_font(run, '微软雅黑', 10.5, COLOR_DARK)
    else:
        p.paragraph_format.left_indent = Cm(2.0)
        run = p.add_run(text)
        set_run_font(run, '微软雅黑', 10, COLOR_SECONDARY)

    # 添加点线
    dots = p.add_run(' ' + '·' * 50)
    set_run_font(dots, '微软雅黑', 10, RGBColor(0xCC, 0xCC, 0xCC))
    dots.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)

    # 页码
    p.add_run('\t')
    run_page = p.add_run(str(page_num))
    set_run_font(run_page, '微软雅黑', 10, COLOR_SECONDARY)

# ============================================================
# 页眉页脚
# ============================================================
def setup_header_footer():
    """设置页眉页脚"""
    # 页眉
    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0]
    hp.text = ''
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = hp.add_run('AI编程上手与GitHub协作开发指南')
    set_run_font(run, '微软雅黑', 8, RGBColor(0x99, 0x99, 0x99))
    # 页眉下边框
    pPr = hp._p.get_or_add_pPr()
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        f'<w:bottom w:val="single" w:sz="4" w:space="1" w:color="CCCCCC"/>'
        f'</w:pBdr>'
    )
    pPr.append(pBdr)

    # 页脚（页码）
    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0]
    fp.text = ''
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # 添加页码字段
    run = fp.add_run()
    fldChar1 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="begin"/>')
    run._r.append(fldChar1)
    run2 = fp.add_run()
    instrText = parse_xml(f'<w:instrText {nsdecls("w")} xml:space="preserve"> PAGE </w:instrText>')
    run2._r.append(instrText)
    run3 = fp.add_run()
    fldChar2 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="end"/>')
    run3._r.append(fldChar2)
    set_run_font(run, '微软雅黑', 9, RGBColor(0x99, 0x99, 0x99))
    set_run_font(run2, '微软雅黑', 9, RGBColor(0x99, 0x99, 0x99))
    set_run_font(run3, '微软雅黑', 9, RGBColor(0x99, 0x99, 0x99))

setup_header_footer()

# ============================================================
# 封面
# ============================================================
# 顶部空间
for _ in range(6):
    doc.add_paragraph()

# 主标题
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(12)
run = p.add_run('AI 编程上手与')
set_run_font(run, '微软雅黑', 36, COLOR_PRIMARY, bold=True)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(30)
run = p.add_run('GitHub 协作开发指南')
set_run_font(run, '微软雅黑', 36, COLOR_PRIMARY, bold=True)

# 副标题
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(8)
run = p.add_run('—— 从零开始，用 AI 写代码、用 Git 做协作 ——')
set_run_font(run, '微软雅黑', 14, COLOR_SECONDARY)

# 分隔线
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
pPr = p._p.get_or_add_pPr()
pBdr = parse_xml(
    f'<w:pBdr {nsdecls("w")}>'
    f'<w:bottom w:val="single" w:sz="12" w:space="1" w:color="1A56DB"/>'
    f'</w:pBdr>'
)
pPr.append(pBdr)

# 空行
for _ in range(3):
    doc.add_paragraph()

# 项目信息
info_items = [
    ('适用项目', '工艺文件辅助编辑系统 (localknowledgebase-word)'),
    ('技术栈', 'React 18 + TypeScript + Python 3.13 + FastAPI'),
    ('AI 工具', 'Trae / Cursor / Claude Code / GitHub Copilot'),
    ('面向读者', '零基础新协作者 / AI 编程初学者'),
    ('文档版本', 'v1.0'),
]
for label, value in info_items:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(6)
    run1 = p.add_run(f'{label}：')
    set_run_font(run1, '微软雅黑', 11, COLOR_SECONDARY)
    run2 = p.add_run(value)
    set_run_font(run2, '微软雅黑', 11, COLOR_DARK)

# 底部空间
for _ in range(4):
    doc.add_paragraph()

# 底部说明
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('本文档基于项目实际代码与协作规范编写，配合《Code Wiki》使用')
set_run_font(run, '微软雅黑', 9, RGBColor(0xAA, 0xAA, 0xAA))

add_page_break()

# ============================================================
# 目录
# ============================================================
add_heading_custom('目  录', level=1)

toc_items = [
    ("第一章  AI 编程入门概述", 3, 1),
    ("1.1 什么是 AI 编程", 3, 2),
    ("1.2 主流 AI 编程工具", 3, 2),
    ("1.3 AI 编程能做什么", 4, 2),
    ("1.4 AI 编程的边界", 4, 2),
    ("第二章  开发环境搭建", 5, 1),
    ("2.1 Git 安装与配置", 5, 2),
    ("2.2 Python 环境", 6, 2),
    ("2.3 Node.js 环境", 6, 2),
    ("2.4 IDE 与 AI 编程工具", 7, 2),
    ("第三章  理解项目架构", 8, 1),
    ("3.1 项目概览", 8, 2),
    ("3.2 技术栈速览", 8, 2),
    ("3.3 目录结构", 9, 2),
    ("3.4 核心概念图解", 10, 2),
    ("第四章  AI 编程实战指南", 11, 1),
    ("4.1 如何向 AI 描述需求（Prompt 工程）", 11, 2),
    ("4.2 用 AI 生成代码", 13, 2),
    ("4.3 用 AI 修改与调试代码", 14, 2),
    ("4.4 AI 编程最佳实践", 15, 2),
    ("第五章  GitHub 协作开发流程", 16, 1),
    ("5.1 Git 基础操作", 16, 2),
    ("5.2 分支模型", 17, 2),
    ("5.3 PR（Pull Request）流程", 18, 2),
    ("5.4 Code Review", 19, 2),
    ("5.5 冲突解决", 20, 2),
    ("第六章  实战演练：从零完成一个功能", 21, 1),
    ("6.1 任务：添加一个新 API 端点", 21, 2),
    ("6.2 Step 1 — 创建分支", 21, 2),
    ("6.3 Step 2 — 用 AI 生成代码", 22, 2),
    ("6.4 Step 3 — 本地测试", 23, 2),
    ("6.5 Step 4 — 提交与推送", 23, 2),
    ("6.6 Step 5 — 开 PR 与处理 Review", 24, 2),
    ("第七章  常见问题与避坑指南", 25, 1),
    ("第八章  进阶技巧与资源", 27, 1),
]

for text, page, level in toc_items:
    add_toc_entry(text, page, level)

add_page_break()

# ============================================================
# 第一章
# ============================================================
add_heading_custom('第一章  AI 编程入门概述', level=1)

add_heading_custom('1.1 什么是 AI 编程', level=2)
add_body('AI 编程是指利用大语言模型（LLM）辅助软件开发的全过程，包括编写代码、调试、重构、写测试、写文档等。你不需要从零手写每一行代码，而是用自然语言描述需求，AI 帮你生成代码，你再审查、修改、确认。', indent=True)
add_body('简单来说：以前是你写代码给计算机执行；现在是你写需求给 AI，AI 写代码给你审查。你的角色从"打字员"变成了"审稿人"和"架构师"。', indent=True)

add_tip_box('', [
    '一个类比：AI 编程就像带了一个不知疲倦但偶尔犯迷糊的初级程序员。',
    '你负责：提需求、定方向、审代码、把关质量。',
    'AI 负责：写初稿、查资料、跑测试、填模板。',
], "tip")

add_heading_custom('1.2 主流 AI 编程工具', level=2)
add_body('以下是目前主流的 AI 编程工具，按使用场景分类：')

add_table_styled(
    ['工具', '类型', '适用场景', '特点'],
    [
        ['Trae', 'IDE（内置AI）', '全流程开发', '免费，AI深度集成编辑器，支持MCP扩展'],
        ['Cursor', 'IDE（内置AI）', '全流程开发', '主流AI IDE，体验流畅，付费'],
        ['GitHub Copilot', '编辑器插件', '代码补全', '行内补全强，适合已有代码基础'],
        ['Claude Code', '命令行AI', '代码理解/重构', '长上下文，适合大型项目分析'],
        ['ChatGPT / 文心一言', '对话式AI', '学习/方案设计', '通用对话，不适合直接改代码'],
    ],
    col_widths=[3.5, 3, 4, 5]
)

add_tip_box('本项目推荐', [
    '推荐使用 Trae（免费 + AI 深度集成）或 Cursor 作为主力 IDE。',
    '配合 Claude Code 做项目级代码理解和重构。',
], "tip")

add_heading_custom('1.3 AI 编程能做什么', level=2)
add_body('在实际开发中，AI 编程能帮你完成以下工作：')

add_bullet('生成代码：描述需求，AI 生成完整函数/组件/接口')
add_bullet('修改代码：指出问题，AI 给出修改方案并直接改')
add_bullet('调试排错：粘贴报错信息，AI 分析原因并给修复建议')
add_bullet('代码解释：选中代码，AI 用自然语言解释逻辑')
add_bullet('写测试：给 AI 一个函数，它生成单元测试')
add_bullet('写文档：AI 根据代码生成注释、README、API 文档')
add_bullet('重构优化：AI 识别坏味道代码，给出重构建议')
add_bullet('翻译转换：代码语言转换（如 Python→TypeScript）')

add_heading_custom('1.4 AI 编程的边界', level=2)
add_body('AI 不是万能的，了解它的边界才能用好它：')

add_table_styled(
    ['AI 擅长的', 'AI 不擅长的'],
    [
        ['生成模板化代码（CRUD、表单、API）', '理解项目特有的业务上下文'],
        ['常见算法与数据结构', '复杂的跨模块交互逻辑'],
        ['标准库/API 用法查询', '最新（训练数据之后）的框架变更'],
        ['代码格式化与简单重构', '性能敏感的底层优化'],
        ['生成测试用例', '判断代码是否符合业务规则'],
    ],
    col_widths=[7.5, 7.5]
)

add_tip_box('核心原则', [
    'AI 生成的一切代码，都必须由你审查理解后才能使用。',
    '你不懂的代码，不要提交。先问 AI 解释，搞懂了再用。',
    'AI 是助手不是替代品——最终责任在你。',
], "warn")

add_page_break()

# ============================================================
# 第二章
# ============================================================
add_heading_custom('第二章  开发环境搭建', level=1)
add_body('本章带你从零搭建开发环境。按顺序操作即可，每步都有验证方法。')

add_heading_custom('2.1 Git 安装与配置', level=2)
add_body('Git 是版本控制工具，是协作开发的基础。所有代码变更都通过 Git 管理。')

add_body('安装 Git：', bold=True, space_after=4)
add_bullet('Windows：访问 https://git-scm.com/download/win 下载安装包，一路 Next 即可')
add_bullet('macOS：终端执行 brew install git')
add_bullet('Linux：sudo apt install git（Ubuntu/Debian）')

add_body('配置用户信息（必须）：', bold=True, space_after=4)
add_code_block(
    'git config --global user.name "你的名字"\n'
    'git config --global user.email "你的邮箱@example.com"\n'
    '\n'
    '# 验证配置\n'
    'git config --list'
)

add_body('配置 SSH 密钥（用于 GitHub 免密操作）：', bold=True, space_after=4)
add_code_block(
    '# 生成密钥（一路回车即可）\n'
    'ssh-keygen -t ed25519 -C "你的邮箱@example.com"\n'
    '\n'
    '# 查看公钥（复制输出内容）\n'
    'cat ~/.ssh/id_ed25519.pub'
)

add_tip_box('添加到 GitHub', [
    '1. 登录 GitHub → Settings → SSH and GPG keys → New SSH key',
    '2. Title 随便填（如"我的电脑"）',
    '3. 粘贴上面 cat 输出的公钥内容',
    '4. 测试连接：ssh -T git@github.com',
], "tip")

add_heading_custom('2.2 Python 环境', level=2)
add_body('后端使用 Python 3.13。推荐使用 conda 管理环境。')

add_code_block(
    '# 安装 Miniconda（推荐）\n'
    '# Windows: 从 https://docs.conda.io/en/latest/miniconda.html 下载\n'
    '\n'
    '# 创建虚拟环境\n'
    'conda create -n craftdoc python=3.13\n'
    'conda activate craftdoc\n'
    '\n'
    '# 安装后端依赖\n'
    'cd backend\n'
    'pip install -r requirements.txt\n'
    '\n'
    '# 验证\n'
    'python --version  # 应显示 3.13.x'
)

add_heading_custom('2.3 Node.js 环境', level=2)
add_body('前端使用 Node.js 18+。推荐使用 nvm 管理版本。')

add_code_block(
    '# Windows: 从 https://nodejs.org 下载 LTS 版本安装\n'
    '# 或使用 nvm-windows\n'
    '\n'
    '# 安装前端依赖\n'
    'cd frontend\n'
    'npm install\n'
    '\n'
    '# 验证\n'
    'node --version  # 应显示 v18+\n'
    'npm --version'
)

add_tip_box('', '如果 npm install 很慢，可以切换淘宝镜像：npm config set registry https://registry.npmmirror.com', "tip")

add_heading_custom('2.4 IDE 与 AI 编程工具', level=2)
add_body('推荐使用 Trae（免费 AI IDE）作为主力开发工具：')

add_number('访问 https://www.trae.ai 下载 Trae 并安装')
add_number('打开 Trae，用 GitHub 账号登录')
add_number('File → Open Folder → 选择项目根目录')
add_number('Trae 内置 AI 对话面板（右侧），可直接用自然语言编程')

add_body('AI 编程工具对比：', bold=True, space_after=4)
add_table_styled(
    ['维度', 'Trae', 'Cursor', 'Copilot'],
    [
        ['价格', '免费', '$20/月', '$10/月'],
        ['AI 对话', '内置', '内置', '需配合 ChatGPT'],
        ['代码补全', '支持', '支持', '最强'],
        ['项目理解', '强', '强', '弱'],
        ['MCP 扩展', '支持', '不支持', '不支持'],
        ['推荐场景', '全流程开发', '全流程开发', '辅助补全'],
    ],
    col_widths=[3, 3.5, 3.5, 4]
)

add_tip_box('环境验证清单', [
    'git --version  →  git version 2.x',
    'python --version  →  Python 3.13.x',
    'node --version  →  v18+',
    'ssh -T git@github.com  →  Hi xxx! You\'ve successfully authenticated.',
    'Trae/Cursor 已安装并能打开项目',
], "ok")

add_page_break()

# ============================================================
# 第三章
# ============================================================
add_heading_custom('第三章  理解项目架构', level=1)
add_body('在用 AI 写代码之前，先理解项目整体结构。这样你才能给 AI 准确的上下文，让它生成符合项目规范的代码。')

add_heading_custom('3.1 项目概览', level=2)
add_body('本项目是一个"工艺文件辅助编辑系统"，核心理念是：工艺意图 → 标准工艺术语 → 工艺文件生成。', indent=True)
add_body('系统通过多层 AI Agent，从工艺素材出发，自动生成符合 QJ903 标准的结构化工艺文件。前端提供表格编辑器，后端以 FastAPI + 多层 Agent + 层次化上下文检索为核心。', indent=True)

add_heading_custom('3.2 技术栈速览', level=2)
add_table_styled(
    ['层', '技术', '你需了解的程度'],
    [
        ['前端', 'React 18 + TypeScript + Vite + Ant Design 5 + Tiptap', '改前端组件时需了解'],
        ['后端', 'Python 3.13 + FastAPI + SQLAlchemy 2.0 + SQLite', '改后端接口时需了解'],
        ['AI/LLM', 'LangChain + Qwen（通义千问）', '改 Agent 逻辑时需了解'],
        ['PDF解析', 'MinerU 3.4（VLM 高精度）', '一般不需改'],
        ['检索', 'HierarchicalContext（关键词+章节结构）', '架构层，谨慎改'],
        ['版本控制', 'Git + GitHub（PR 工作流）', '必须掌握'],
    ],
    col_widths=[2.5, 7.5, 5]
)

add_heading_custom('3.3 目录结构', level=2)
add_body('项目核心目录结构（仅列关键部分）：')
add_code_block(
    'llbased-word/\n'
    '├── backend/                    # Python 后端\n'
    '│   ├── app/\n'
    '│   │   ├── agents/             # Agent 系统（架构层，改前看规范）\n'
    '│   │   │   ├── core/           # 注册表 & 协议\n'
    '│   │   │   ├── functional/     # 功能 Agent（writing/review/proofread）\n'
    '│   │   │   └── orchestrator/   # 编排器 + 状态机\n'
    '│   │   ├── api/                # FastAPI 路由（18个文件）\n'
    '│   │   ├── models/             # 数据模型（ORM + Pydantic）\n'
    '│   │   ├── services/           # 业务服务层（40+文件）\n'
    '│   │   ├── tools/              # PDF解析 & 合规/术语工具\n'
    '│   │   └── config.py           # 全局配置\n'
    '│   ├── main.py                 # 后端入口\n'
    '│   └── requirements.txt\n'
    '├── frontend/                   # React 前端\n'
    '│   ├── src/\n'
    '│   │   ├── components/         # UI 组件\n'
    '│   │   ├── stores/             # Zustand 状态管理\n'
    '│   │   ├── services/           # API 客户端\n'
    '│   │   └── pages/              # 页面\n'
    '│   └── package.json\n'
    '├── ARCHITECTURE.md             # 唯一架构源（必读）\n'
    '├── CONTRIBUTING.md             # 协作规范（必读）\n'
    '└── CODE-WIKI.md                # 代码 Wiki（详细参考）'
)

add_heading_custom('3.4 核心概念图解', level=2)
add_body('理解以下核心概念，才能在项目中高效工作：')

add_table_styled(
    ['概念', '说明', '在哪里'],
    [
        ['Agent', 'AI 代理，负责执行特定任务（写/审/校）', 'backend/app/agents/'],
        ['Orchestrator', '编排器，协调多个 Agent 工作', 'agents/orchestrator/'],
        ['SSE', 'Server-Sent Events，前端接收AI流式输出', 'api/agent.py → AIChatPanel'],
        ['HierarchicalContext', '层次化上下文检索（5层）', 'services/hierarchical_context.py'],
        ['Source-driven 直注', '从源文档直接抽取内容填充（主路径）', 'orchestrator + writing_agent'],
        ['Profile', '领域画像（装配/焊接/涂装）', 'data/profiles/*.json'],
        ['架构层', '改动需独立PR+强制review的文件', '见 CONTRIBUTING.md §4'],
    ],
    col_widths=[3.5, 6, 5.5]
)

add_tip_box('给新人的建议', [
    '1. 先跑通项目（后端:8000 + 前端:3000），感受功能',
    '2. 读 ARCHITECTURE.md 了解整体架构',
    '3. 读 CODE-WIKI.md 了解模块细节',
    '4. 从小改动开始（改个文案、修个小bug），熟悉流程后再做大功能',
], "tip")

add_page_break()

# ============================================================
# 第四章
# ============================================================
add_heading_custom('第四章  AI 编程实战指南', level=1)
add_body('本章教你如何高效地用 AI 编程。核心技能是"会提问"——好的 Prompt 产出好代码。')

add_heading_custom('4.1 如何向 AI 描述需求（Prompt 工程）', level=2)
add_body('Prompt（提示词）是你给 AI 的指令。好的 Prompt = 准确的上下文 + 明确的目标 + 约束条件。')

add_body('Prompt 四要素公式：', bold=True, space_after=4)
add_code_block(
    '角色（你是谁）+ 上下文（在什么项目里）+ 任务（做什么）+ 约束（怎么做的要求）'
)

add_body('示例对比：', bold=True, space_after=4)

add_tip_box('差的 Prompt', [
    '帮我写一个接口',
    '→ AI 不知道什么接口、什么框架、什么数据，只能给泛泛的模板',
], "no")

add_tip_box('好的 Prompt', [
    '在 backend/app/api/materials.py 中添加一个新接口：',
    'GET /api/materials/search?keyword=xxx&page=1&page_size=20',
    '功能：按关键词搜索物料（搜 name 和 model 字段），支持分页',
    '约束：',
    '1. 用 FastAPI 路由装饰器，和文件中现有接口风格一致',
    '2. 返回格式和现有 list_materials 接口一致',
    '3. 用 SQLAlchemy 查询 Material 表',
    '4. 加上错误处理和日志',
], "ok")

add_heading_custom('常用 Prompt 模板', level=3)

add_body('模板 1：生成新功能', bold=True, space_after=4)
add_code_block(
    '在 [文件路径] 中添加 [功能描述]。\n'
    '要求：\n'
    '1. 参考文件中现有的 [类似功能] 的写法\n'
    '2. [具体约束1]\n'
    '3. [具体约束2]\n'
    '4. 加上注释和错误处理'
)

add_body('模板 2：修改现有代码', bold=True, space_after=4)
add_code_block(
    '修改 [文件路径] 中的 [函数名] 函数：\n'
    '当前问题：[描述问题]\n'
    '期望行为：[描述期望]\n'
    '约束：不要改变函数签名和返回值格式'
)

add_body('模板 3：调试排错', bold=True, space_after=4)
add_code_block(
    '运行 [命令] 时报错：\n'
    '[粘贴完整报错信息]\n'
    '\n'
    '相关代码在 [文件路径] 的 [行号] 附近。\n'
    '请分析原因并给出修复方案。'
)

add_body('模板 4：理解代码', bold=True, space_after=4)
add_code_block(
    '请解释 [文件路径] 中 [函数名] 的逻辑，\n'
    '包括：\n'
    '1. 输入参数和返回值\n'
    '2. 核心处理步骤\n'
    '3. 依赖了哪些其他模块\n'
    '4. 有什么潜在问题或优化空间'
)

add_heading_custom('4.2 用 AI 生成代码', level=2)
add_body('在 Trae / Cursor 中，有以下方式让 AI 生成代码：')

add_table_styled(
    ['方式', '操作', '适用场景'],
    [
        ['AI 对话面板', '右侧 Chat 面板输入需求', '复杂功能、多文件改动'],
        ['行内补全', '写代码时 AI 自动提示，Tab 接受', '补全单行/小段代码'],
        ['选中操作', '选中代码 → Cmd/Ctrl+K → 输入指令', '修改选中的代码'],
        ['终端 AI', '在终端用自然语言描述命令', '不记得命令时'],
        ['@文件引用', '在 Chat 中 @文件名 给 AI 上下文', '让 AI 看特定文件'],
    ],
    col_widths=[3.5, 6, 5.5]
)

add_tip_box('给 AI 上下文的技巧', [
    '@文件名：让 AI 读取指定文件（如 @materials.py）',
    '@文件夹：让 AI 读取整个目录（如 @api/）',
    '粘贴报错：直接把终端报错粘贴到 Chat',
    '选中代码：编辑器选中代码后，Chat 中 AI 能看到选中内容',
    '说明：给 AI 的上下文越精准，生成的代码越符合项目规范',
], "tip")

add_heading_custom('4.3 用 AI 修改与调试代码', level=2)
add_body('修改和调试是 AI 编程最高频的场景。掌握以下技巧能大幅提效：')

add_body('场景 1：修 Bug', bold=True, space_after=4)
add_number('复现问题，收集完整报错信息')
add_number('在 AI Chat 中粘贴报错 + 相关代码（用 @文件 引用）')
add_number('AI 给出分析原因 + 修复方案')
add_number('审查方案：理解修改逻辑，确认不会引入新问题')
add_number('应用修改，运行测试验证')

add_body('场景 2：重构代码', bold=True, space_after=4)
add_number('选中要重构的代码（函数/类/模块）')
add_number('Cmd/Ctrl+K，输入重构目标（如"提取公共逻辑为函数"）')
add_number('AI 给出重构方案')
add_number('审查：确认功能不变、可读性提升')
add_number('应用 + 跑测试')

add_tip_box('调试黄金法则', [
    '1. 先看报错信息——90%的bug报错信息已经告诉你原因了',
    '2. 报错看不懂？直接粘贴给 AI，让它解释',
    '3. AI 的修复方案一定要理解后再应用，不要盲目接受',
    '4. 修改后跑测试：pytest（后端）/ npm test（前端）',
], "warn")

add_heading_custom('4.4 AI 编程最佳实践', level=2)

add_body('DO — 推荐做法：', bold=True, color=COLOR_GREEN, space_after=4)
add_bullet('每次只让 AI 做一件小事，不要一次要求太多')
add_bullet('给 AI 精准的上下文（@文件、选中代码、粘贴报错）')
add_bullet('AI 生成代码后，逐行阅读理解，不懂就追问')
add_bullet('改完就跑测试，确认没破坏其他功能')
add_bullet('遵循项目现有代码风格（命名、结构、注释）')
add_bullet('一个功能一个 commit，消息清晰')

add_body('DON\'T — 避免做法：', bold=True, color=COLOR_RED, space_after=4)
add_bullet('不要盲目复制粘贴 AI 的代码而不理解')
add_bullet('不要让 AI 一次生成太多文件（容易失控）')
add_bullet('不要在不知道项目架构的情况下改架构层文件')
add_bullet('不要把 .env / 密钥 / 内网地址提交到 Git')
add_bullet('不要跳过测试直接提交 PR')
add_bullet('不要在 main 分支上直接开发')

add_page_break()

# ============================================================
# 第五章
# ============================================================
add_heading_custom('第五章  GitHub 协作开发流程', level=1)
add_body('本章是协作开发的核心。所有代码变更都通过 Git 管理，通过 PR 合入主干。')

add_heading_custom('5.1 Git 基础操作', level=2)
add_body('Git 是分布式版本控制系统。把它想象成"代码的时光机"——记录每次改动，随时可回退。')

add_body('核心概念：', bold=True, space_after=4)
add_table_staged = add_table_styled(
    ['概念', '说明', '类比'],
    [
        ['Repository (仓库)', '项目代码的存储空间', '一个项目文件夹'],
        ['Commit (提交)', '一次代码改动的快照', '存档点'],
        ['Branch (分支)', '代码的独立副本', '平行宇宙'],
        ['Push (推送)', '本地代码上传到远程', '交作业'],
        ['Pull (拉取)', '远程代码下载到本地', '收作业'],
        ['PR (Pull Request)', '请求把你的分支合入主干', '提交审批'],
        ['Merge (合并)', '把分支代码合入目标分支', '审批通过，合稿'],
    ],
    col_widths=[4, 5.5, 5.5]
)

add_body('日常操作命令：', bold=True, space_after=4)
add_code_block(
    '# 查看状态（最常用，随时看）\n'
    'git status\n'
    '\n'
    '# 查看改了什么\n'
    'git diff\n'
    '\n'
    '# 暂存改动\n'
    'git add 文件名          # 添加指定文件\n'
    'git add .               # 添加所有改动（谨慎）\n'
    '\n'
    '# 提交\n'
    'git commit -m "feat(xxx): 描述"\n'
    '\n'
    '# 推送到远程\n'
    'git push\n'
    '\n'
    '# 拉取最新代码\n'
    'git pull'
)

add_heading_custom('5.2 分支模型', level=2)
add_body('本项目采用分支模型管理代码变更。核心规则：main 分支受保护，禁止直推，所有改动走 PR。')

add_table_styled(
    ['分支类型', '命名格式', '用途'],
    [
        ['主干', 'main', '稳定发布版本，只接 PR merge'],
        ['功能分支', 'feature/<scope>-<desc>', '开发新功能'],
        ['修复分支', 'bugfix/<desc>', '修复 Bug'],
        ['重构分支', 'refactor/<desc>', '代码重构'],
        ['架构分支', 'feature/arch-<desc>', '架构层改动（强制 review）'],
    ],
    col_widths=[3, 5, 7]
)

add_body('创建分支的标准流程：', bold=True, space_after=4)
add_code_block(
    '# 1. 切到 main 并拉取最新\n'
    'git checkout main\n'
    'git pull\n'
    '\n'
    '# 2. 从最新 main 创建功能分支\n'
    'git checkout -b feature/csv-export-batch\n'
    '\n'
    '# 3. 在分支上开发、提交\n'
    'git add 文件\n'
    'git commit -m "feat(csv): 批量导出功能"\n'
    '\n'
    '# 4. 推送分支到远程\n'
    'git push -u origin feature/csv-export-batch'
)

add_tip_box('分支命名规范', [
    'feature/ 前缀：新功能',
    'bugfix/ 前缀：修 Bug',
    'refactor/ 前缀：重构',
    'feature/arch- 前缀：架构层改动',
    '示例：feature/g25a-parallel-gen、bugfix/pdf-upload-error',
], "tip")

add_heading_custom('5.3 PR（Pull Request）流程', level=2)
add_body('PR 是把你的分支代码合入 main 的审批流程。这是协作开发的核心环节。')

add_body('PR 完整流程：', bold=True, space_after=4)

add_number('确保代码已推送到远程分支')
add_number('在 GitHub 网页上打开 PR：base=main ← compare=你的分支')
add_number('填写 PR 模板：')
add_bullet('改动概述：一句话说明做了什么')
add_bullet('是否触碰架构层：是/否（触碰了需标 [architecture]）')
add_bullet('自测结果：跑了什么测试，结果如何')
add_number('等待 Review（@alerlocked 审查）')
add_number('按 Review 意见修改代码，push 到同一分支（PR 自动更新）')
add_number('Review 通过 → Merge → 删除远程分支')

add_body('Commit 规范：', bold=True, space_after=4)
add_code_block(
    '<type>(<scope>): <subject>\n'
    '\n'
    '# type 可选值：\n'
    '#   feat     - 新功能\n'
    '#   fix      - 修 Bug\n'
    '#   refactor - 重构（不改功能）\n'
    '#   test     - 测试相关\n'
    '#   docs     - 文档\n'
    '#   chore    - 构建/工具/杂项\n'
    '\n'
    '# 示例：\n'
    'feat(g25a): per-row parallel generation\n'
    'fix(frontend): table column align\n'
    'refactor(orchestrator): cleanup dead workflow code'
)

add_heading_custom('5.4 Code Review', level=2)
add_body('Code Review 是保证代码质量的最后一道关卡。本项目使用"南天门多维审查"：')

add_table_styled(
    ['审查维度', '检查内容', '严重级别'],
    [
        ['Bug 检测', '逻辑错误、空指针、边界条件', '🔴 blocker'],
        ['安全审查', '密钥泄露、注入风险、权限问题', '🔴 blocker'],
        ['架构越界', '功能 PR 是否混入架构层文件', '🔴 blocker'],
        ['项目经验', '匹配已知踩坑（exp-*.md / pitfalls）', '🟡 warn'],
        ['代码品味', '命名、结构、复杂度、注释', '⚪ nit'],
    ],
    col_widths=[3, 7, 5]
)

add_body('Review 结果分级：', bold=True, space_after=4)
add_bullet('🔴 blocker（必修）：必须修复后才能 merge')
add_bullet('🟡 warn（应修）：建议修复，评估后决定')
add_bullet('⚪ nit（可选）：锦上添花，不强制')

add_tip_box('处理 Review 反馈', [
    '1. 逐条阅读 Review 意见',
    '2. 同意的：修改代码 → push（PR 自动更新）',
    '3. 不同意的：在 PR 里礼貌回复说明理由',
    '4. blocker 必须全部解决才能 merge',
    '5. 不要 force push（会让 Review 评论丢失）',
], "tip")

add_heading_custom('5.5 冲突解决', level=2)
add_body('当你的分支和 main 都改了同一处代码时，合并会产生冲突。解决冲突是协作开发的常见操作。')

add_code_block(
    '# 1. 拉取最新 main 到本地\n'
    'git checkout main\n'
    'git pull\n'
    '\n'
    '# 2. 切回你的分支\n'
    'git checkout feature/your-feature\n'
    '\n'
    '# 3. 合并 main 到你的分支\n'
    'git merge main\n'
    '# 或者用 rebase（更干净的历史）\n'
    'git rebase main\n'
    '\n'
    '# 4. 如果有冲突，Git 会提示冲突文件\n'
    '#    打开冲突文件，找到 <<<<<<< 标记\n'
    '#    手动选择保留哪些代码，删除冲突标记\n'
    '\n'
    '# 5. 解决冲突后，标记为已解决\n'
    'git add 冲突文件\n'
    '\n'
    '# 6. 继续合并/rebase\n'
    'git commit            # merge 方式\n'
    'git rebase --continue # rebase 方式\n'
    '\n'
    '# 7. 推送\n'
    'git push'
)

add_tip_box('冲突解决技巧', [
    '冲突看不懂？把冲突部分粘贴给 AI，让它分析两边改了什么，建议保留哪个。',
    '不确定保留哪个？在 PR 里 @alerlocked 讨论，不要盲目选择。',
    '本项目规定：不擅自 pull/merge/rebase 解决分叉，分叉在 PR 里讨论。',
], "warn")

add_page_break()

# ============================================================
# 第六章
# ============================================================
add_heading_custom('第六章  实战演练：从零完成一个功能', level=1)
add_body('本章通过一个完整示例，带你走完从建分支到 PR merge 的全流程。')

add_heading_custom('6.1 任务：添加一个新 API 端点', level=2)
add_body('任务目标：在后端添加一个"按关键词搜索物料"的 API 端点。')
add_code_block(
    'GET /api/materials/search?keyword=螺钉&page=1&page_size=20\n'
    '\n'
    '返回：匹配的物料列表（按 name 和 model 字段搜索）'
)

add_heading_custom('6.2 Step 1 — 创建分支', level=2)
add_code_block(
    '# 切到 main 并拉取最新\n'
    'git checkout main\n'
    'git pull\n'
    '\n'
    '# 创建功能分支\n'
    'git checkout -b feature/material-search-api'
)

add_heading_custom('6.3 Step 2 — 用 AI 生成代码', level=2)
add_body('在 Trae 的 AI Chat 面板中输入 Prompt：')
add_code_block(
    '在 @backend/app/api/materials.py 中添加一个物料搜索接口。\n'
    '\n'
    '需求：\n'
    '- GET /materials/search?keyword=xxx&page=1&page_size=20\n'
    '- 按 name 和 model 字段做模糊搜索（LIKE）\n'
    '- 支持分页，返回格式参考文件中现有的 list_materials 接口\n'
    '\n'
    '约束：\n'
    '1. 使用 FastAPI 路由装饰器，风格和文件中现有接口一致\n'
    '2. 用 SQLAlchemy 查询 Material 表\n'
    '3. 加上错误处理和日志（用 get_logger）\n'
    '4. 关键词为空时返回空列表，不报错'
)

add_body('AI 会生成类似如下的代码：', bold=True, space_after=4)
add_code_block(
    '@router.get("/materials/search")\n'
    'async def search_materials(\n'
    '    keyword: str = Query("", description="搜索关键词"),\n'
    '    page: int = Query(1, ge=1, description="页码"),\n'
    '    page_size: int = Query(20, ge=1, le=100, description="每页数量"),\n'
    '    db: Session = Depends(get_db)\n'
    '):\n'
    '    """按关键词搜索物料"""\n'
    '    logger.info(f"搜索物料: keyword={keyword}, page={page}")\n'
    '    try:\n'
    '        query = db.query(Material)\n'
    '        if keyword:\n'
    '            pattern = f"%{keyword}%"\n'
    '            query = query.filter(\n'
    '                or_(Material.name.like(pattern),\n'
    '                    Material.model.like(pattern))\n'
    '            )\n'
    '        total = query.count()\n'
    '        items = query.offset((page - 1) * page_size)\\\n'
    '                    .limit(page_size).all()\n'
    '        return {"total": total, "items": [...]}\n'
    '    except Exception as e:\n'
    '        logger.error(f"搜索物料失败: {e}")\n'
    '        return {"total": 0, "items": []}'
)

add_tip_box('审查 AI 生成的代码', [
    '1. 检查路由路径是否和现有接口风格一致',
    '2. 检查是否正确导入了 or_、Query、Depends 等',
    '3. 检查错误处理是否合理（不应 500，应优雅降级）',
    '4. 检查返回格式是否和现有接口一致',
    '5. 不懂的地方问 AI 解释，搞懂了再保存',
], "warn")

add_heading_custom('6.4 Step 3 — 本地测试', level=2)
add_code_block(
    '# 启动后端\n'
    'cd backend\n'
    'python main.py\n'
    '\n'
    '# 另开终端，测试接口\n'
    'curl "http://127.0.0.1:8000/api/materials/search?keyword=螺钉"\n'
    '\n'
    '# 跑相关测试\n'
    'pytest tests/ -k "material"'
)

add_heading_custom('6.5 Step 4 — 提交与推送', level=2)
add_code_block(
    '# 查看改了哪些文件\n'
    'git status\n'
    'git diff\n'
    '\n'
    '# 暂存（只添加你改的文件，不要 git add .）\n'
    'git add backend/app/api/materials.py\n'
    '\n'
    '# 提交（遵循 commit 规范）\n'
    'git commit -m "feat(materials): add keyword search API endpoint"\n'
    '\n'
    '# 推送\n'
    'git push -u origin feature/material-search-api'
)

add_heading_custom('6.6 Step 5 — 开 PR 与处理 Review', level=2)
add_body('在 GitHub 网页操作：')
add_number('进入仓库页面，GitHub 会提示 "Compare & pull request"')
add_number('base: main ← compare: feature/material-search-api')
add_number('填写 PR 模板：')
add_code_block(
    '## 改动概述\n'
    '添加物料关键词搜索 API：GET /api/materials/search\n'
    '支持按 name 和 model 模糊搜索，分页返回。\n'
    '\n'
    '## 是否触碰架构层\n'
    '否（仅新增 API 端点，未修改 agents/services/database.py）\n'
    '\n'
    '## 自测结果\n'
    '- curl 测试 keyword=螺钉 返回正确结果\n'
    '- pytest tests/ -k material 全部通过\n'
    '- 无新增 lint 错误'
)
add_number('提交 PR，等待 @alerlocked Review')
add_number('如有 Review 反馈，修改后 push 到同一分支（PR 自动更新）')
add_number('Review 通过 → Merge → 删除远程分支')

add_tip_box('恭喜！', '你已完成从建分支到 PR merge 的全流程。实际开发中重复这个循环即可。', "ok")

add_page_break()

# ============================================================
# 第七章
# ============================================================
add_heading_custom('第七章  常见问题与避坑指南', level=1)

add_heading_custom('环境与配置', level=2)

add_body('Q: 后端启动报 ModuleNotFoundError？', bold=True, color=COLOR_PRIMARY, space_after=4)
add_body('A: 依赖没装全。确保在正确的 conda 环境中执行了 pip install -r requirements.txt。用 conda activate craftdoc 激活环境后再启动。', indent=True)

add_body('Q: 前端 npm install 报错？', bold=True, color=COLOR_PRIMARY, space_after=4)
add_body('A: 1) 检查 Node.js 版本 >= 18；2) 删除 node_modules 和 package-lock.json 后重试；3) 切换淘宝镜像。', indent=True)

add_body('Q: 后端启动但 AI 功能不工作？', bold=True, color=COLOR_PRIMARY, space_after=4)
add_body('A: 检查 .env 中的 LLM 配置。后端启动时会打印 LLM/VLM 连通性检查结果。不通则检查地址和密钥。', indent=True)

add_body('Q: .env 文件在哪里找？', bold=True, color=COLOR_PRIMARY, space_after=4)
add_body('A: .env 不进 Git。从 backend/.env.example 拷贝一份，填入实际的 LLM/VLM 地址和密钥。配置找 @alerlocked 要。', indent=True)

add_heading_custom('Git 与 GitHub', level=2)

add_body('Q: git push 被拒绝（rejected）？', bold=True, color=COLOR_PRIMARY, space_after=4)
add_body('A: 远程有你本地没有的提交。先 git pull 拉取，如有冲突解决后再 push。在 feature 分支上正常 pull/push 即可。', indent=True)

add_body('Q: 不小心提交了 .env / 密钥怎么办？', bold=True, color=COLOR_PRIMARY, space_after=4)
add_body('A: 立即联系 @alerlocked。不要试图自己删（Git 历史里还有）。以后用 git add 指定文件名，不用 git add .。', indent=True)

add_body('Q: commit message 写错了怎么办？', bold=True, color=COLOR_PRIMARY, space_after=4)
add_body('A: 还没 push：git commit --amend 修改最近一条。已 push：在 PR 里说明即可，不必纠结。', indent=True)

add_heading_custom('AI 编程', level=2)

add_body('Q: AI 生成的代码跑不通？', bold=True, color=COLOR_PRIMARY, space_after=4)
add_body('A: 把报错信息粘贴给 AI，让它分析修复。常见原因：1) 导入缺失；2) API 版本差异；3) 项目上下文不够。给 AI 更多上下文（@文件）通常能解决。', indent=True)

add_body('Q: AI 改了不该改的文件（架构层）？', bold=True, color=COLOR_PRIMARY, space_after=4)
add_body('A: 撤销那些改动（git checkout 文件名），只保留功能相关的改动。架构层改动需独立 PR。在 Prompt 中明确告诉 AI"不要修改 xxx 文件"。', indent=True)

add_body('Q: AI 生成的代码看不懂？', bold=True, color=COLOR_PRIMARY, space_after=4)
add_body('A: 选中代码问 AI"解释这段代码"。不懂的代码不要提交。先搞懂逻辑，确认正确后再用。', indent=True)

add_heading_custom('项目特定避坑', level=2)

add_tip_box('项目避坑清单', [
    '1. 上传新 PDF 文档后，需重启后端清 HierarchicalContext 缓存，否则新文档不可见',
    '2. 架构层文件（agents/**、hierarchical_context.py、knowledge_graph.py、database.py、agent.py 主链、ARCHITECTURE.md）改动需独立 [architecture] PR',
    '3. 向量检索（chromadb/SearchAgent）已删除，不要尝试恢复',
    '4. Workflow 编排是死代码已清理，实际走 _dispatch_to_sub_agent',
    '5. 前后端 column key 必须对齐（有 guard hook 检测）',
    '6. SQLite 并发写会撞锁，当前为单 worker',
    '7. 不提交业务数据（.docx/.db 等），.gitignore 已排除',
    '8. 不提交内网真实 IP，脱敏用占位符 SERVER_IP',
], "warn")

add_page_break()

# ============================================================
# 第八章
# ============================================================
add_heading_custom('第八章  进阶技巧与资源', level=1)

add_heading_custom('8.1 AI 编程进阶技巧', level=2)

add_body('技巧 1：分步拆解复杂任务', bold=True, space_after=4)
add_body('不要让 AI 一次做太多。把大功能拆成小步骤，每步生成一段代码，验证后再继续。这样每步都可控，出错容易定位。', indent=True)

add_body('技巧 2：让 AI 先写测试（TDD）', bold=True, space_after=4)
add_body('先让 AI 根据需求写测试用例，再让 AI 写实现代码直到测试通过。这样能确保代码正确性。', indent=True)

add_body('技巧 3：用 AI 做代码审查', bold=True, space_after=4)
add_body('提交前，把改动粘贴给 AI："审查这段代码，检查 bug、安全问题和优化空间"。AI 能发现很多你没注意到的问题。', indent=True)

add_body('技巧 4：建立项目级 AI 上下文', bold=True, space_after=4)
add_body('在 Trae/Cursor 中配置项目规则文件（如 .trae/rules 或 .cursorrules），让 AI 了解项目规范、代码风格、禁止事项。这样每次对话不用重复说明。', indent=True)

add_body('技巧 5：善用 @ 引用', bold=True, space_after=4)
add_body('在 AI Chat 中用 @文件名 引用相关文件，让 AI 看到完整上下文。这是生成符合项目规范代码的关键。', indent=True)

add_heading_custom('8.2 学习资源', level=2)

add_table_styled(
    ['资源', '说明', '链接'],
    [
        ['Git 教程', '廖雪峰 Git 教程（中文）', 'liaoxuefeng.com'],
        ['FastAPI 文档', '后端框架官方文档', 'fastapi.tiangolo.com'],
        ['React 文档', '前端框架官方文档', 'react.dev'],
        ['TypeScript 文档', 'TS 类型系统', 'typescriptlang.org'],
        ['GitHub Flow', 'GitHub 协作流程指南', 'docs.github.com'],
        ['Prompt 工程', 'OpenAI Prompt 工程指南', 'platform.openai.com'],
    ],
    col_widths=[3.5, 5.5, 6]
)

add_heading_custom('8.3 项目关键文档索引', level=2)
add_table_styled(
    ['文档', '角色', '何时读'],
    [
        ['CLAUDE.md', '技术栈 / 怎么跑', '第一次上手'],
        ['ARCHITECTURE.md', '唯一架构源', '改架构前必读'],
        ['CONTRIBUTING.md', '协作规范', '提交 PR 前必读'],
        ['ONBOARDING.md', '新人上手', '第一天看'],
        ['DEV-LOG.md', '进度 / 历史决策', '了解项目现状'],
        ['VISION.md', '项目北极星', '理解项目方向'],
        ['CODE-WIKI.md', '代码 Wiki', '需要了解模块细节时'],
    ],
    col_widths=[4, 5, 6]
)

add_heading_custom('8.4 求助渠道', level=2)
add_bullet('环境/配置问题 → 找 @alerlocked 要 .env 配置')
add_bullet('不确定改动是否越界（碰了架构层？）→ PR 里直接 @alerlocked 问')
add_bullet('代码看不懂 → 选中代码问 AI"解释这段代码"')
add_bullet('Git 操作出错 → 把 git 命令和报错粘贴给 AI 分析')
add_bullet('完整规范（分支模型 / commit / 禁区 / hook）→ CONTRIBUTING.md')

# ============================================================
# 附录：速查卡
# ============================================================
add_page_break()
add_heading_custom('附录  速查卡', level=1)

add_heading_custom('日常开发 5 步循环', level=2)
add_code_block(
    '# 1. 从最新 main 切分支\n'
    'git checkout main && git pull\n'
    'git checkout -b feature/<你的功能>\n'
    '\n'
    '# 2. 开发 + 提交\n'
    'git add <files>\n'
    'git commit -m "feat(xxx): 一句话描述"\n'
    '\n'
    '# 3. 推分支\n'
    'git push -u origin feature/<你的功能>\n'
    '\n'
    '# 4. GitHub 开 PR（base=main ← 你的分支）\n'
    '# 5. 等 review → 改 → merge'
)

add_heading_custom('Commit 规范速查', level=2)
add_code_block(
    'feat(xxx): 新功能\n'
    'fix(xxx): 修 Bug\n'
    'refactor(xxx): 重构\n'
    'test(xxx): 测试\n'
    'docs(xxx): 文档\n'
    'chore(xxx): 杂项'
)

add_heading_custom('启动命令速查', level=2)
add_code_block(
    '# 后端\n'
    'cd backend && conda activate craftdoc && python main.py  # :8000\n'
    '\n'
    '# 前端\n'
    'cd frontend && npm run dev  # :3000\n'
    '\n'
    '# 测试\n'
    'cd backend && pytest                    # 后端全量\n'
    'cd backend && pytest -k "关键词"        # 后端指定\n'
    'cd frontend && npm test                 # 前端'
)

add_heading_custom('架构层文件清单（改动需独立 PR）', level=2)
add_bullet('backend/app/agents/**（Agent 系统）')
add_bullet('backend/app/services/hierarchical_context.py（上下文检索）')
add_bullet('backend/app/services/knowledge_graph.py（知识图谱）')
add_bullet('backend/app/models/database.py（数据库表/字段）')
add_bullet('backend/app/api/agent.py 的 generate-stream 主链')
add_bullet('ARCHITECTURE.md（架构文档）')

add_tip_box('一句话总结', [
    '从 main 切分支 → 用 AI 写代码 → 跑测试 → 提 commit → 推分支 → 开 PR → 等 review → merge',
    '拿不准的事，在 PR 里问 @alerlocked。',
], "ok")

# ============================================================
# 保存文档
# ============================================================
output_path = '/workspace/AI编程上手与GitHub协作开发指南.docx'
doc.save(output_path)
print(f'文档已生成：{output_path}')
