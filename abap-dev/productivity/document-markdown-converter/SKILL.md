---
name: document-markdown-converter
version: 1.0
description: Hướng dẫn tiền xử lý (pre-processing) tài liệu FS nhị phân (PDF, DOCX, XLSX, PPTX, HTML, v.v.) bằng công cụ Microsoft MarkItDown thành định dạng Markdown (MD) trước khi phân tích trong các workflow SAP. Sử dụng khi một tài liệu thiết kế FS/spec được cung cấp làm đầu vào cho workflow phân tích (fs-analytic, bug-fix...) — KHÔNG dùng cho các thao tác PDF/Word/Excel tổng quát (tạo, chỉnh sửa, merge file — việc đó thuộc các skill pdf/docx/xlsx chuyên dụng). Triggers: `markitdown`, `convert fs`, `parse FS document`, `tiền xử lý tài liệu FS`, `đọc file FS`.
---

# Document Markdown Converter (MarkItDown Integration)

Guide for pre-processing binary Functional Specification (FS) documents into Markdown format for token-efficient analysis.

## Core Objective
Never attempt to read raw binary files (`.pdf`, `.docx`, `.xlsx`) directly. Always use `markitdown` CLI to convert them to structured Markdown format first, and then analyze the resulting Markdown file.

## Workflow

### 1. Environment Verification
Check if the virtual environment binary exists using a relative path from the workspace root:
```bash
./.venv_markitdown/bin/markitdown --version
```
If the command fails (command not found), create the venv locally and install it (requires Python >= 3.10):
```bash
python3 -m venv .venv_markitdown && ./.venv_markitdown/bin/pip install 'markitdown[all]'
```

### 2. Document Conversion
Locate the input file (usually inside the active project's `projects/<project>/fs_docs/`).
Execute the conversion command and output to the same project's `scratchpads/` directory:
```bash
./.venv_markitdown/bin/markitdown "projects/<project>/fs_docs/[Your_File_Name.ext]" -o "projects/<project>/scratchpads/fs_markdown.md"
```

### 3. Handoff to Analysis
Once `fs_markdown.md` is generated successfully, **stop reading the original document**. Read `projects/<project>/scratchpads/fs_markdown.md` instead (with the Read tool).
The resulting markdown will contain preserved headings, lists, and tables which you can easily parse for Data Model and UI elements extraction.

## Optional: LLM OCR for Images
If the document is known to contain complex images (flowcharts, UI mockups) embedded within it, you can utilize the `markitdown-ocr` plugin if configured, or fallback to the `fs-vision-extractor` skill to handle images separately. For standard text and tables, the base `markitdown` command is perfectly sufficient.
