#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABAP Code Audit Tool - Main Entry Point
ABAP代码审计工具 - 主入口

Author: 吴平
联系方式: 13574840501 | 微信号：wuping800223
Date: 2026-04-20
Version: 2.1.0 (支持交互式版本选择和报告格式选择)
"""

import sys
import os

# Windows UTF-8 模式
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from pathlib import Path
from datetime import datetime
import json

# 导入各模块
from frm_file_handler import FileHandler, ABAPFile
from frm_source_detector import ABAPSourceDetector
from frm_audit_single_file import ABAPAuditEngine, AuditReport, format_issues_text, ABAPVersionSelector
from frm_report_generator import ReportGenerator
from frm_pdf_builder import AuditPDFGenerator


class ABAPAuditTool:
    """ABAP审计工具主类"""
    
    def __init__(self, config_dir: str = None):
        """初始化审计工具
        
        Args:
            config_dir: 配置目录
        """
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(script_dir), 'config')
        
        self.config_dir = Path(config_dir)
        self.file_handler = FileHandler()
        self.source_detector = ABAPSourceDetector()
        self.report_generator = ReportGenerator()
        self.pdf_generator = AuditPDFGenerator(silent=True)
        self.version_selector = ABAPVersionSelector()
        
        # 当前审计版本
        self.current_version = None
        self.current_product = ""
        
        # 输出目录
        # 默认输出目录改为用户主目录下的 ABAP_Audit_Reports
        default_output_dir = Path.home() / "ABAP_Audit_Reports"
        self.output_dir = default_output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def select_version_interactive(self, choice: str = None) -> bool:
        """交互式选择ABAP版本
        
        Args:
            choice: 可选，指定选择（用于命令行参数自动化）
                   - None: 显示交互式菜单等待用户输入
                   - '1' 或 'latest': 自动选择最新版本
                   - '2': 显示版本列表（仍需用户输入具体版本）
                   - 具体版本号（如 '750', '7.60+'）: 直接设置该版本
        
        Returns:
            bool: 是否选择了版本
        """
        # 命令行参数自动化模式
        if choice is not None and choice not in ('1', '2'):
            # 尝试作为具体版本号处理
            all_versions = [v['version'] for v in self.version_selector.get_sorted_versions()]
            if choice.lower() == 'latest':
                selected = self.version_selector.get_latest_version()
                if selected:
                    self.current_version = selected['version']
                    self.current_product = selected.get('product', '')
                    print(f"\n✅ 自动选择最新版本: {self.current_version} ({self.current_product})")
                    return True
            elif choice in all_versions:
                self.current_version = choice
                info = self.version_selector.get_version_info(choice)
                self.current_product = info.get('product', '') if info else ''
                print(f"\n✅ 已指定版本: {self.current_version} ({self.current_product})")
                return True
            else:
                print(f"\n⚠️ 未知版本 '{choice}'，将使用最新版本")
            
            # 回退到最新版本
            selected = self.version_selector.get_latest_version()
            if selected:
                self.current_version = selected['version']
                self.current_product = selected.get('product', '')
                print(f"✅ 已选择: {self.current_version} ({self.current_product})")
                return True
            return False
        
        # 交互式模式
        print("\n" + "=" * 60)
        print("📋 ABAP版本选择")
        print("=" * 60)
        print("\n请选择审计适用的ABAP版本：")
        print("  1. 使用最新版本（推荐）")
        print("  2. 从列表中选择指定版本\n")
        
        default_choice = '1'
        user_input = input(f"请输入选项 [1/2] (默认{default_choice}): ").strip()
        
        if user_input == '':
            user_input = default_choice
        
        if user_input == '1':
            # 自动选择最新版本
            selected = self.version_selector.get_latest_version()
            if selected:
                self.current_version = selected['version']
                self.current_product = selected.get('product', '')
                print(f"\n✅ 已选择: {self.current_version} ({self.current_product})")
                return True
        elif user_input == '2':
            # 显示版本列表
            return self._select_version_from_list()
        else:
            print("无效选择，默认使用最新版本")
            selected = self.version_selector.get_latest_version()
            if selected:
                self.current_version = selected['version']
                self.current_product = selected.get('product', '')
                print(f"\n✅ 已选择: {self.current_version} ({self.current_product})")
                return True
        return False
    
    def _select_version_from_list(self) -> bool:
        """从列表中选择版本（需要用户再次输入具体版本）"""
        versions = self.version_selector.get_all_versions()
        
        print("\n可用版本列表（由新到旧）：")
        print("-" * 60)
        
        version_map = {}
        for i, v in enumerate(versions, 1):
            mark = " ⭐ 最新" if v.get('is_latest') else ""
            print(f"  {i}. {v['version']:<10} - {v.get('product', '')}{mark}")
            version_map[str(i)] = v['version']
        print("-" * 60)
        
        while True:
            choice = input("请输入版本编号或直接输入版本号: ").strip()
            
            if choice in version_map:
                self.current_version = version_map[choice]
                for v in versions:
                    if v['version'] == self.current_version:
                        self.current_product = v.get('product', '')
                        break
                print(f"\n✅ 已选择: {self.current_version} ({self.current_product})")
                return True
            elif choice in [v['version'] for v in versions]:
                self.current_version = choice
                for v in versions:
                    if v['version'] == choice:
                        self.current_product = v.get('product', '')
                        break
                print(f"\n✅ 已选择: {self.current_version} ({self.current_product})")
                return True
            else:
                print("⚠️ 无效输入，请重新选择")
    
    def _install_pdf_library(self) -> bool:
        """安装PDF生成库"""
        print("\n📦 正在安装 PDF 生成库 (reportlab)...")
        try:
            import subprocess
            result = subprocess.run(['pip', 'install', 'reportlab'], 
                                   capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                print("✅ reportlab 安装成功！")
                return True
            else:
                print(f"⚠️ 安装失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"⚠️ 安装出错: {e}")
            return False
    
    def _check_pdf_available(self) -> bool:
        """检查PDF生成库是否可用"""
        try:
            import reportlab
            return True
        except ImportError:
            return False
    
    def prompt_save_format(self, base_name: str, interactive: bool = True,
                           choice: str = None) -> str:
        """提示用户选择保存格式
        
        Args:
            base_name: 文件基础名
            interactive: 是否交互式选择
            choice: 可选，指定选择（用于命令行参数自动化）
                   - None: 显示交互式菜单等待用户输入
                   - '1': TXT格式
                   - '2', 'html': HTML格式
                   - '3', 'json': JSON格式
                   - '4', 'pdf': PDF格式
                   - '5', 'all': 所有格式
            
        Returns:
            str: 选择的格式 ['text', 'html', 'json', 'pdf', 'all']
        """
        format_map = {
            '1': ('text', 'TXT'),
            '2': ('html', 'HTML'),
            '3': ('json', 'JSON'),
            '4': ('pdf', 'PDF'),
            '5': ('all', '所有格式'),
        }
        default_choice = '2'
        
        # 命令行参数自动化模式
        if choice is not None:
            # 转换格式名称为数字选项
            name_to_num = {'text': '1', 'html': '2', 'json': '3', 'pdf': '4', 'all': '5'}
            if choice.lower() in name_to_num:
                choice = name_to_num[choice.lower()]
            
            if choice in format_map:
                selected_fmt, fmt_name = format_map[choice]
                print(f"\n💾 已选择格式: {fmt_name}")
                
                # PDF检查
                if selected_fmt in ('pdf', 'all'):
                    if not self._check_pdf_available():
                        if not self._install_pdf_library():
                            print("⚠️ PDF库安装失败，降级为HTML格式")
                            return 'html'
                return selected_fmt
            else:
                print(f"⚠️ 无效格式 '{choice}'，使用默认HTML")
                return 'html'
        
        # 交互式模式
        print("\n" + "=" * 60)
        print("💾 报告已生成！请选择保存格式：")
        print("=" * 60)
        print("  1. TXT  - 纯文本格式，适合快速查看")
        print("  2. HTML - 网页格式，样式美观（推荐）")
        print("  3. JSON - JSON格式，适合程序处理")
        print("  4. PDF  - PDF文档，适合打印存档")
        print("  5. ALL  - 保存所有格式\n")
        
        try:
            while True:
                user_input = input(f"请输入选项 [1-5] (默认{default_choice}): ").strip()
                
                if user_input == '':
                    user_input = default_choice
                
                if user_input not in format_map:
                    print("❌ 无效选择，请输入 1-5")
                    continue
                
                selected_fmt, _ = format_map[user_input]
                
                # 如果选择了PDF或ALL，先检查/安装库
                if selected_fmt in ('pdf', 'all'):
                    if not self._check_pdf_available():
                        if not self._install_pdf_library():
                            print("⚠️ PDF库安装失败，已移除PDF相关选项")
                            del format_map['4']
                            del format_map['5']
                            if user_input not in format_map:
                                print("📋 请重新选择其他格式")
                                continue
                
                return selected_fmt
                
        except (EOFError, IOError):
            print("📋 自动选择: HTML（推荐）")
            return 'html'
    
    def audit_file(self, file_path: str, output_formats: list = None, 
                   interactive: bool = True) -> AuditReport:
        """审计文件或目录
        
        Args:
            file_path: 文件或目录路径
            output_formats: 输出格式列表 ['text', 'html', 'json', 'pdf']
            interactive: 是否交互式选择
            
        Returns:
            AuditReport: 审计报告（目录模式下合并所有文件的报告）
        """
        from pathlib import Path
        
        # 交互式选择版本
        if interactive and self.current_version is None:
            self.select_version_interactive()
        
        # 创建审计引擎（传入版本）
        audit_engine = ABAPAuditEngine(
            str(self.config_dir / 'audit-rules.json'),
            abap_version=self.current_version
        )
        
        # 处理文件/目录
        abap_files = self.file_handler.process_file(file_path)
        
        if not abap_files:
            raise ValueError(f"未找到ABAP文件: {file_path}")
        
        # 判断是否为目录（多个文件）
        is_directory = len(abap_files) > 1 or Path(file_path).is_dir()
        
        if is_directory:
            # 目录模式：审计所有文件并合并报告
            all_issues = []
            total_lines = 0
            
            for abap_file in abap_files:
                try:
                    report = audit_engine.analyze_file(
                        abap_file, 
                        self.current_version, 
                        self.current_product
                    )
                    all_issues.extend(report.issues)
                    total_lines += report.total_lines
                except Exception as e:
                    print(f"  ⚠️ 审计 {abap_file.file_name} 出错: {e}")
            
            # 创建合并报告
            merged_report = AuditReport(
                file_name=Path(file_path).name,
                file_path=str(Path(file_path).resolve()),
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                total_lines=total_lines,
                total_issues=len(all_issues),
                source_type="DIRECTORY",
                abap_version=self.current_version,
                abap_product=self.current_product,
                issues=all_issues
            )
            return merged_report
        else:
            # 单文件模式
            abap_file = abap_files[0]
            report = audit_engine.analyze_file(
                abap_file, 
                self.current_version, 
                self.current_product
            )
            return report
    
    def save_report_interactive(self, report: AuditReport, interactive: bool = True,
                                choice: str = None) -> list:
        """交互式保存报告
        
        Args:
            report: 审计报告
            interactive: 是否交互式选择
            choice: 可选，指定格式选择（用于命令行参数自动化）
            
        Returns:
            list: 生成的报告文件路径
        """
        base_name = Path(report.file_name).stem
        output_formats = []
        
        # 提示用户选择格式
        fmt = self.prompt_save_format(base_name, interactive=interactive, choice=choice)
        
        if fmt == 'all':
            output_formats = ['text', 'html', 'json', 'pdf']
        else:
            output_formats = [fmt]
        
        # 生成报告
        generated_files = []
        for f in output_formats:
            if f == 'text':
                txt_path = self.output_dir / f"{base_name}_report.txt"
                self.report_generator.generate_text(report, str(txt_path))
                generated_files.append(str(txt_path))
                print(f"  ✅ 已保存: {txt_path}")
            elif f == 'html':
                html_path = self.output_dir / f"{base_name}_report.html"
                self.report_generator.generate_html(report, str(html_path))
                generated_files.append(str(html_path))
                print(f"  ✅ 已保存: {html_path}")
            elif f == 'json':
                json_path = self.output_dir / f"{base_name}_report.json"
                self.report_generator.generate_json(report, str(json_path))
                generated_files.append(str(json_path))
                print(f"  ✅ 已保存: {json_path}")
            elif f == 'pdf':
                # 先生成HTML，再转PDF
                html_path = self.output_dir / f"{base_name}_report.html"
                self.report_generator.generate_html(report, str(html_path))
                pdf_path = self.output_dir / f"{base_name}_report.pdf"
                self.pdf_generator.generate_from_html(str(html_path), str(pdf_path))
                generated_files.append(str(pdf_path))
                print(f"  ✅ 已保存: {pdf_path}")
        
        return generated_files
    
    def audit_snippet(self, code: str, name: str = "snippet", 
                      output_formats: list = None,
                      interactive: bool = True) -> AuditReport:
        """审计代码片段
        
        Args:
            code: ABAP代码片段
            name: 名称
            output_formats: 输出格式列表
            interactive: 是否交互式选择
            
        Returns:
            AuditReport: 审计报告
        """
        # 交互式选择版本
        if interactive and self.current_version is None:
            self.select_version_interactive()
        
        # 创建审计引擎
        audit_engine = ABAPAuditEngine(
            str(self.config_dir / 'audit-rules.json'),
            abap_version=self.current_version
        )
        
        # 审计
        report = audit_engine.analyze_snippet(
            code, name, 
            self.current_version, 
            self.current_product
        )
        
        return report
    
    def get_output_files(self) -> dict:
        """获取输出文件列表
        
        Returns:
            dict: 各格式文件路径
        """
        files = {}
        for f in self.output_dir.glob('*_report.*'):
            ext = f.suffix[1:]
            if ext not in files:
                files[ext] = []
            files[ext].append(str(f))
        return files


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='ABAP代码审计工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 交互式审计文件（推荐）
  python frm_main.py --file test.abap
  
  # 审计文件并指定格式
  python frm_main.py --file test.abap --output html
  
  # 审计代码片段
  python frm_main.py --snippet "SELECT * FROM mara."
  
  # 审计ZIP包
  python frm_main.py --file archive.zip --output all
  
  # 指定ABAP版本
  python frm_main.py --file test.abap --version 740
  
  # 非交互模式（命令行参数指定所有选项）
  python frm_main.py --file test.abap --output html --version 750 --no-interactive
        """
    )
    
    parser.add_argument('--file', '-f', help='ABAP文件路径')
    parser.add_argument('--snippet', '-s', help='ABAP代码片段')
    parser.add_argument('--name', '-n', default='snippet', help='代码片段名称')
    parser.add_argument('--output', '-o', choices=['text', 'html', 'json', 'pdf', 'all'], 
                        help='输出格式（不指定则交互式选择）')
    parser.add_argument('--format', choices=['mb', 'text', 'json'], default='mb',
                        help='显示格式')
    parser.add_argument('--output-dir', help='输出目录')
    parser.add_argument('--version', '-v', help='指定ABAP版本（如740、750、7.60+）')
    # parser.add_argument('--no-interactive', action='store_true', 
    #                     help='非交互模式，不提示用户输入')
    
    args = parser.parse_args()
    
    if not args.file and not args.snippet:
        parser.print_help()
        print("\n" + "=" * 60)
        print("💡 提示: 运行不带参数的版本选择测试：")
        print("   python frm_main.py --test-version")
        print("=" * 60)
        return
    
    # 创建工具实例
    tool = ABAPAuditTool()
    
    if args.output_dir:
        tool.output_dir = Path(args.output_dir)
        tool.output_dir.mkdir(parents=True, exist_ok=True)
    
    # 命令行版本参数处理
    if args.version:
        # 使用参数化版本选择（支持 latest/版本号）
        tool.select_version_interactive(args.version)
    else:
        # 无参数，显示交互式菜单
        tool.select_version_interactive()
    
    try:
        # 执行审计（始终交互模式）
        if args.file:
            report = tool.audit_file(args.file, interactive=True)
        elif args.snippet:
            report = tool.audit_snippet(args.snippet, args.name, interactive=True)
        
        # 显示审计信息
        print("\n" + "=" * 60)
        print("📊 审计完成！")
        print("=" * 60)
        print(f"   目标版本: {report.abap_version}")
        if report.abap_product:
            print(f"   对应产品: {report.abap_product}")
        print(f"   问题总数: {report.total_issues}")
        print(f"   严重: {report.summary['critical']} | 高: {report.summary['high']} | 中: {report.summary['medium']} | 低: {report.summary['low']}")
        
        # 显示问题摘要
        print("\n" + "-" * 60)
        print(format_issues_text(report.issues))
        
        # 保存报告（传递命令行格式参数）
        files = tool.save_report_interactive(report, interactive=True, choice=args.output)
        if files:
            print("\n✅ 报告已保存到:")
            for f in files:
                print(f"   📄 {f}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        tool.file_handler.cleanup()


if __name__ == '__main__':
    main()
