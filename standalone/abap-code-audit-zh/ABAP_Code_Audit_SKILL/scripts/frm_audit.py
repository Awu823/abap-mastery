#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABAP代码审计工具
SKILL版本: 2.3.1

Author: 吴平
联系方式: 13574840501 | 微信号：wuping800223
Date: 2026-04-20
Version: 2.3.1 (通用目录审计脚本 - 支持多格式报告输出)
"""

import sys
import os
from pathlib import Path
import io
from datetime import datetime

# 设置输出编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加SKILL脚本路径
SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(SKILL_DIR))

from frm_file_handler import FileHandler
from frm_source_detector import ABAPSourceDetector
from frm_audit_single_file import ABAPAuditEngine, format_issues_text, ABAPVersionSelector
from frm_report_generator import ReportGenerator

def main():
    # 获取目标路径
    if len(sys.argv) < 2:
        print("用法: python frm_audit.py <目录或文件路径>")
        return
    
    target_path = Path(sys.argv[1])
    if not target_path.exists():
        print(f"❌ 路径不存在: {target_path}")
        return
    
    # ABAP版本选择（默认最新）
    version_selector = ABAPVersionSelector()
    selected = version_selector.get_latest_version()
    
    if not selected:
        print("❌ 版本选择失败")
        return
    
    abap_version = selected['version']
    abap_product = selected.get('product', '')
    
    print(f"\n✅ 审计版本: {abap_version} ({abap_product})")
    print()
    
    # 创建处理器
    file_handler = FileHandler()
    source_detector = ABAPSourceDetector()
    engine = ABAPAuditEngine(abap_version=abap_version)
    
    # 获取文件列表
    print("=" * 60)
    print("📂 扫描文件")
    print("=" * 60)
    
    abap_files = file_handler.process_file(str(target_path))
    
    if not abap_files:
        print("❌ 未找到ABAP文件")
        return
    
    print(f"\n找到 {len(abap_files)} 个文件：\n")
    for i, f in enumerate(abap_files, 1):
        # 兼容处理：可能是ABAPFile对象或字典
        if hasattr(f, 'file_type'):
            ftype = f.file_type
            fname = Path(f.file_path).name if isinstance(f.file_path, str) else f.file_name
        else:
            ftype = 'unknown'
            fname = str(f)
        print(f"  {i:2d}. [{ftype:15s}] {fname}")
    print()
    
    # 审计每个文件
    all_issues = []
    total_lines = 0
    
    print("=" * 60)
    print("🔍 开始审计")
    print("=" * 60)
    
    for abap_file in abap_files:
        # 兼容处理
        if hasattr(abap_file, 'file_path'):
            fname = Path(abap_file.file_path).name if isinstance(abap_file.file_path, str) else abap_file.file_name
            ftype = abap_file.file_type
        else:
            fname = str(abap_file)
            ftype = 'unknown'
        
        print(f"\n📄 {fname}")
        print(f"   类型: {ftype}")
        
        try:
            report = engine.analyze_file(
                abap_file, 
                abap_version=abap_version,
                abap_product=abap_product
            )
            
            print(f"   行数: {report.total_lines}")
            print(f"   问题: {report.total_issues} 个")
            
            all_issues.extend(report.issues)
            total_lines += report.total_lines
            
        except Exception as e:
            print(f"   ⚠️ 出错: {e}")
    
    # 输出汇总
    print("\n" + "=" * 60)
    print("📊 审计汇总")
    print("=" * 60)
    
    # 统计
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for issue in all_issues:
        sev = issue.severity.lower()
        if sev in severity_counts:
            severity_counts[sev] += 1
    
    print(f"\n📈 代码行数: {total_lines}")
    print(f"📁 审计文件: {len(abap_files)} 个")
    print(f"⚠️  问题总数: {len(all_issues)} 个")
    print()
    print(f"   🔴 严重: {severity_counts['critical']} 个")
    print(f"   🟠 高:   {severity_counts['high']} 个")
    print(f"   🟡 中:   {severity_counts['medium']} 个")
    print(f"   🟢 低:   {severity_counts['low']} 个")
    
    if all_issues:
        print("\n" + format_issues_text(all_issues))

        # 格式选择
        print("\n" + "=" * 60)
        print("💾 报告已生成！请选择保存格式：")
        print("=" * 60)
        print("  1) TXT  - 纯文本格式，适合快速查看")
        print("  2) HTML - 网页格式，样式美观（推荐）")
        print("  3) JSON - JSON格式，适合程序处理")
        print("  4) PDF  - PDF文档，适合打印存档")
        print("  5) ALL  - 保存所有格式\n")

        format_map = {
            '1': ('txt', 'TXT'),
            '2': ('html', 'HTML'),
            '3': ('json', 'JSON'),
            '4': ('pdf', 'PDF'),
            '5': ('all', '所有格式'),
        }

        choice = input("请输入选项 [1-5] (默认2): ").strip()
        if choice == '':
            choice = '2'
        selected_format = format_map.get(choice, ('html', 'HTML'))

        output_dir = Path("D:/My Documents/Workbuddy_Workspace/Outbox/ABAP_Audit_Reports")
        output_dir.mkdir(parents=True, exist_ok=True)

        report_gen = ReportGenerator()
        base_name = f"ABAP_Audit_{target_path.name}_{abap_version.replace('.', '')}"

        # 根据选择的格式生成报告
        formats_to_generate = [selected_format[0]] if selected_format[0] != 'all' else ['txt', 'html', 'json', 'pdf']

        for fmt in formats_to_generate:
            if fmt == 'html':
                html_path = output_dir / f"{base_name}.html"
                report_gen.generate_html_from_issues(
                    all_issues=all_issues,
                    output_path=str(html_path),
                    abap_version=abap_version,
                    abap_product=abap_product,
                    audit_summary={
                        'total_files': len(abap_files),
                        'total_lines': total_lines,
                        'total_issues': len(all_issues),
                        'audit_dir': str(target_path)
                    }
                )
                print(f"   ✅ HTML报告: {html_path}")
            elif fmt == 'txt':
                txt_path = output_dir / f"{base_name}.txt"
                # 生成TXT报告
                from frm_audit_single_file import AuditReport, AuditIssue
                # 构造AuditReport对象用于生成TXT
                issues_for_report = []
                for issue in all_issues:
                    if hasattr(issue, 'severity'):
                        issues_for_report.append(issue)
                # 使用简化的文本输出
                txt_content = []
                txt_content.append("=" * 70)
                txt_content.append("                   ABAP代码审计报告")
                txt_content.append("=" * 70)
                txt_content.append(f"\n审计版本: {abap_version} ({abap_product})")
                txt_content.append(f"审计目录: {target_path}")
                txt_content.append(f"审计文件: {len(abap_files)} 个")
                txt_content.append(f"代码行数: {total_lines}")
                txt_content.append(f"问题总数: {len(all_issues)}")
                txt_content.append(f"\n🔴 严重: {severity_counts['critical']} | 🟠 高: {severity_counts['high']} | 🟡 中: {severity_counts['medium']} | 🟢 低: {severity_counts['low']}")
                txt_content.append("\n" + format_issues_text(all_issues))
                txt_content.append("\n" + "=" * 70)
                txt_content.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                txt_content.append("Author: 吴平 | 联系方式: 13574840501")
                txt_content.append("=" * 70)
                Path(txt_path).write_text('\n'.join(txt_content), encoding='utf-8')
                print(f"   ✅ TXT报告: {txt_path}")
            elif fmt == 'json':
                json_path = output_dir / f"{base_name}.json"
                import json
                json_data = {
                    'abap_version': abap_version,
                    'abap_product': abap_product,
                    'audit_dir': str(target_path),
                    'total_files': len(abap_files),
                    'total_lines': total_lines,
                    'total_issues': len(all_issues),
                    'severity_counts': severity_counts,
                    'issues': [issue.to_dict() if hasattr(issue, 'to_dict') else {
                        'line': issue.line,
                        'severity': issue.severity,
                        'category': issue.category,
                        'rule_id': issue.rule_id,
                        'message': issue.message,
                        'code': issue.code,
                        'suggestion': issue.suggestion
                    } for issue in all_issues],
                    'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'author': '吴平 | 联系方式: 13574840501'
                }
                Path(json_path).write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding='utf-8')
                print(f"   ✅ JSON报告: {json_path}")
            elif fmt == 'pdf':
                # 先生成HTML，再转PDF
                html_path = output_dir / f"{base_name}.html"
                report_gen.generate_html_from_issues(
                    all_issues=all_issues,
                    output_path=str(html_path),
                    abap_version=abap_version,
                    abap_product=abap_product,
                    audit_summary={
                        'total_files': len(abap_files),
                        'total_lines': total_lines,
                        'total_issues': len(all_issues),
                        'audit_dir': str(target_path)
                    }
                )
                pdf_path = output_dir / f"{base_name}.pdf"
                try:
                    from frm_pdf_builder import AuditPDFGenerator
                    pdf_gen = AuditPDFGenerator()
                    pdf_gen.generate_from_html(str(html_path), str(pdf_path))
                    print(f"   ✅ PDF报告: {pdf_path}")
                except Exception as e:
                    print(f"   ⚠️ PDF生成失败: {e}")
                    print(f"   📄 HTML报告已生成: {html_path}")
        
    else:
        print("\n✅ 未检测到问题！代码质量良好。")
    
    print("\n" + "=" * 60)
    print(f"✅ 审计完成！共发现 {len(all_issues)} 个问题")
    print("=" * 60)

if __name__ == "__main__":
    main()
