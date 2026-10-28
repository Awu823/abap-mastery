#!/usr/bin/env python3
"""
ABAP File Handler - 文件输入处理器
处理TXT/MD/ZIP/RAR文件及代码片段输入

Author: 吴平
联系方式: 13574840501 | 微信号：wuping800223
Date: 2026-04-20
Version: 2.0.0
"""

import re
import os
import zipfile
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class FileType(Enum):
    """支持的文件类型"""
    TXT = "txt"
    MD = "md"
    ZIP = "zip"
    RAR = "rar"
    SNIPPET = "snippet"
    UNKNOWN = "unknown"


@dataclass
class ABAPFile:
    """ABAP文件对象"""
    file_name: str
    file_path: str
    content: str
    file_type: str
    source_type: str = "UNKNOWN"
    size: int = 0
    
    def __post_init__(self):
        if self.size == 0:
            self.size = len(self.content)


class FileHandler:
    """文件输入处理器"""
    
    ABAP_EXTENSIONS = {'.abap', '.prog', '.txt', '.source', '.代码'}
    
    RAR_AVAILABLE = False
    try:
        import rarfile
        RAR_AVAILABLE = True
    except ImportError:
        pass
    
    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.temp_dir = Path(self.temp_dir)
        self.extracted_files: List[Path] = []
    
    def detect_file_type(self, file_path: str) -> FileType:
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix == '.txt':
            return FileType.TXT
        elif suffix == '.md':
            return FileType.MD
        elif suffix == '.zip':
            return FileType.ZIP
        elif suffix in ('.rar', '.cbr'):
            return FileType.RAR
        else:
            return FileType.UNKNOWN
    
    def is_abap_file(self, file_name: str) -> bool:
        path = Path(file_name)
        suffix = path.suffix.lower()
        return suffix in self.ABAP_EXTENSIONS
    
    def process_file(self, file_path: str) -> List[ABAPFile]:
        """处理文件或目录，支持TXT/MD/ZIP/RAR/目录"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"路径不存在: {file_path}")
        
        # 支持目录输入
        if path.is_dir():
            return self._process_directory(path)
        
        file_type = self.detect_file_type(file_path)
        
        if file_type == FileType.TXT:
            return self._process_txt(path)
        elif file_type == FileType.MD:
            return self._process_md(path)
        elif file_type == FileType.ZIP:
            return self._process_zip(path)
        elif file_type == FileType.RAR:
            return self._process_rar(path)
        else:
            raise ValueError(f"不支持的文件类型: {file_path}")
    
    def _process_directory(self, dir_path: Path) -> List[ABAPFile]:
        """处理目录，递归扫描所有ABAP文件"""
        abap_files = []
        scanned_dirs = set()
        
        # 递归扫描所有文件
        for file_path in dir_path.rglob('*'):
            if file_path.is_file() and self.is_abap_file(file_path.name):
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    file_type_str = self._detect_abap_type(file_path, content)
                    abap_files.append(ABAPFile(
                        file_name=file_path.name,
                        file_path=str(file_path),
                        content=content.strip(),
                        file_type=file_type_str
                    ))
                except Exception:
                    continue
        
        # 按依赖顺序排序
        abap_files = self._sort_by_dependency(abap_files, dir_path.name)
        
        return abap_files
    
    def _detect_abap_type(self, file_path: Path, content: str) -> str:
        """识别ABAP文件类型"""
        first_line = content.strip().split('\n')[0] if content.strip() else ""
        file_name = file_path.stem.lower()
        
        # REPORT 优先
        if 'REPORT' in first_line.upper():
            return 'REPORT'
        # INCLUDE 其次
        if 'INCLUDE' in first_line.upper():
            return 'INCLUDE'
        # 函数模块
        if 'FUNCTION' in first_line.upper() or file_name.startswith('zfm_'):
            return 'FUNCTION'
        # 全局INCLUDE
        if file_name.startswith('global-'):
            return 'GLOBAL_INCLUDE'
        # 子模块
        if '_in_' in file_name:
            return 'SUBMODULE'
        # 其他
        return 'UNKNOWN'
    
    def _sort_by_dependency(self, files: List[ABAPFile], main_name: str) -> List[ABAPFile]:
        """按依赖顺序排序：REPORT > INCLUDE > FUNCTION > GLOBAL_INCLUDE > SUBMODULE"""
        def sort_key(f: ABAPFile) -> tuple:
            type_order = {
                'REPORT': 0,
                'INCLUDE': 1,
                'FUNCTION': 2,
                'GLOBAL_INCLUDE': 3,
                'SUBMODULE': 4,
                'UNKNOWN': 5
            }
            order = type_order.get(f.file_type, 5)
            # 同类型按文件名排序
            return (order, f.file_name)
        
        return sorted(files, key=sort_key)
    
    def process_snippet(self, code: str, source_name: str = "snippet") -> List[ABAPFile]:
        """处理代码片段"""
        abap_files = []
        blocks = self._split_code_blocks(code)
        
        for i, block in enumerate(blocks):
            if block.strip():
                name = f"{source_name}_{i+1}" if len(blocks) > 1 else source_name
                abap_files.append(ABAPFile(
                    file_name=f"{name}.abap",
                    file_path="",
                    content=block.strip(),
                    file_type="snippet"
                ))
        
        return abap_files
    
    def _process_txt(self, path: Path) -> List[ABAPFile]:
        content = path.read_text(encoding='utf-8', errors='ignore')
        return [ABAPFile(
            file_name=path.name,
            file_path=str(path),
            content=content.strip(),
            file_type="txt"
        )]
    
    def _process_md(self, path: Path) -> List[ABAPFile]:
        content = path.read_text(encoding='utf-8', errors='ignore')
        abap_files = []
        blocks = self._extract_md_code_blocks(content)
        
        for i, (block_content, block_info) in enumerate(blocks):
            file_name = self._extract_filename_from_context(content, block_info, path.stem, i)
            abap_files.append(ABAPFile(
                file_name=file_name,
                file_path=str(path),
                content=block_content.strip(),
                file_type="md"
            ))
        
        if not abap_files:
            abap_files.append(ABAPFile(
                file_name=path.stem + ".abap",
                file_path=str(path),
                content=content.strip(),
                file_type="md"
            ))
        
        return abap_files
    
    def _extract_md_code_blocks(self, content: str) -> List[Tuple[str, Dict]]:
        """提取Markdown中的ABAP代码块"""
        blocks = []
        pattern = r'```(?:abap|ABAP|prog)?\s*\n?(.*?)```'
        matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            code_content = match.group(1)
            start_pos = match.start()
            context_start = max(0, start_pos - 200)
            context = content[context_start:start_pos]
            
            blocks.append((code_content, {
                'start': start_pos,
                'context': context
            }))
        
        return blocks
    
    def _extract_filename_from_context(self, content: str, block_info: Dict, 
                                       default_name: str, index: int) -> str:
        """从上下文提取文件名"""
        context = block_info.get('context', '')
        patterns = [
            r'[-_]?([A-Z0-9_]+\.(?:abap|prog|txt))',
            r'文件名[:：]?\s*([^\s\n]+)',
            r'name[:：]?\s*([^\s\n]+)',
            r'([YZ]CL_[A-Z0-9_]+)',
            r'(Z[A-Z0-9_]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                filename = match.group(1)
                if '.' not in filename:
                    filename += '.abap'
                return filename
        
        return f"{default_name}_{index+1}.abap"
    
    def _process_zip(self, path: Path) -> List[ABAPFile]:
        """处理ZIP压缩包"""
        abap_files = []
        extract_dir = self.temp_dir / f"abap_zip_{path.stem}"
        
        try:
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                self.extracted_files.append(extract_dir)
                
                for file_path in extract_dir.rglob('*'):
                    if file_path.is_file() and self.is_abap_file(file_path.name):
                        try:
                            content = file_path.read_text(encoding='utf-8', errors='ignore')
                            abap_files.append(ABAPFile(
                                file_name=file_path.name,
                                file_path=str(file_path),
                                content=content.strip(),
                                file_type="zip"
                            ))
                        except Exception:
                            continue
                            
        except zipfile.BadZipFile:
            raise ValueError(f"无效的ZIP文件: {path}")
        
        return abap_files
    
    def _process_rar(self, path: Path) -> List[ABAPFile]:
        """处理RAR压缩包"""
        if not self.RAR_AVAILABLE:
            raise ImportError("处理RAR文件需要安装 rarfile 库: pip install rarfile")
        
        import rarfile
        
        abap_files = []
        extract_dir = self.temp_dir / f"abap_rar_{path.stem}"
        
        try:
            with rarfile.RarFile(path, 'r') as rar_ref:
                rar_ref.extractall(extract_dir)
                self.extracted_files.append(extract_dir)
                
                for file_path in extract_dir.rglob('*'):
                    if file_path.is_file() and self.is_abap_file(file_path.name):
                        try:
                            content = file_path.read_text(encoding='utf-8', errors='ignore')
                            abap_files.append(ABAPFile(
                                file_name=file_path.name,
                                file_path=str(file_path),
                                content=content.strip(),
                                file_type="rar"
                            ))
                        except Exception:
                            continue
                            
        except rarfile.BadRarFile:
            raise ValueError(f"无效的RAR文件: {path}")
        
        return abap_files
    
    def _split_code_blocks(self, code: str) -> List[str]:
        """分割代码块"""
        blocks = []
        pattern = r'(?=^(?:REPORT|PROGRAM|FUNCTION-POOL|CLASS\s+\w+\s+DEFINITION)\b)'
        parts = re.split(pattern, code, flags=re.MULTILINE | re.IGNORECASE)
        
        for part in parts:
            stripped = part.strip()
            if stripped:
                blocks.append(stripped)
        
        if len(blocks) == 1:
            separator_pattern = r'\n(?:={3,}|---{3,})\n'
            parts = re.split(separator_pattern, code)
            blocks = [p.strip() for p in parts if p.strip()]
        
        if len(blocks) == 1 and not blocks[0].strip():
            blocks = [code.strip()]
        
        return blocks if blocks else [code.strip()]
    
    def cleanup(self):
        """清理临时文件"""
        for dir_path in self.extracted_files:
            try:
                if dir_path.exists():
                    import shutil
                    shutil.rmtree(dir_path)
            except Exception:
                pass
        self.extracted_files.clear()
    
    def get_supported_formats(self) -> List[str]:
        formats = ['.txt', '.md', '.zip']
        if self.RAR_AVAILABLE:
            formats.append('.rar')
        return formats


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='ABAP文件处理器')
    parser.add_argument('--file', '-f', help='文件路径')
    parser.add_argument('--snippet', '-s', help='代码片段')
    parser.add_argument('--output-dir', '-o', help='输出目录')
    
    args = parser.parse_args()
    handler = FileHandler()
    
    try:
        if args.file:
            files = handler.process_file(args.file)
            print(f"处理完成，共 {len(files)} 个ABAP文件:")
            for f in files:
                print(f"  - {f.file_name} ({len(f.content)} 字符)")
        
        elif args.snippet:
            files = handler.process_snippet(args.snippet)
            print(f"处理完成，共 {len(files)} 个代码块:")
            for i, f in enumerate(files):
                print(f"  - Block {i+1}: ({len(f.content)} 字符)")
        
        else:
            parser.print_help()
            
    finally:
        handler.cleanup()


if __name__ == '__main__':
    main()
