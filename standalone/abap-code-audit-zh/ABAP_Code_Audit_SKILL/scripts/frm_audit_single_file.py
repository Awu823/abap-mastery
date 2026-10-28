#!/usr/bin/env python3
"""
ABAP Code Audit Engine - 扩展版审计引擎
支持性能审计(必须) + 代码质量(可选)

Author: 吴平
联系方式: 13574840501 | 微信号：wuping800223
Date: 2026-04-20
Version: 2.0.0
"""

import re
import json
import argparse
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime
from enum import Enum

from frm_file_handler import FileHandler, ABAPFile
from frm_source_detector import ABAPSourceDetector, SourceDetectionResult


class Severity(Enum):
    """严重程度枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Category(Enum):
    """审计类别枚举"""
    PERFORMANCE = "performance"
    SECURITY = "security"
    QUALITY = "quality"
    BEST_PRACTICE = "best_practice"


@dataclass
class AuditIssue:
    """审计问题"""
    line: int
    severity: str
    category: str
    rule_id: str
    rule_name: str
    message: str
    code: str
    suggestion: str
    source_line: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AuditReport:
    """审计报告"""
    file_name: str
    file_path: str
    timestamp: str
    total_lines: int
    total_issues: int
    source_type: str = "UNKNOWN"
    source_confidence: float = 0.0
    issues: List[AuditIssue] = field(default_factory=list)
    metrics: Dict = field(default_factory=dict)
    abap_version: str = ""           # 审计使用的ABAP版本
    abap_product: str = ""           # 版本对应产品
    version_diff_notes: List[str] = field(default_factory=list)  # 版本差异说明
    
    @property
    def summary(self) -> Dict:
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for issue in self.issues:
            counts[issue.severity] += 1
        return counts
    
    def to_dict(self) -> Dict:
        return {
            'file_name': self.file_name,
            'file_path': self.file_path,
            'timestamp': self.timestamp,
            'total_lines': self.total_lines,
            'total_issues': self.total_issues,
            'source_type': self.source_type,
            'source_confidence': self.source_confidence,
            'summary': self.summary,
            'issues': [issue.to_dict() for issue in self.issues],
            'metrics': self.metrics,
            'abap_version': self.abap_version,
            'abap_product': self.abap_product,
            'version_diff_notes': self.version_diff_notes
        }


class ABAPVersionSelector:
    """ABAP版本选择器"""
    
    def __init__(self, version_file: str = None):
        if version_file is None:
            version_file = Path(__file__).parent.parent / 'version.json'
        self.version_file = Path(version_file)
        self.versions = self._load_versions()
    
    def _load_versions(self) -> List[Dict]:
        """加载版本列表"""
        if not self.version_file.exists():
            return []
        try:
            with open(self.version_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('abap_versions', [])
        except Exception:
            return []
    
    def get_latest_version(self) -> Optional[Dict]:
        """获取最新支持版本"""
        for v in self.versions:
            if v.get('latest_support') == 'X':
                return v
        # 如果没有标记，返回最新版本
        if self.versions:
            return self.versions[-1]
        return None
    
    def get_sorted_versions(self) -> List[Dict]:
        """获取按版本号排序的版本列表（由新到旧）"""
        def version_key(v):
            ver = v['version']
            # 处理7.60+格式
            if '+' in ver:
                ver = ver.replace('+', '')
            # 移除空格和括号
            ver = re.sub(r'[\s()]', '', ver)
            try:
                # 转为数字用于排序
                parts = ver.split('.')
                return sum(int(p) * (100 ** (2-i)) for i, p in enumerate(parts[:3]))
            except:
                return 0
        
        return sorted(self.versions, key=version_key, reverse=True)
    
    def get_version_info(self, version_str: str) -> Optional[Dict]:
        """根据版本字符串获取版本信息"""
        for v in self.versions:
            if v['version'] == version_str:
                return v
        return None
    
    def get_version_compatibility(self, selected_version: str, latest_version: str) -> Tuple[bool, List[str]]:
        """获取版本兼容性和差异说明
        
        Returns:
            Tuple[is_compatible, diff_notes]
        """
        diff_notes = []
        selected_int = self._parse_version(selected_version)
        latest_int = self._parse_version(latest_version)
        
        if not selected_int or not latest_int:
            return True, []
        
        # 版本差异规则
        version_checks = [
            (750, "ABAP 7.50+: 支持内表行引用（FIELD SYMBOL）优化"),
            (740, "ABAP 7.40+: 支持内联声明 @DATA()/FIELD-SYMBOL等新语法"),
            (730, "ABAP 7.30+: 支持窗口函数、复杂SQL表达式"),
            (720, "ABAP 7.20: 支持新语法糖（CONV、CORRESPONDING等）"),
            (710, "ABAP 7.10+: 支持增强的ABAP Object特性"),
            (702, "ABAP 7.02+: 支持正则表达式内置函数"),
            (701, "ABAP 7.01+: 支持SQL函数"),
        ]
        
        for threshold, note in version_checks:
            if selected_int < threshold <= latest_int:
                diff_notes.append(f"⚠️ 注意: {note}，但目标版本 {selected_version} 不支持此特性")
        
        if selected_int == latest_int:
            return True, []
        
        # 基础兼容性说明
        is_compatible = selected_int <= latest_int
        if not is_compatible:
            diff_notes.insert(0, f"⚠️ 警告: 代码使用的特性需要 {latest_version}，但选择了 {selected_version}")
        
        return is_compatible, diff_notes
    
    def _parse_version(self, version_str: str) -> Optional[Tuple[int, int, int]]:
        """解析版本字符串为数字元组"""
        # 移除+和括号内容
        clean = re.sub(r'[\s()]', '', version_str)
        # 提取数字部分
        nums = re.findall(r'\d+', clean)
        if not nums:
            return None
        try:
            return (int(nums[0]), int(nums[1]) if len(nums) > 1 else 0, int(nums[2]) if len(nums) > 2 else 0)
        except:
            return None
    
    def interactive_select(self) -> Dict:
        """交互式版本选择
        
        Returns:
            选择的版本信息字典
        """
        print("\n" + "=" * 60)
        print("📋 ABAP版本选择")
        print("=" * 60)
        print("\n请选择审计适用的ABAP版本：\n")
        print("  1) 使用最新版本（推荐）\n")
        print("  2) 从列表中选择指定版本\n")
        
        while True:
            choice = input("请输入选项 [1/2] (默认1): ").strip()
            if choice == '' or choice == '1':
                latest = self.get_latest_version()
                if latest:
                    print(f"\n✅ 已选择最新版本: {latest['version']}")
                    print(f"   产品: {latest['product']}")
                    return latest
                print("❌ 未找到最新版本，将使用默认配置")
                return {'version': '7.60+', 'product': 'S/4HANA 2022 及以后'}
            
            elif choice == '2':
                return self._select_from_list()
            else:
                print("❌ 无效选择，请输入 1 或 2")
    
    def _select_from_list(self) -> Dict:
        """从列表中选择版本"""
        sorted_versions = self.get_sorted_versions()
        
        print("\n可用版本列表（由新到旧）：")
        print("-" * 60)
        for i, v in enumerate(sorted_versions, start=1):
            version = v['version']
            product = v['product']
            remark = f" ({v['remarks']})" if v.get('remarks') else ""
            latest_mark = " ⭐ 最新" if v.get('latest_support') == 'X' else ""
            print(f"  {i:2d}) {version:12s} - {product}{remark}{latest_mark}")
        
        print("-" * 60)
        
        while True:
            try:
                choice = input("\n请输入版本编号 (1-{}) 或直接输入版本号 (如750): ".format(len(sorted_versions))).strip()
                
                # 尝试作为数字索引
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(sorted_versions):
                        selected = sorted_versions[idx]
                        print(f"\n✅ 已选择: {selected['version']} - {selected['product']}")
                        return selected
                    else:
                        print(f"❌ 编号超出范围 (1-{len(sorted_versions)})")
                        continue
                
                # 尝试作为版本号
                for v in sorted_versions:
                    if v['version'] == choice or v['version'].replace('.', '') == choice:
                        print(f"\n✅ 已选择: {v['version']} - {v['product']}")
                        return v
                
                print(f"❌ 未找到版本 '{choice}'，请重试")
            except ValueError:
                print("❌ 无效输入，请重试")


class AuditRulesLoader:
    """审计规则加载器"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'audit-rules.json'
        
        self.config_path = Path(config_path)
        self.rules = self._load_rules()
    
    def _load_rules(self) -> Dict:
        if not self.config_path.exists():
            return self._get_default_rules()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except Exception:
            return self._get_default_rules()
    
    def _get_default_rules(self) -> Dict:
        return {
            'performance_rules': {},
            'quality_rules': {},
            'security_rules': {},
            'best_practice_rules': {}
        }
    
    def get_enabled_rules(self, category: str) -> List[Dict]:
        category_map = {
            'performance': 'performance_rules',
            'quality': 'quality_rules',
            'security': 'security_rules',
            'best_practice': 'best_practice_rules'
        }
        
        rule_key = category_map.get(category, '')
        if not rule_key:
            return []
        
        rules = self.rules.get(rule_key, {})
        return [
            {**rule, 'id': rule_id, 'category': category}
            for rule_id, rule in rules.items()
            if rule.get('enabled', True)
        ]
    
    def get_all_enabled_rules(self) -> List[Dict]:
        all_rules = []
        for category in ['performance', 'quality', 'security', 'best_practice']:
            all_rules.extend(self.get_enabled_rules(category))
        return all_rules


