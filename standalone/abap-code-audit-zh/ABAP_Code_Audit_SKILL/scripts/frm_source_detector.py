#!/usr/bin/env python3
"""
ABAP Source Detector - ABAP来源识别器
识别代码来源于SAP开发对象类型：REPORT/FUNCTION/CLASS/MODULE/FORM

Author: 吴平
联系方式: 13574840501 | 微信号：wuping800223
Date: 2026-04-20
Version: 2.0.0
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ABAPSourceType(Enum):
    """ABAP来源类型"""
    REPORT = "REPORT"           # 可执行程序或模块池
    FUNCTION = "FUNCTION"       # 函数模块
    CLASS_DEF = "CLASS_DEF"     # 类定义
    CLASS_IMP = "CLASS_IMP"     # 类实现
    MODULE_POOL = "MODULE"      # Module Pool或屏幕
    FORM = "FORM"               # 子程序/FORM
    FUNCTION_POOL = "FUNC_POOL" # 函数组
    INTERFACE = "INTERFACE"     # 接口
    UNKNOWN = "UNKNOWN"         # 未知


@dataclass
class SourceDetectionResult:
    """来源检测结果"""
    source_type: str
    confidence: float  # 0.0 - 1.0
    matched_pattern: str
    metadata: Dict
    program_name: Optional[str] = None
    method_name: Optional[str] = None
    function_name: Optional[str] = None
    form_name: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'source_type': self.source_type,
            'confidence': self.confidence,
            'matched_pattern': self.matched_pattern,
            'metadata': self.metadata,
            'program_name': self.program_name,
            'method_name': self.method_name,
            'function_name': self.function_name,
            'form_name': self.form_name
        }


class ABAPSourceDetector:
    """ABAP来源检测器"""
    
    PATTERNS = {
        'REPORT': [
            (r'^REPORT\s+(\w+)', 0.95),
            (r'^PROGRAM\s+(\w+)', 0.95),
            (r'^INCLUDE\s+(\w+)', 0.6),
        ],
        'FUNCTION': [
            (r'^FUNCTION\s+(\w+)', 0.95),
            (r'^ENDFUNCTION', 0.7),
        ],
        'CLASS_DEF': [
            (r'^CLASS\s+(\w+)\s+DEFINITION', 0.95),
            (r'^\s+(PUBLIC\s+SECTION|PRIVATE\s+SECTION|PROTECTED\s+SECTION)', 0.5),
        ],
        'CLASS_IMP': [
            (r'^CLASS\s+(\w+)\s+IMPLEMENTATION', 0.95),
            (r'^\s+METHOD\s+(\w+)', 0.8),
        ],
        'MODULE': [
            (r'^MODULE\s+(\w+)\s+OUTPUT', 0.9),
            (r'^MODULE\s+(\w+)\s+INPUT', 0.9),
            (r'(?:PBO|PAI):?\s*MODULE', 0.7),
        ],
        'FORM': [
            (r'^FORM\s+(\w+)', 0.95),
            (r'^ENDFORM', 0.8),
            (r'PERFORM\s+(\w+)', 0.3),
        ],
        'FUNCTION_POOL': [
            (r'^FUNCTION-POOL\s+(\w+)', 0.95),
        ],
        'INTERFACE': [
            (r'^INTERFACE\s+(\w+)', 0.95),
            (r'^ENDINTERFACE', 0.8),
        ],
    }
    
    KEYWORD_WEIGHTS = {
        'TABLES': 0.1, 'DATA': 0.1, 'CONSTANTS': 0.1,
        'SELECT': 0.15, 'INSERT': 0.15, 'UPDATE': 0.15,
        'DELETE': 0.15, 'MODIFY': 0.15,
        'CALL FUNCTION': 0.1, 'CALL METHOD': 0.1, 'PERFORM': 0.1,
        'SUBMIT': 0.15, 'AUTHORITY-CHECK': 0.2,
        'START-OF-SELECTION': 0.3, 'END-OF-SELECTION': 0.3,
        'AT SELECTION-SCREEN': 0.3, 'INITIALIZATION': 0.3,
        'TOP-OF-PAGE': 0.3, 'END-OF-PAGE': 0.3,
    }
    
    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self):
        self.compiled_patterns = {}
        for source_type, patterns in self.PATTERNS.items():
            self.compiled_patterns[source_type] = [
                (re.compile(pattern, re.MULTILINE | re.IGNORECASE), weight)
                for pattern, weight in patterns
            ]
    
    def detect(self, code: str, file_name: Optional[str] = None) -> SourceDetectionResult:
        """检测代码来源"""
        lines = code.strip().split('\n')
        first_lines = '\n'.join(lines[:20]).strip()
        
        scores = {}
        metadata = {
            'line_count': len(lines),
            'has_comments': self._count_comments(lines),
            'has_select': 'SELECT' in code.upper(),
            'has_authority_check': 'AUTHORITY-CHECK' in code.upper(),
            'has_modify_data': any(k in code.upper() for k in ['INSERT', 'UPDATE', 'DELETE']),
        }
        
        for source_type, compiled_patterns in self.compiled_patterns.items():
            score = 0.0
            matched_pattern = None
            match_info = {}
            
            for pattern, base_weight in compiled_patterns:
                match = pattern.search(first_lines)
                if match:
                    score += base_weight
                    if matched_pattern is None:
                        matched_pattern = pattern.pattern
            
            if score > 0:
                scores[source_type] = (score, matched_pattern, match_info)
        
        code_upper = code.upper()
        for keyword, weight in self.KEYWORD_WEIGHTS.items():
            if keyword.upper() in code_upper:
                for source_type in scores:
                    current_score, pattern, info = scores[source_type]
                    scores[source_type] = (current_score + weight, pattern, info)
        
        if file_name:
            fn_upper = file_name.upper()
            name_metadata = self._detect_from_filename(fn_upper)
            metadata.update(name_metadata)
            
            if 'REPORT' in fn_upper or (fn_upper.startswith('Z') and not any(
                x in fn_upper for x in ['CL_', 'IF_', 'FUGR']
            )):
                scores['REPORT'] = scores.get('REPORT', (0, None, {}))
            
            if 'CL_' in fn_upper or 'CLASS' in fn_upper:
                scores['CLASS_DEF'] = scores.get('CLASS_DEF', (0, None, {}))
                scores['CLASS_IMP'] = scores.get('CLASS_IMP', (0, None, {}))
            
            if 'IF_' in fn_upper or 'INTERFACE' in fn_upper:
                scores['INTERFACE'] = scores.get('INTERFACE', (0, None, {}))
            
            if 'FUGR' in fn_upper or 'FUNCTION' in fn_upper:
                scores['FUNCTION_POOL'] = scores.get('FUNCTION_POOL', (0, None, {}))
        
        special_result = self._detect_special_patterns(code)
        if special_result:
            scores[special_result.source_type] = (
                special_result.confidence,
                special_result.matched_pattern,
                special_result.metadata
            )
            metadata.update(special_result.metadata)
        
        if scores:
            best_type = max(scores, key=lambda x: scores[x][0])
            best_score, best_pattern, best_info = scores[best_type]
            confidence = min(best_score / 2.0, 1.0)
            
            return SourceDetectionResult(
                source_type=best_type,
                confidence=confidence,
                matched_pattern=best_pattern,
                metadata=metadata,
                **self._extract_name_info(best_type, code, best_pattern)
            )
        
        return SourceDetectionResult(
            source_type='UNKNOWN',
            confidence=0.0,
            matched_pattern=None,
            metadata=metadata
        )
    
    def _count_comments(self, lines: List[str]) -> int:
        count = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('*') or stripped.startswith('"') or stripped.startswith('*"'):
                count += 1
        return count
    
    def _detect_from_filename(self, file_name: str) -> Dict:
        result = {'filename_hints': []}
        
        if file_name.startswith('Z') and not any(x in file_name for x in ['CL_', 'IF_', 'FUGR', 'SAPL']):
            result['filename_hints'].append('REPORT')
        if 'CL_' in file_name:
            result['filename_hints'].append('CLASS')
        if 'IF_' in file_name:
            result['filename_hints'].append('INTERFACE')
        if 'FUGR' in file_name or file_name.startswith('SAPL'):
            result['filename_hints'].append('FUNCTION_POOL')
        
        return result
    
    def _detect_special_patterns(self, code: str) -> Optional[SourceDetectionResult]:
        lines = code.strip().split('\n')[:50]
        code_snippet = '\n'.join(lines)
        
        imp_match = re.search(r'CLASS\s+(\w+)\s+IMPLEMENTATION', code_snippet, re.IGNORECASE)
        if imp_match:
            return SourceDetectionResult(
                source_type='CLASS_IMP', confidence=0.95,
                matched_pattern='CLASS IMPLEMENTATION',
                metadata={'class_name': imp_match.group(1)},
                class_name=imp_match.group(1)
            )
        
        method_match = re.search(r'METHOD\s+(\w+)', code_snippet, re.IGNORECASE)
        if method_match:
            return SourceDetectionResult(
                source_type='CLASS_IMP', confidence=0.85,
                matched_pattern='METHOD',
                metadata={'method_name': method_match.group(1)},
                method_name=method_match.group(1)
            )
        
        module_match = re.search(r'MODULE\s+(\w+)\s+(OUTPUT|INPUT)', code_snippet, re.IGNORECASE)
        if module_match:
            return SourceDetectionResult(
                source_type='MODULE', confidence=0.9,
                matched_pattern='MODULE OUTPUT/INPUT',
                metadata={'module_name': module_match.group(1)},
                program_name=module_match.group(1)
            )
        
        func_match = re.search(r'FUNCTION\s+(\w+)', code_snippet, re.IGNORECASE)
        if func_match:
            return SourceDetectionResult(
                source_type='FUNCTION', confidence=0.95,
                matched_pattern='FUNCTION',
                metadata={'function_name': func_match.group(1)},
                function_name=func_match.group(1)
            )
        
        form_match = re.search(r'^FORM\s+(\w+)', code_snippet, re.IGNORECASE | re.MULTILINE)
        if form_match:
            return SourceDetectionResult(
                source_type='FORM', confidence=0.9,
                matched_pattern='FORM',
                metadata={'form_name': form_match.group(1)},
                form_name=form_match.group(1)
            )
        
        return None
    
    def _extract_name_info(self, source_type: str, code: str, pattern: Optional[str]) -> Dict:
        result = {}
        
        if source_type == 'REPORT':
            match = re.search(r'^(?:REPORT|PROGRAM)\s+(\w+)', code, re.MULTILINE | re.IGNORECASE)
            if match:
                result['program_name'] = match.group(1)
        elif source_type in ('CLASS_DEF', 'CLASS_IMP'):
            match = re.search(r'CLASS\s+(\w+)', code, re.IGNORECASE)
            if match:
                result['program_name'] = match.group(1)
        elif source_type == 'FUNCTION':
            match = re.search(r'FUNCTION\s+(\w+)', code, re.IGNORECASE)
            if match:
                result['function_name'] = match.group(1)
        elif source_type == 'FORM':
            match = re.search(r'FORM\s+(\w+)', code, re.IGNORECASE)
            if match:
                result['form_name'] = match.group(1)
        elif source_type == 'MODULE':
            match = re.search(r'MODULE\s+(\w+)', code, re.IGNORECASE)
            if match:
                result['program_name'] = match.group(1)
        
        return result
    
    def detect_batch(self, code_list: List[Tuple[str, Optional[str]]]) -> List[SourceDetectionResult]:
        return [self.detect(code, fname) for code, fname in code_list]
    
    def get_source_description(self, source_type: str) -> str:
        descriptions = {
            'REPORT': '可执行程序或模块池程序',
            'FUNCTION': '函数模块 (Function Module)',
            'CLASS_DEF': '类定义 (Class Definition)',
            'CLASS_IMP': '类实现 (Class Implementation)',
            'MODULE': 'Module Pool或屏幕PAI/PBO模块',
            'FORM': '子程序 (FORM Routine)',
            'FUNCTION_POOL': '函数组 (Function Pool)',
            'INTERFACE': '接口定义 (Interface)',
            'UNKNOWN': '未知来源'
        }
        return descriptions.get(source_type, '未知')


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='ABAP来源检测器')
    parser.add_argument('--file', '-f', help='ABAP文件路径')
    parser.add_argument('--snippet', '-s', help='ABAP代码片段')
    
    args = parser.parse_args()
    detector = ABAPSourceDetector()
    
    if args.file:
        from pathlib import Path
        code = Path(args.file).read_text(encoding='utf-8', errors='ignore')
        result = detector.detect(code, Path(args.file).name)
    elif args.snippet:
        result = detector.detect(args.snippet)
    else:
        parser.print_help()
        return
    
    print(f"来源类型: {result.source_type}")
    print(f"描述: {detector.get_source_description(result.source_type)}")
    print(f"置信度: {result.confidence:.2%}")
    print(f"匹配模式: {result.matched_pattern}")
    print(f"元数据: {result.metadata}")


if __name__ == '__main__':
    main()
