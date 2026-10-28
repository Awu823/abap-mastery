#!/usr/bin/env python3
"""
ABAP PDF Builder - PDF报告构建器（基于 reportlab）

Author: 吴平
联系方式: 13574840501 | 微信号：wuping800223
Date: 2026-04-20
Version: 3.0.0
"""

import os
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime


def _check_reportlab_available() -> bool:
    """检查 reportlab 是否可用"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        return True
    except ImportError:
        return False


class PDFBuilder:
    """PDF报告构建器（纯 reportlab 实现）"""
    
    def __init__(self, silent=False):
        self.library = 'reportlab' if _check_reportlab_available() else None
        
        if not self.library and not silent:
            print("⚠️ 警告: 未安装PDF生成库 (reportlab)")
            print("请运行以下命令安装:")
            print("  pip install reportlab")
    
    def generate_pdf(self, html_content: str, pdf_path: str) -> bool:
        """从HTML内容生成PDF"""
        if not self.library:
            return False
        
        return self._generate_with_reportlab(html_content, pdf_path)
    
    def _generate_with_reportlab(self, html_content: str, output_path: str) -> bool:
        """使用 reportlab 生成 PDF"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib import colors
            from reportlab.lib.units import cm
            
            doc = SimpleDocTemplate(
                output_path, 
                pagesize=A4,
                leftMargin=2*cm,
                rightMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            styles = getSampleStyleSheet()
            
            # 自定义样式
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=20,
                textColor=colors.HexColor('#1a365d'),
                alignment=1  # 居中
            )
            
            subtitle_style = ParagraphStyle(
                'Subtitle',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=10,
                textColor=colors.gray
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceBefore=15,
                spaceAfter=10,
                textColor=colors.HexColor('#2c5282')
            )
            
            normal_style = styles['Normal']
            normal_style.fontSize = 10
            normal_style.leading = 14
            
            elements = []
            
            # 标题
            elements.append(Paragraph("ABAP 代码审计报告", title_style))
            elements.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
            elements.append(Spacer(1, 20))
            
            # 解析 HTML 内容
            from html.parser import HTMLParser
            
            class HTMLToPDFParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.elements = []
                    self.styles = getSampleStyleSheet()
                    self.current_tag = None
                    self.skip_tags = {'script', 'style', 'head', 'link', 'meta'}
                    self.text_buffer = []
                    self.table_data = []
                    self.in_table = False
                    self.in_thead = False
                    self.in_tbody = False
                    self.in_tr = False
                    self.in_th = False
                    self.in_td = False
                    self.current_row = []
                    self.header_row = []
                    self.table_style = []
                    
                    # 样式映射
                    self.severity_colors = {
                        'critical': colors.HexColor('#c53030'),
                        'high': colors.HexColor('#dd6b20'),
                        'medium': colors.HexColor('#d69e2e'),
                        'low': colors.HexColor('#38a169')
                    }
                    
                def handle_starttag(self, tag, attrs):
                    self.current_tag = tag
                    attrs_dict = dict(attrs)
                    
                    if tag == 'h1':
                        self.text_buffer = []
                    elif tag == 'h2':
                        self.text_buffer = []
                    elif tag == 'h3':
                        self.text_buffer = []
                    elif tag == 'p':
                        self.text_buffer = []
                    elif tag == 'div':
                        self.text_buffer = []
                    elif tag == 'span':
                        self.text_buffer = []
                    elif tag == 'table':
                        self.in_table = True
                        self.table_data = []
                        self.header_row = []
                        self.table_style = []
                    elif tag == 'thead':
                        self.in_thead = True
                    elif tag == 'tbody':
                        self.in_tbody = True
                    elif tag == 'tr':
                        self.in_tr = True
                        self.current_row = []
                    elif tag == 'th':
                        self.in_th = True
                        self.text_buffer = []
                    elif tag == 'td':
                        self.in_td = True
                        self.text_buffer = []
                    elif tag == 'br':
                        if self.text_buffer:
                            self.text_buffer.append('\n')
                    elif tag == 'strong' or tag == 'b':
                        self.text_buffer.append('<b>')
                    elif tag == 'em' or tag == 'i':
                        self.text_buffer.append('<i>')
                    elif tag == 'ul':
                        self.text_buffer = []
                    elif tag == 'li':
                        if not self.text_buffer:
                            self.text_buffer = ['• ']
                        else:
                            self.text_buffer.append('\n• ')
                
                def handle_endtag(self, tag):
                    if tag == 'h1':
                        text = ''.join(self.text_buffer).strip()
                        if text:
                            self.elements.append(Paragraph(text, title_style))
                            self.elements.append(Spacer(1, 10))
                    elif tag == 'h2':
                        text = ''.join(self.text_buffer).strip()
                        if text:
                            self.elements.append(Paragraph(text, heading_style))
                    elif tag == 'h3':
                        text = ''.join(self.text_buffer).strip()
                        if text:
                            style = ParagraphStyle('H3', parent=self.styles['Normal'], 
                                                  fontSize=12, spaceBefore=8, spaceAfter=5,
                                                  textColor=colors.HexColor('#4a5568'))
                            self.elements.append(Paragraph(text, style))
                    elif tag == 'p':
                        text = ''.join(self.text_buffer).strip()
                        if text:
                            self.elements.append(Paragraph(text, normal_style))
                            self.elements.append(Spacer(1, 5))
                    elif tag == 'div':
                        text = ''.join(self.text_buffer).strip()
                        if text and not self.in_table:
                            self.elements.append(Paragraph(text, normal_style))
                    elif tag == 'span':
                        text = ''.join(self.text_buffer).strip()
                        if text:
                            self.elements.append(Paragraph(text, normal_style))
                    elif tag == 'strong' or tag == 'b':
                        self.text_buffer.append('</b>')
                    elif tag == 'em' or tag == 'i':
                        self.text_buffer.append('</i>')
                    elif tag == 'th':
                        text = ''.join(self.text_buffer).strip()
                        self.header_row.append(text)
                        self.in_th = False
                    elif tag == 'td':
                        text = ''.join(self.text_buffer).strip()
                        self.current_row.append(text)
                        self.in_td = False
                    elif tag == 'tr':
                        if self.in_thead:
                            self.table_data.insert(0, self.header_row)
                            self.header_row = []
                        elif self.current_row:
                            self.table_data.append(self.current_row)
                        self.current_row = []
                        self.in_tr = False
                    elif tag == 'thead':
                        self.in_thead = False
                    elif tag == 'tbody':
                        self.in_tbody = False
                    elif tag == 'table':
                        if self.table_data:
                            # 构建表格样式
                            table_style = TableStyle([
                                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, 0), 10),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                                ('TOPPADDING', (0, 0), (-1, 0), 8),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
                                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                                ('FONTSIZE', (0, 1), (-1, -1), 9),
                                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                                ('TOPPADDING', (0, 1), (-1, -1), 6),
                                ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
                                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#edf2f7')])
                            ])
                            
                            col_widths = [3*cm, 2*cm, 11*cm]
                            table = Table(self.table_data, colWidths=col_widths)
                            table.setStyle(table_style)
                            self.elements.append(table)
                            self.elements.append(Spacer(1, 15))
                        self.in_table = False
                        self.table_data = []
                    elif tag == 'ul':
                        text = ''.join(self.text_buffer).strip()
                        if text:
                            for line in text.split('\n'):
                                if line.strip():
                                    self.elements.append(Paragraph(line.strip(), normal_style))
                        self.text_buffer = []
                    elif tag == 'li':
                        text = ''.join(self.text_buffer).strip()
                        if text:
                            self.text_buffer = []
                    elif tag == 'br':
                        pass
                    
                    self.current_tag = None
                
                def handle_data(self, data):
                    if self.current_tag and self.current_tag not in self.skip_tags:
                        self.text_buffer.append(data)
                
                def get_elements(self):
                    return self.elements
            
            parser = HTMLToPDFParser()
            parser.feed(html_content)
            elements.extend(parser.get_elements())
            
            # 如果没有解析出内容，使用简化模式
            if len(elements) <= 3:
                elements = []
                elements.append(Paragraph("ABAP 代码审计报告", title_style))
                elements.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
                elements.append(Spacer(1, 20))
                
                # 简单提取文本
                import re
                text = re.sub(r'<[^>]+>', ' ', html_content)
                text = re.sub(r'\s+', ' ', text)
                lines = text.split('•')
                for line in lines[1:20]:  # 限制前20条
                    line = line.strip()
                    if line:
                        elements.append(Paragraph(f"• {line}", normal_style))
                        elements.append(Spacer(1, 3))
            
            doc.build(elements)
            print(f"✅ PDF报告已生成: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ ReportLab生成PDF失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def html_to_pdf(self, html_path: str, pdf_path: Optional[str] = None) -> bool:
        """将HTML文件转换为PDF"""
        if not self.library:
            return False
        
        try:
            html_content = Path(html_path).read_text(encoding='utf-8')
        except:
            html_content = Path(html_path).read_text(encoding='gbk')
        
        if pdf_path is None:
            pdf_path = str(Path(html_path).with_suffix('.pdf'))
        
        return self.generate_pdf(html_content, pdf_path)


class AuditPDFGenerator:
    """审计PDF专用生成器"""
    
    def __init__(self, silent=False):
        self.builder = PDFBuilder(silent=silent)
    
    def generate_from_html(self, html_path: str, pdf_path: Optional[str] = None) -> bool:
        """从HTML文件生成PDF"""
        return self.builder.html_to_pdf(html_path, pdf_path)
    
    def generate_from_report_data(self, report_data: dict, output_path: str) -> bool:
        """从报告数据生成PDF"""
        html = self._build_html_from_data(report_data)
        return self.builder.generate_pdf(html, output_path)
    
    def _build_html_from_data(self, data: dict) -> str:
        """将报告数据转换为HTML"""
        summary = data.get('summary', {})
        issues = data.get('issues', [])
        
        html = f"""
        <h1>ABAP代码审计报告</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <h2>审计摘要</h2>
        <p>总问题数: {summary.get('total', 0)}</p>
        <p>严重: {summary.get('critical', 0)} | 高: {summary.get('high', 0)} | 中: {summary.get('medium', 0)} | 低: {summary.get('low', 0)}</p>
        <h2>问题详情</h2>
        """
        
        for issue in issues:
            severity = issue.get('severity', 'low')
            rule_id = issue.get('rule_id', '')
            message = issue.get('message', '')
            line = issue.get('line', 0)
            code = issue.get('code', '')
            
            html += f"""
            <p><strong>[{severity.upper()}] {rule_id}</strong> - 第{line}行</p>
            <p>代码: {code}</p>
            <p>说明: {message}</p>
            <hr/>
            """
        
        return html


# 导出
__all__ = ['PDFBuilder', 'AuditPDFGenerator']