class ABAPAuditEngine:
    """ABAP审计引擎"""
    
    def __init__(self, config_path: Optional[str] = None, abap_version: Optional[str] = None):
        self.rules_loader = AuditRulesLoader(config_path)
        self.rules = self.rules_loader.get_all_enabled_rules()
        self._compile_patterns()
        self.source_detector = ABAPSourceDetector()
        self.abap_version = abap_version or "7.60+"
        self._version_int = self._parse_version(self.abap_version)
    
    def _parse_version(self, version_str: str) -> Tuple[int, int, int]:
        """解析版本字符串为数字元组"""
        clean = re.sub(r'[\s()]', '', version_str)
        nums = re.findall(r'\d+', clean)
        if not nums:
            return (7, 60, 0)
        try:
            return (int(nums[0]), int(nums[1]) if len(nums) > 1 else 0, int(nums[2]) if len(nums) > 2 else 0)
        except:
            return (7, 60, 0)
    
    def _is_rule_applicable(self, rule: Dict) -> bool:
        """检查规则是否适用于当前ABAP版本"""
        min_version = rule.get('min_version')
        if not min_version:
            return True
        
        rule_int = self._parse_version(min_version)
        return self._version_int >= rule_int
    
    def _compile_patterns(self):
        for rule in self.rules:
            if 'pattern' in rule:
                try:
                    rule['_compiled'] = re.compile(
                        rule['pattern'],
                        re.MULTILINE | re.IGNORECASE | re.DOTALL
                    )
                except re.error:
                    rule['_compiled'] = None
    
    def analyze_file(self, abap_file: ABAPFile, abap_version: str = None, abap_product: str = "") -> AuditReport:
        source_result = self.source_detector.detect(
            abap_file.content, 
            abap_file.file_name
        )
        
        # 获取版本信息
        version_info = abap_version or self.abap_version
        product_info = abap_product
        
        # 计算版本差异说明
        version_diff_notes = self._get_version_diff_notes()
        
        report = AuditReport(
            file_name=abap_file.file_name,
            file_path=abap_file.file_path,
            timestamp=datetime.now().isoformat(),
            total_lines=len(abap_file.content.split('\n')),
            total_issues=0,
            source_type=source_result.source_type,
            source_confidence=source_result.confidence,
            abap_version=version_info,
            abap_product=product_info,
            version_diff_notes=version_diff_notes
        )
        
        issues = self._analyze_code(abap_file.content, abap_file.file_path)
        issues.extend(self._check_performance_issues(abap_file.content))
        
        report.issues = issues
        report.total_issues = len(issues)
        report.metrics = self._calculate_metrics(abap_file.content)
        
        return report
    
    def _get_version_diff_notes(self) -> List[str]:
        """获取版本差异说明"""
        notes = []
        
        # 版本相关的差异说明
        version_notes = {
            (7, 40): "ABAP 7.40+: 代码使用了NEW操作符、内联声明等新语法",
            (7, 50): "ABAP 7.50+: 代码可使用内表行引用优化内存使用",
            (7, 51): "ABAP 7.51+: 代码可使用窗口函数和高级SQL特性",
            (7, 52): "ABAP 7.52+: 代码可使用更多SQL内置函数",
            (7, 60): "ABAP 7.60+: 完全支持现代ABAP所有特性",
        }
        
        for (ver_int, note) in sorted(version_notes.items()):
            if self._version_int >= ver_int:
                continue  # 新版本包含旧特性
            notes.append(f"⚠️ {note}")
        
        if notes:
            notes.insert(0, f"📌 审计基于 ABAP {self.abap_version} 版本")
        else:
            notes.insert(0, f"✅ 审计基于 ABAP {self.abap_version} 版本，所有新特性均可用")
        
        return notes
    
    def analyze_snippet(self, code: str, name: str = "snippet", 
                        abap_version: str = None, abap_product: str = "") -> AuditReport:
        abap_file = ABAPFile(
            file_name=f"{name}.abap",
            file_path="",
            content=code,
            file_type="snippet"
        )
        return self.analyze_file(abap_file, abap_version, abap_product)
    
    def _analyze_code(self, code: str, file_path: str) -> List[AuditIssue]:
        issues = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, start=1):
            clean_line = line.strip()
            
            if self._is_comment(clean_line):
                continue
            
            for rule in self.rules:
                # 检查规则是否适用于当前版本
                if not self._is_rule_applicable(rule):
                    continue
                
                if not rule.get('_compiled'):
                    continue
                
                try:
                    if rule['_compiled'].search(line):
                        issue = AuditIssue(
                            line=line_num,
                            severity=rule.get('severity', 'medium'),
                            category=rule.get('category', 'quality'),
                            rule_id=rule.get('id', rule.get('name', 'UNKNOWN')),
                            rule_name=rule.get('name', 'UNKNOWN'),
                            message=rule.get('message', ''),
                            code=clean_line[:150],
                            suggestion=rule.get('suggestion', ''),
                            source_line=line
                        )
                        # 如果是版本相关的最佳实践建议，添加版本说明
                        if rule.get('min_version'):
                            issue.suggestion += f" (此规则适用于 ABAP {rule['min_version']}+)"
                        issues.append(issue)
                except re.error:
                    continue
        
        return issues
    
    def _is_comment(self, line: str) -> bool:
        stripped = line.strip()
        return (
            stripped.startswith('*"') or 
            stripped.startswith('*') or 
            stripped.startswith('"')
        )
    
    def _check_performance_issues(self, code: str) -> List[AuditIssue]:
        issues = []
        lines = code.split('\n')
        
        issues.extend(self._check_n_plus_1(lines))
        issues.extend(self._check_sort_in_loop(lines))
        issues.extend(self._check_modify_in_loop(lines))
        
        return issues
    
    def _check_n_plus_1(self, lines: List[str]) -> List[AuditIssue]:
        issues = []
        in_loop = False
        
        for i, line in enumerate(lines, start=1):
            clean_line = line.strip()
            
            if re.match(r'LOOP\s+AT\s+', clean_line, re.IGNORECASE):
                in_loop = True
                continue
            
            if clean_line.upper().startswith('ENDLOOP'):
                in_loop = False
                continue
            
            if in_loop and re.search(r'SELECT\s+', clean_line, re.IGNORECASE):
                issues.append(AuditIssue(
                    line=i,
                    severity="high",
                    category="performance",
                    rule_id="P002",
                    rule_name="N_PLUS_1_QUERY",
                    message="检测到嵌套SELECT查询，存在N+1问题",
                    code=clean_line[:100],
                    suggestion="使用FOR ALL ENTRIES或JOIN代替嵌套查询",
                    source_line=line
                ))
        
        return issues
    
    def _check_sort_in_loop(self, lines: List[str]) -> List[AuditIssue]:
        issues = []
        in_loop = False
        
        for i, line in enumerate(lines, start=1):
            clean_line = line.strip()
            
            if re.match(r'LOOP\s+AT\s+', clean_line, re.IGNORECASE):
                in_loop = True
                continue
            
            if clean_line.upper().startswith('ENDLOOP'):
                in_loop = False
                continue
            
            if in_loop and re.search(r'\bSORT\b', clean_line, re.IGNORECASE):
                issues.append(AuditIssue(
                    line=i,
                    severity="high",
                    category="performance",
                    rule_id="P005",
                    rule_name="SORT_INSIDE_LOOP",
                    message="在循环内进行排序操作",
                    code=clean_line[:100],
                    suggestion="将排序移到循环外部执行",
                    source_line=line
                ))
        
        return issues
    
    def _check_modify_in_loop(self, lines: List[str]) -> List[AuditIssue]:
        issues = []
        in_loop = False
        
        for i, line in enumerate(lines, start=1):
            clean_line = line.strip()
            
            if re.match(r'LOOP\s+AT\s+', clean_line, re.IGNORECASE):
                in_loop = True
                continue
            
            if clean_line.upper().startswith('ENDLOOP'):
                in_loop = False
                continue
            
            if in_loop:
                if re.search(r'\b(?:UPDATE|DELETE|INSERT\s+INTO|MODIFY)\b', 
                            clean_line, re.IGNORECASE):
                    issues.append(AuditIssue(
                        line=i,
                        severity="medium",
                        category="performance",
                        rule_id="P008",
                        rule_name="MODIFY_INSIDE_LOOP",
                        message="在循环内执行数据库修改操作",
                        code=clean_line[:100],
                        suggestion="考虑批量操作代替循环内单条修改",
                        source_line=line
                    ))
                
                if re.search(r'\bCOMMIT\s+WORK\b', clean_line, re.IGNORECASE):
                    issues.append(AuditIssue(
                        line=i,
                        severity="high",
                        category="performance",
                        rule_id="P009",
                        rule_name="COMMIT_WORK_IN_LOOP",
                        message="在循环内执行COMMIT WORK",
                        code=clean_line[:100],
                        suggestion="将COMMIT移到循环外部",
                        source_line=line
                    ))
        
        return issues
    
    def _calculate_metrics(self, code: str) -> Dict:
        lines = code.split('\n')
        code_lines = [l for l in lines if l.strip() and not self._is_comment(l.strip())]
        comment_lines = [l for l in lines if self._is_comment(l.strip())]
        
        complexity = self._calculate_complexity(code)
        
        return {
            'lines_of_code': len(code_lines),
            'lines_of_comments': len(comment_lines),
            'comment_ratio': len(comment_lines) / len(lines) if lines else 0,
            'cyclomatic_complexity': complexity,
            'has_select': 'SELECT' in code.upper(),
            'has_authority_check': 'AUTHORITY-CHECK' in code.upper(),
        }
    
    def _calculate_complexity(self, code: str) -> int:
        complexity = 1
        complexity += len(re.findall(r'\bIF\b', code, re.IGNORECASE))
        complexity += len(re.findall(r'\bWHEN\b', code, re.IGNORECASE))
        complexity += len(re.findall(r'\b(DO|WHILE)\b', code, re.IGNORECASE))
        complexity += len(re.findall(r'\bCATCH\b', code, re.IGNORECASE))
        complexity += len(re.findall(r'\bAND\b|\bOR\b', code, re.IGNORECASE))
        return complexity




