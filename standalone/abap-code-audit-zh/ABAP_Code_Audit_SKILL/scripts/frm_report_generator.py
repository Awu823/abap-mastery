#!/usr/bin/env python3
"""
ABAP Report Generator - 报告生成器
支持MB/TXT/PDF/HTML多种输出格式
支持词元配置文件（token.json）自定义报告用词风格

Author: 吴平
联系方式: 13574840501 | 微信号：wuping800223
Date: 2026-04-20
Version: 2.1.0
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import asdict

from frm_audit_single_file import AuditReport, AuditIssue


class TokenLoader:
    """词元加载器 - 从token.json加载报告用词"""
    
    _instance = None
    _tokens = None
    
    def __new__(cls, token_file: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, token_file: str = None):
        if token_file is None:
            token_file = Path(__file__).parent.parent / 'token.json'
        self.token_file = Path(token_file)
        self._tokens = self._load_tokens()
    
    def _load_tokens(self) -> Dict:
        """加载词元配置"""
        if not self.token_file.exists():
            return self._get_default_tokens()
        
        try:
            with open(self.token_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 返回除注释字段外的所有词元
            return {k: v for k, v in data.items() if not k.startswith('_')}
        except Exception:
            return self._get_default_tokens()
    
    def _get_default_tokens(self) -> Dict:
        """获取默认词元"""
        return {
            'report': {
                'title': 'ABAP代码审计报告',
                'title_prefix': '🔍',
                'separator': '=',
                'footer_author': 'Author: 吴平 | 联系方式: 13574840501',
                'footer_time_format': '报告生成时间: {time}'
            },
            'sections': {
                'version_info': '【审计版本信息】',
                'file_info': '【文件信息】',
                'audit_summary': '审计汇总',
                'code_metrics': '代码度量',
                'version_diff': '版本差异说明',
                'issue_details': '问题详情',
                'no_issues': '✅ 未检测到问题！代码质量良好。'
            },
            'labels': {
                'target_version': '目标ABAP版本',
                'product': '对应产品',
                'file_name': '文件名称',
                'file_path': '文件路径',
                'audit_time': '审计时间',
                'source_type': '代码来源',
                'confidence': '置信度',
                'total_lines': '代码总行数',
                'total_issues': '问题总计',
                'lines_of_code': '代码行数',
                'lines_of_comments': '注释行数',
                'comment_ratio': '注释比例',
                'cyclomatic_complexity': '圈复杂度',
                'issue_count': '个'
            },
            'severity': {
                'critical': {'label': '严重问题', 'emoji': '🔴', 'color_class': 'critical'},
                'high': {'label': '高风险问题', 'emoji': '🟠', 'color_class': 'high'},
                'medium': {'label': '中等问题', 'emoji': '🟡', 'color_class': 'medium'},
                'low': {'label': '低风险问题', 'emoji': '🟢', 'color_class': 'low'}
            },
            'issue_fields': {
                'line': '行号',
                'rule': '规则',
                'category': '类别',
                'problem': '问题',
                'code': '代码',
                'suggestion': '建议'
            },
            'messages': {
                'discovered': '发现 {count} 个问题',
                'line_prefix': '行',
                'rule_prefix': '[{rule_id}]',
                'no_problem_found': '未发现问题',
                'latest_recommended': '（推荐）',
                'latest_version': '最新',
                'version_diff_prefix': '📌',
                'warning_prefix': '⚠️',
                'check_pass_prefix': '✅'
            },
            'category_names': {
                'performance': '性能',
                'security': '安全',
                'quality': '质量',
                'best_practice': '最佳实践'
            },
            'format_selection': {
                'title': '💾 报告已生成！请选择保存格式',
                'option_txt': 'TXT',
                'option_txt_desc': '纯文本格式，适合快速查看',
                'option_html': 'HTML',
                'option_html_desc': '网页格式，样式美观（推荐）',
                'option_json': 'JSON',
                'option_json_desc': 'JSON格式，适合程序处理',
                'option_pdf': 'PDF',
                'option_pdf_desc': 'PDF文档，适合打印存档',
                'option_all': 'ALL',
                'option_all_desc': '保存所有格式',
                'prompt': '请输入选项',
                'default': '默认'
            }
        }
    
    def get(self, *args, default=''):
        """获取指定路径的词元，如 get('severity', 'critical', 'label') 或 get('severity', default={})"""
        # 处理两种调用方式：
        # 1. get('a', 'b', 'c') -> keys = ('a', 'b', 'c')
        # 2. get('severity', default={}) -> args = ('severity',), default = {}
        if args and isinstance(args[-1], dict) and 'default' not in args:
            # 检测到字典作为最后一个参数，视为 default
            keys = args[:-1]
            default = args[-1]
        else:
            keys = args
        
        value = self._tokens
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, default)
            else:
                return default
        return value if value else default
    
    @property
    def tokens(self) -> Dict:
        """获取所有词元"""
        return self._tokens


class ReportGenerator:
    """报告生成器 - 支持从token.json读取用词"""
    
    def __init__(self, output_dir: Optional[str] = None, token_file: Optional[str] = None):
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tokens = TokenLoader(token_file)
    
    def _sep(self, width: int = 70) -> str:
        """获取分隔符"""
        sep_char = self.tokens.get('report', 'separator', default='=')
        return sep_char * width
    
    def _t(self, *keys, default='') -> str:
        """快捷获取词元"""
        return self.tokens.get(*keys, default=default)
    
    def generate_text(self, report: AuditReport, output_path: Optional[str] = None) -> str:
        """生成TXT文本报告"""
        lines = []
        sep = self._sep()
        
        lines.append(sep)
        lines.append(f"                    {self._t('report', 'title')}")
        lines.append(sep)
        lines.append("")
        
        # ABAP版本信息
        if report.abap_version:
            lines.append(self._t('sections', 'version_info'))
            lines.append(f"  {self._t('labels', 'target_version')}: {report.abap_version}")
            if report.abap_product:
                lines.append(f"  {self._t('labels', 'product')}: {report.abap_product}")
            lines.append("")
        
        lines.append(self._t('sections', 'file_info'))
        lines.append(f"  {self._t('labels', 'file_name')}: {report.file_name}")
        lines.append(f"  {self._t('labels', 'file_path')}: {report.file_path}")
        lines.append(f"  {self._t('labels', 'audit_time')}: {report.timestamp}")
        lines.append(f"  {self._t('labels', 'total_lines')}: {report.total_lines}")
        lines.append(f"  {self._t('labels', 'source_type')}: {report.source_type} ({self._t('labels', 'confidence')}: {report.source_confidence:.0%})")
        lines.append("")
        
        summary = report.summary
        lines.append("-" * 70)
        lines.append(self._t('sections', 'audit_summary'))
        lines.append("-" * 70)
        
        # 使用词元中的严重程度标签
        sev = self.tokens.get('severity', {})
        lines.append(f"  {sev.get('critical', {}).get('emoji', '🔴')} {sev.get('critical', {}).get('label', '严重问题')}: {summary['critical']}")
        lines.append(f"  {sev.get('high', {}).get('emoji', '🟠')} {sev.get('high', {}).get('label', '高风险问题')}: {summary['high']}")
        lines.append(f"  {sev.get('medium', {}).get('emoji', '🟡')} {sev.get('medium', {}).get('label', '中等问题')}: {summary['medium']}")
        lines.append(f"  {sev.get('low', {}).get('emoji', '🟢')} {sev.get('low', {}).get('label', '低风险问题')}: {summary['low']}")
        lines.append(f"  📊 {self._t('labels', 'total_issues')}: {report.total_issues}")
        lines.append("")
        
        if report.metrics:
            lines.append("-" * 70)
            lines.append(self._t('sections', 'code_metrics'))
            lines.append("-" * 70)
            metrics = report.metrics
            lines.append(f"  {self._t('labels', 'lines_of_code')}: {metrics.get('lines_of_code', 0)}")
            lines.append(f"  {self._t('labels', 'lines_of_comments')}: {metrics.get('lines_of_comments', 0)}")
            lines.append(f"  {self._t('labels', 'comment_ratio')}: {metrics.get('comment_ratio', 0):.1%}")
            lines.append(f"  {self._t('labels', 'cyclomatic_complexity')}: {metrics.get('cyclomatic_complexity', 0)}")
            lines.append("")
        
        # 版本差异说明
        if report.version_diff_notes:
            lines.append("-" * 70)
            lines.append(self._t('sections', 'version_diff'))
            lines.append("-" * 70)
            for note in report.version_diff_notes:
                lines.append(f"  {note}")
            lines.append("")
        
        if report.issues:
            lines.append("-" * 70)
            lines.append(self._t('sections', 'issue_details'))
            lines.append("-" * 70)
            
            severity_order = ['critical', 'high', 'medium', 'low']
            
            for sev_level in severity_order:
                sev_issues = [i for i in report.issues if i.severity == sev_level]
                if not sev_issues:
                    continue
                
                sev_info = sev.get(sev_level, {})
                sev_emoji = sev_info.get('emoji', '🔴')
                sev_label = sev_info.get('label', sev_level)
                count_label = self._t('labels', 'issue_count')
                
                lines.append(f"\n【{sev_emoji} {sev_label}】（{len(sev_issues)}{count_label}）")
                lines.append("")
                
                issue_fields = self.tokens.get('issue_fields', {})
                for issue in sev_issues:
                    lines.append(f"  {issue_fields.get('line', '行号')}: {issue.line}")
                    lines.append(f"  {issue_fields.get('rule', '规则')}: {issue.rule_id} - {issue.rule_name}")
                    
                    # 类别转换
                    category = issue.category.upper()
                    cat_names = self.tokens.get('category_names') or {}
                    if category.lower() in cat_names:
                        category = cat_names[category.lower()]
                    lines.append(f"  {issue_fields.get('category', '类别')}: {category}")
                    
                    lines.append(f"  {issue_fields.get('problem', '问题')}: {issue.message}")
                    lines.append(f"  {issue_fields.get('code', '代码')}: {issue.code}")
                    lines.append(f"  {issue_fields.get('suggestion', '建议')}: {issue.suggestion}")
                    lines.append("")
        
        lines.append(self._sep())
        lines.append(self._t('report', 'footer_time_format').format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        lines.append(self._t('report', 'footer_author'))
        lines.append(self._sep())
        
        content = '\n'.join(lines)
        
        if output_path:
            Path(output_path).write_text(content, encoding='utf-8')
        
        return content
    
    def generate_html(self, report: AuditReport, output_path: Optional[str] = None) -> str:
        """生成HTML报告"""
        summary = report.summary
        sev = self.tokens.get('severity', {})
        
        issue_rows = []
        issue_fields = self.tokens.get('issue_fields', {})
        
        for issue in report.issues:
            severity_class = f"severity-{issue.severity}"
            sev_info = sev.get(issue.severity, {})
            
            # 类别转换
            category = issue.category.upper()
            cat_names = self.tokens.get('category_names') or {}
            if category.lower() in cat_names:
                category = cat_names[category.lower()]
            
            issue_rows.append(f"""
                <tr>
                    <td>{issue.line}</td>
                    <td><span class="severity-badge {severity_class}">{sev_info.get('label', issue.severity.upper())}</span></td>
                    <td>{category}</td>
                    <td>{issue.rule_id}</td>
                    <td>{issue.message}</td>
                    <td class="code-cell">{issue.code}</td>
                    <td class="suggestion">{issue.suggestion}</td>
                </tr>
            """)
        
        issue_table = '\n'.join(issue_rows) if issue_rows else f'<tr><td colspan="7">{self._t("messages", "no_problem_found", default="未发现问题")}</td></tr>'
        
        # 版本差异说明
        version_diff_section = ""
        if report.version_diff_notes:
            diff_notes_html = '\n'.join([f'<li>{note}</li>' for note in report.version_diff_notes])
            version_diff_section = f"""
                <div class="section">
                    <h2>📌 {self._t('sections', 'version_diff', default='版本差异说明')}</h2>
                    <ul class="version-notes">
                        {diff_notes_html}
                    </ul>
                </div>
            """
        
        report_title = self._t('report', 'title', default='ABAP代码审计报告')
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_title} - {report.file_name}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ 
            font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif; 
            background: white;
            min-height: 100vh; padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            background: white; border-radius: 16px; padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1); margin-bottom: 20px;
        }}
        .header h1 {{ color: #333; margin-bottom: 10px; font-size: 28px; }}
        .header h1::before {{ content: '{self._t("report", "title_prefix", default="🔍")} '; }}
        .file-info {{ color: #666; line-height: 1.8; }}
        .file-info strong {{ color: #333; }}
        .summary {{
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;
            margin: 20px 0;
        }}
        .summary-card {{
            padding: 25px; border-radius: 12px; text-align: center;
            color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .critical {{ background: linear-gradient(135deg, #dc2626, #ef4444); }}
        .high {{ background: linear-gradient(135deg, #d97706, #f59e0b); }}
        .medium {{ background: linear-gradient(135deg, #ca8a04, #eab308); }}
        .low {{ background: linear-gradient(135deg, #16a34a, #22c55e); }}
        .summary-card h2 {{ font-size: 3em; margin-bottom: 5px; }}
        .summary-card p {{ font-size: 14px; opacity: 0.9; }}
        .section {{
            background: white; border-radius: 16px; padding: 25px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1); margin-bottom: 20px;
        }}
        .section h2 {{ color: #333; border-bottom: 3px solid #d97706; padding-bottom: 10px; margin-bottom: 20px; }}
        .metrics-grid {{
            display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;
        }}
        .metric-item {{
            background: #fef9ee; padding: 15px; border-radius: 8px;
            border-left: 4px solid #d97706;
        }}
        .metric-label {{ color: #666; font-size: 12px; margin-bottom: 5px; }}
        .metric-value {{ color: #333; font-size: 24px; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th {{
            background: #d97706; color: white; padding: 15px 10px;
            text-align: left; font-weight: 600;
        }}
        td {{ padding: 12px 10px; border-bottom: 1px solid #eee; vertical-align: top; }}
        tr:hover {{ background: #fffbeb; }}
        .severity-badge {{
            padding: 4px 12px; border-radius: 20px; color: white;
            font-size: 12px; font-weight: 600; display: inline-block;
        }}
        .severity-critical {{ background: #dc2626; }}
        .severity-high {{ background: #d97706; }}
        .severity-medium {{ background: #ca8a04; color: #fff; }}
        .severity-low {{ background: #16a34a; }}
        .code-cell {{
            font-family: 'Consolas', 'Monaco', monospace; font-size: 12px;
            background: #fef9ee; max-width: 300px; overflow: hidden;
            text-overflow: ellipsis; white-space: nowrap;
        }}
        .suggestion {{ color: #d97706; font-size: 13px; }}
        .version-info {{
            background: linear-gradient(135deg, #1e40af, #3b82f6);
            color: white; padding: 20px; border-radius: 12px;
            margin-bottom: 20px;
        }}
        .version-info h2 {{
            margin-bottom: 10px; font-size: 18px;
        }}
        .version-info p {{
            margin: 5px 0; opacity: 0.9;
        }}
        .version-badge {{
            display: inline-block; background: rgba(255,255,255,0.2);
            padding: 4px 12px; border-radius: 20px; font-size: 14px;
            margin-right: 10px;
        }}
        .version-notes {{
            list-style: none; padding: 0;
        }}
        .version-notes li {{
            padding: 10px 15px; margin: 5px 0;
            background: #fef9ee; border-radius: 8px;
            border-left: 4px solid #d97706;
        }}
        .footer {{
            text-align: center; color: #333; padding: 20px;
            font-size: 14px;
            border-top: 2px solid #d97706;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="version-info">
            <h2>📌 {self._t('sections', 'version_info', default='审计版本信息').replace('【', '').replace('】', '')}</h2>
            <p><span class="version-badge">{report.abap_version or "未指定"}</span><strong>{self._t('labels', 'target_version', default='目标ABAP版本')}</strong></p>
            <p>{self._t('labels', 'product', default='对应产品')}: {report.abap_product or "未指定"}</p>
        </div>
        
        <div class="header">
            <h1>{report_title}</h1>
            <div class="file-info">
                <p><strong>{self._t('labels', 'file_name', default='文件名称')}:</strong> {report.file_name}</p>
                <p><strong>{self._t('labels', 'file_path', default='文件路径')}:</strong> {report.file_path}</p>
                <p><strong>{self._t('labels', 'audit_time', default='审计时间')}:</strong> {report.timestamp}</p>
                <p><strong>{self._t('labels', 'source_type', default='代码来源')}:</strong> {report.source_type} ({self._t('labels', 'confidence', default='置信度')}: {report.source_confidence:.0%})</p>
            </div>
        </div>
        
        <div class="summary">
            <div class="summary-card critical">
                <h2>{summary['critical']}</h2>
                <p>{sev.get('critical', {}).get('emoji', '🔴')} {sev.get('critical', {}).get('label', '严重问题')}</p>
            </div>
            <div class="summary-card high">
                <h2>{summary['high']}</h2>
                <p>{sev.get('high', {}).get('emoji', '🟠')} {sev.get('high', {}).get('label', '高风险问题')}</p>
            </div>
            <div class="summary-card medium">
                <h2>{summary['medium']}</h2>
                <p>{sev.get('medium', {}).get('emoji', '🟡')} {sev.get('medium', {}).get('label', '中等问题')}</p>
            </div>
            <div class="summary-card low">
                <h2>{summary['low']}</h2>
                <p>{sev.get('low', {}).get('emoji', '🟢')} {sev.get('low', {}).get('label', '低风险问题')}</p>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 {self._t('sections', 'code_metrics', default='代码度量')}</h2>
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-label">{self._t('labels', 'lines_of_code', default='代码行数')}</div>
                    <div class="metric-value">{report.metrics.get('lines_of_code', 0)}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">{self._t('labels', 'lines_of_comments', default='注释行数')}</div>
                    <div class="metric-value">{report.metrics.get('lines_of_comments', 0)}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">{self._t('labels', 'comment_ratio', default='注释比例')}</div>
                    <div class="metric-value">{report.metrics.get('comment_ratio', 0):.1%}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">{self._t('labels', 'cyclomatic_complexity', default='圈复杂度')}</div>
                    <div class="metric-value">{report.metrics.get('cyclomatic_complexity', 0)}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">{self._t('labels', 'total_issues', default='问题总数')}</div>
                    <div class="metric-value">{report.total_issues}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">{self._t('labels', 'total_lines', default='总行数')}</div>
                    <div class="metric-value">{report.total_lines}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>📋 {self._t('sections', 'issue_details', default='问题详情')}</h2>
            <table>
                <thead>
                    <tr>
                        <th>{self._t('issue_fields', 'line', default='行号')}</th>
                        <th>{self._t('labels', 'target_version', default='严重程度').replace('目标ABAP版本', '严重程度') if self._t('labels', 'target_version') == '目标ABAP版本' else '严重程度'}</th>
                        <th>{self._t('issue_fields', 'category', default='类别')}</th>
                        <th>规则ID</th>
                        <th>{self._t('issue_fields', 'problem', default='问题描述')}</th>
                        <th>{self._t('issue_fields', 'code', default='问题代码')}</th>
                        <th>{self._t('issue_fields', 'suggestion', default='改进建议')}</th>
                    </tr>
                </thead>
                <tbody>
                    {issue_table}
                </tbody>
            </table>
        </div>
        
        {version_diff_section}
        
        <div class="footer">
            <p>{self._t('report', 'footer_time_format').format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</p>
            <p>{self._t('report', 'footer_author')}</p>
        </div>
    </div>
</body>
</html>"""
        
        if output_path:
            Path(output_path).write_text(html, encoding='utf-8')
        
        return html
    
    def generate_json(self, report: AuditReport, output_path: Optional[str] = None) -> str:
        """生成JSON报告"""
        json_data = report.to_dict()
        # 添加词元信息到JSON报告
        json_data['_tokens_used'] = True
        json_data['_token_source'] = str(self.tokens.token_file)
        # 添加作者联系信息（所有格式统一）
        json_data['_author'] = self.tokens.get('report', {}).get('footer_author', '吴平')
        json_data['_report_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        content = json.dumps(json_data, ensure_ascii=False, indent=2)
        
        if output_path:
            Path(output_path).write_text(content, encoding='utf-8')
        
        return content
    
    def generate_html_from_issues(self, all_issues: List, output_path: Optional[str] = None,
                                   abap_version: str = "", abap_product: str = "",
                                   audit_summary: Dict = None) -> str:
        """直接从问题列表生成HTML报告（无需AuditReport对象）"""
        from frm_audit_single_file import AuditIssue
        
        sev = self.tokens.get('severity') or {}
        issue_fields = self.tokens.get('issue_fields') or {}
        
        # 统计问题数量
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for issue in all_issues:
            sev_key = issue.severity.lower() if hasattr(issue, 'severity') else 'low'
            if sev_key in severity_counts:
                severity_counts[sev_key] += 1
        
        # 生成问题行
        issue_rows = []
        for issue in all_issues:
            severity_class = f"severity-{issue.severity}"
            sev_info = sev.get(issue.severity, {})
            
            # 类别转换
            category = issue.category.upper()
            cat_names = self.tokens.get('category_names') or {}
            if category.lower() in cat_names:
                category = cat_names[category.lower()]
            
            issue_rows.append(f"""
                <tr>
                    <td>{issue.line}</td>
                    <td><span class="severity-badge {severity_class}">{sev_info.get('label', issue.severity.upper())}</span></td>
                    <td>{category}</td>
                    <td>{issue.rule_id}</td>
                    <td>{issue.message}</td>
                    <td class="code-cell">{issue.code}</td>
                    <td class="suggestion">{issue.suggestion}</td>
                </tr>
            """)
        
        issue_table = '\n'.join(issue_rows) if issue_rows else f'<tr><td colspan="7">未发现问题</td></tr>'
        
        # 获取摘要信息
        total_files = audit_summary.get('total_files', 0) if audit_summary else 0
        total_lines = audit_summary.get('total_lines', 0) if audit_summary else 0
        total_issues = audit_summary.get('total_issues', len(all_issues))
        audit_dir = audit_summary.get('audit_dir', '') if audit_summary else ''
        
        report_title = self._t('report', 'title', default='ABAP代码审计报告')
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        footer_author = self._t('report', 'footer_author')
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_title} - {abap_version}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
            background: white;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .version-info {{
            background: linear-gradient(135deg, #1e40af, #3b82f6);
            color: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
        }}
        .version-info h2 {{
            margin-bottom: 10px;
            font-size: 18px;
        }}
        .version-info p {{
            margin: 5px 0;
            opacity: 0.9;
        }}
        .version-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 14px;
            margin-right: 10px;
        }}
        .header {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .header h1 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }}
        .header h1::before {{ content: '🔍 '; }}
        .file-info {{
            color: #666;
            line-height: 1.8;
        }}
        .file-info strong {{
            color: #333;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        .summary-card {{
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .critical {{ background: linear-gradient(135deg, #dc2626, #ef4444); }}
        .high {{ background: linear-gradient(135deg, #d97706, #f59e0b); }}
        .medium {{ background: linear-gradient(135deg, #ca8a04, #eab308); }}
        .low {{ background: linear-gradient(135deg, #16a34a, #22c55e); }}
        .summary-card h2 {{
            font-size: 3em;
            margin-bottom: 5px;
        }}
        .summary-card p {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .section {{
            background: white;
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .section h2 {{
            color: #333;
            border-bottom: 3px solid #d97706;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
        }}
        .metric-item {{
            background: #fef9ee;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #d97706;
        }}
        .metric-label {{
            color: #666;
            font-size: 12px;
            margin-bottom: 5px;
        }}
        .metric-value {{
            color: #333;
            font-size: 24px;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th {{
            background: #d97706;
            color: white;
            padding: 15px 10px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px 10px;
            border-bottom: 1px solid #eee;
            vertical-align: top;
        }}
        tr:hover {{
            background: #fffbeb;
        }}
        .severity-badge {{
            padding: 4px 12px;
            border-radius: 20px;
            color: white;
            font-size: 12px;
            font-weight: 600;
            display: inline-block;
        }}
        .severity-critical {{ background: #dc2626; }}
        .severity-high {{ background: #d97706; }}
        .severity-medium {{ background: #ca8a04; color: #fff; }}
        .severity-low {{ background: #16a34a; }}
        .code-cell {{
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            background: #fef9ee;
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .suggestion {{
            color: #d97706;
            font-size: 13px;
        }}
        .footer {{
            text-align: center;
            color: #333;
            padding: 20px;
            font-size: 14px;
            border-top: 2px solid #d97706;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="version-info">
            <h2>📌 审计版本信息</h2>
            <p><span class="version-badge">{abap_version}</span><strong>目标ABAP版本</strong></p>
            <p>对应产品: {abap_product}</p>
        </div>

        <div class="header">
            <h1>ABAP代码审计报告</h1>
            <div class="file-info">
                <p><strong>审计目录:</strong> {audit_dir}</p>
                <p><strong>审计文件:</strong> {total_files} 个</p>
                <p><strong>代码行数:</strong> {total_lines}</p>
                <p><strong>生成时间:</strong> {current_time}</p>
            </div>
        </div>

        <div class="summary">
            <div class="summary-card critical">
                <h2>{severity_counts['critical']}</h2>
                <p>🔴 严重问题</p>
            </div>
            <div class="summary-card high">
                <h2>{severity_counts['high']}</h2>
                <p>🟠 高风险问题</p>
            </div>
            <div class="summary-card medium">
                <h2>{severity_counts['medium']}</h2>
                <p>🟡 中等问题</p>
            </div>
            <div class="summary-card low">
                <h2>{severity_counts['low']}</h2>
                <p>🟢 低风险问题</p>
            </div>
        </div>

        <div class="section">
            <h2>📋 问题详情</h2>
            <table>
                <thead>
                    <tr>
                        <th>行号</th>
                        <th>严重程度</th>
                        <th>类别</th>
                        <th>规则ID</th>
                        <th>问题描述</th>
                        <th>问题代码</th>
                        <th>优化建议</th>
                    </tr>
                </thead>
                <tbody>
                    {issue_table}
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>报告生成时间: {current_time}</p>
            <p>{footer_author}</p>
        </div>
    </div>
</body>
</html>"""

        if output_path:
            Path(output_path).write_text(html, encoding='utf-8')

        return html

    def save_report(self, report: AuditReport, base_name: Optional[str] = None) -> Dict[str, str]:
        """保存所有格式的报告"""
        if base_name is None:
            base_name = Path(report.file_name).stem
        
        paths = {}
        
        txt_path = self.output_dir / f"{base_name}_report.txt"
        self.generate_text(report, str(txt_path))
        paths['txt'] = str(txt_path)
        
        html_path = self.output_dir / f"{base_name}_report.html"
        self.generate_html(report, str(html_path))
        paths['html'] = str(html_path)
        
        json_path = self.output_dir / f"{base_name}_report.json"
        self.generate_json(report, str(json_path))
        paths['json'] = str(json_path)
        
        return paths
    
    @staticmethod
    def get_format_selection_prompt() -> str:
        """获取格式选择提示（从token.json读取）"""
        token_file = Path(__file__).parent.parent / 'token.json'
        if token_file.exists():
            try:
                with open(token_file, 'r', encoding='utf-8') as f:
                    tokens = json.load(f)
                fs = tokens.get('format_selection', {})
                if fs:
                    lines = []
                    lines.append(fs.get('title', '💾 报告已生成！请选择保存格式：'))
                    lines.append("")
                    lines.append(f"  1) {fs.get('option_txt', 'TXT')}  - {fs.get('option_txt_desc', '纯文本格式')}")
                    lines.append(f"  2) {fs.get('option_html', 'HTML')} - {fs.get('option_html_desc', '网页格式（推荐）')}")
                    lines.append(f"  3) {fs.get('option_json', 'JSON')} - {fs.get('option_json_desc', 'JSON格式')}")
                    lines.append(f"  4) {fs.get('option_pdf', 'PDF')}  - {fs.get('option_pdf_desc', 'PDF文档')}")
                    lines.append(f"  5) {fs.get('option_all', 'ALL')}  - {fs.get('option_all_desc', '保存所有格式')}")
                    lines.append("")
                    lines.append(f"{fs.get('prompt', '请输入选项')} [1-5] ({fs.get('default', '默认')}: 2): ")
                    return '\n'.join(lines)
            except Exception:
                pass
        
        # 默认提示
        return """💾 报告已生成！请选择保存格式：

  1) TXT  - 纯文本格式，适合快速查看
  2) HTML - 网页格式，样式美观（推荐）
  3) JSON - JSON格式，适合程序处理
  4) PDF  - PDF文档，适合打印存档
  5) ALL  - 保存所有格式

请输入选项 [1-5] (默认2): """


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='ABAP报告生成器')
    parser.add_argument('--input', '-i', required=True, help='输入JSON文件')
    parser.add_argument('--output-dir', '-o', help='输出目录')
    parser.add_argument('--format', '-f', choices=['text', 'html', 'json', 'all'], default='all', help='输出格式')
    
    args = parser.parse_args()
    
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    issues = [AuditIssue(**issue) for issue in data.get('issues', [])]
    report = AuditReport(
        file_name=data['file_name'],
        file_path=data.get('file_path', ''),
        timestamp=data['timestamp'],
        total_lines=data['total_lines'],
        total_issues=data['total_issues'],
        source_type=data.get('source_type', 'UNKNOWN'),
        source_confidence=data.get('source_confidence', 0.0),
        issues=issues,
        metrics=data.get('metrics', {}),
        abap_version=data.get('abap_version', ''),
        abap_product=data.get('abap_product', ''),
        version_diff_notes=data.get('version_diff_notes', [])
    )
    
    generator = ReportGenerator(output_dir=args.output_dir)
    
    if args.format == 'all':
        paths = generator.save_report(report)
        print("报告已生成:")
        for fmt, path in paths.items():
            print(f"  {fmt}: {path}")
    else:
        if args.format == 'text':
            content = generator.generate_text(report)
        elif args.format == 'html':
            content = generator.generate_html(report)
        else:
            content = generator.generate_json(report)
        print(content)


if __name__ == '__main__':
    main()