def _load_tokens() -> Dict:
    """加载词元配置"""
    token_file = Path(__file__).parent.parent / 'token.json'
    if not token_file.exists():
        return None
    try:
        with open(token_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def format_issues_text(issues: List[AuditIssue]) -> str:
    # 尝试从token.json加载词元
    tokens = _load_tokens()
    
    if not issues:
        if tokens:
            return f"{tokens.get('sections', {}).get('no_issues', '✅ 未检测到问题！代码质量良好。')}"
        return "✅ 未检测到问题！代码质量良好。"
    
    # 从词元获取配置
    if tokens:
        sev_config = tokens.get('severity', {})
        msg_config = tokens.get('messages', {})
        issue_fields = tokens.get('issue_fields', {})
        
        # 获取发现问题的消息模板
        discovered_template = msg_config.get('discovered', '发现 {count} 个问题')
        output = f"🔍 {discovered_template.format(count=len(issues))}\n\n"
        
        severity_order = ['critical', 'high', 'medium', 'low']
        
        for sev in severity_order:
            if sev in [i.severity for i in issues]:
                sev_issues = [i for i in issues if i.severity == sev]
                sev_info = sev_config.get(sev, {})
                sev_emoji = sev_info.get('emoji', '🔴')
                sev_label = sev_info.get('label', sev)
                issue_count = msg_config.get('issue_count', '个')
                
                output += f"\n{sev_emoji} {sev_label} ({len(sev_issues)}{issue_count}):\n"
                output += "-" * 50 + "\n"
                
                for issue in sev_issues:
                    line_label = issue_fields.get('line', '行')
                    rule_prefix = msg_config.get('rule_prefix', '[{rule_id}]').format(rule_id=issue.rule_id)
                    code_label = issue_fields.get('code', '代码')
                    suggestion_label = issue_fields.get('suggestion', '建议')
                    
                    output += f"  📌 {line_label} {issue.line} | {rule_prefix} {issue.message}\n"
                    output += f"     {code_label}: {issue.code}\n"
                    output += f"     {suggestion_label}: {issue.suggestion}\n\n"
        
        return output
    
    # 默认格式（无token.json）
    output = f"🔍 发现 {len(issues)} 个问题:\n\n"
    
    by_severity = {}
    for issue in issues:
        if issue.severity not in by_severity:
            by_severity[issue.severity] = []
        by_severity[issue.severity].append(issue)
    
    severity_order = ['critical', 'high', 'medium', 'low']
    severity_labels = {
        'critical': '🔴 严重',
        'high': '🟠 高',
        'medium': '🟡 中',
        'low': '🟢 低'
    }
    
    for sev in severity_order:
        if sev in by_severity:
            output += f"\n{severity_labels[sev]} ({len(by_severity[sev])}个):\n"
            output += "-" * 50 + "\n"
            
            for issue in by_severity[sev]:
                output += f"  📌 行 {issue.line} | [{issue.rule_id}] {issue.message}\n"
                output += f"     代码: {issue.code}\n"
                output += f"     建议: {issue.suggestion}\n\n"
    
    return output


def main():
    parser = argparse.ArgumentParser(description='ABAP代码审计引擎')
    parser.add_argument('--file', '-f', help='ABAP文件路径')
    parser.add_argument('--snippet', '-s', help='ABAP代码片段')
    parser.add_argument('--output', '-o', help='输出JSON文件路径')
    parser.add_argument('--config', '-c', help='规则配置文件路径')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='输出格式')
    
    args = parser.parse_args()
    
    engine = ABAPAuditEngine(config_path=args.config)
    
    if args.file:
        file_handler = FileHandler()
        abap_files = file_handler.process_file(args.file)
        
        for abap_file in abap_files:
            report = engine.analyze_file(abap_file)
            print(f"\n{'='*60}")
            print(f"文件: {report.file_name}")
            print(f"来源: {report.source_type} (置信度: {report.source_confidence:.0%})")
            print(f"总行数: {report.total_lines} | 问题数: {report.total_issues}")
            print(f"{'='*60}")
            print(format_issues_text(report.issues))
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
    
    elif args.snippet:
        report = engine.analyze_snippet(args.snippet)
        print(f"来源: {report.source_type}")
        print(format_issues_text(report.issues))
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
