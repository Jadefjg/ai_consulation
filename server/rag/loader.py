"""文档加载器 - 支持txt/docx/pdf/markdown/ppt/pptx/csv/xls/xlsx/json/xml/html/css/js/sql/other"""
import os
from pathlib import Path
import json
import csv
from typing import Optional


def load_document(file_path: str) -> str:
    """
    加载并解析文档内容
    :param file_path: 文件绝对路径
    :return: 提取后的文本内容
    """
    path_obj = Path(file_path)
    # 前置校验
    if not path_obj.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    if not path_obj.is_file():
        raise IsADirectoryError(f"路径不是文件: {file_path}")

    ext = path_obj.suffix.lower()

    try:
        if ext in (".txt", ".md", ".markdown", ".css", ".js", ".sql"):
            return _load_text(file_path)
        elif ext == ".pdf":
            return _load_pdf(file_path)
        elif ext == ".docx":
            return _load_docx(file_path)
        elif ext == ".doc":
            return _load_doc(file_path)
        elif ext in (".pptx", ".ppt"):
            return _load_pptx(file_path)
        elif ext == ".csv":
            return _load_csv(file_path)
        elif ext in (".xls", ".xlsx"):
            return _load_excel(file_path)
        elif ext == ".json":
            return _load_json(file_path)
        elif ext in (".html", ".htm", ".xml"):
            return _load_html_xml(file_path)
        else:
            # other 兜底：尝试当做文本读取
            return _load_text(file_path)
    except Exception as e:
        raise RuntimeError(f"解析文件[{file_path}]失败:{str(e)}") from e


def _load_text(file_path: str) -> str:
    """加载纯文本/markdown/css/js/sql等文本类文件，多编码尝试"""
    for encoding in ("utf-8", "gbk", "gb2312", "latin-1"):
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            continue
    raise ValueError(f"无法解码文件: {file_path}, 尝试编码: utf‑8/gbk/gb2312/latin‑1")


def _load_pdf(file_path: str) -> str:
    """加载PDF文件"""
    from pypdf import PdfReader
    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            pages.append(text.strip())
    return "\n\n".join(pages)


def _load_docx(file_path: str) -> str:
    """加载docx文档"""
    from docx import Document
    doc = Document(file_path)
    paragraph_texts = [p.text for p in doc.paragraphs if p.text.strip()]
    # 同时读取表格内容
    for table in doc.tables:
        for row in table.rows:
            row_text = "\t".join(cell.text for cell in row.cells)
            paragraph_texts.append(row_text)
    return "\n".join(paragraph_texts)


def _load_doc(file_path: str) -> str:
    """
    旧版 .doc二进制文件
    注意：python没有纯库完美解析doc，Windows可调用antiword，mac/linux需要安装antiword
    无antiword环境下返回提示文本
    """
    import subprocess
    try:
        result = subprocess.run(
            ["antiword", file_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    raise RuntimeError("不支持直接解析 .doc，请转为docx；本机需要安装antiword工具")


def _load_pptx(file_path: str) -> str:
    """读取PPTX文本；.ppt二进制旧格式无法纯python解析"""
    ext = Path(file_path).suffix.lower()
    if ext == ".ppt":
        raise RuntimeError("旧版二进制 .ppt不支持，请另存为 .pptx")

    from pptx import Presentation
    prs = Presentation(file_path)
    text_list = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                text_list.append(shape.text.strip())
    return "\n".join(text_list)


def _load_csv(file_path: str) -> str:
    """读取csv，转为可读文本"""
    rows_out = []
    for encoding in ("utf-8", "gbk", "utf‑8‑sig"):
        try:
            with open(file_path, "r", encoding=encoding, newline="") as f:
                reader = csv.reader(f)
                for row in reader:
                    rows_out.append("\t".join(row))
            return "\n".join(rows_out)
        except UnicodeDecodeError:
            continue
    raise ValueError("csv解码失败")


def _load_excel(file_path: str) -> str:
    """读取 xls / xlsx，提取所有sheet文本"""
    ext = Path(file_path).suffix.lower()
    text_blocks = []
    if ext == ".xlsx":
        from openpyxl import load_workbook
        wb = load_workbook(file_path, read_only=True, data_only=True)
    else:
        import xlrd
        wb = xlrd.open_workbook(file_path)

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        text_blocks.append(f"==== Sheet:{sheet_name} ====")
        # openpyxl vs xlrd 行遍历兼容
        if ext == ".xlsx":
            for row in ws.iter_rows(values_only=True):
                line = "\t".join(str(cell) if cell is not None else "" for cell in row)
                text_blocks.append(line)
        else:
            for row_idx in range(ws.nrows):
                row = ws.row_values(row_idx)
                line = "\t".join(str(cell) for cell in row)
                text_blocks.append(line)
    return "\n".join(text_blocks)


def _load_json(file_path: str) -> str:
    """加载json文件，格式化输出文本"""
    raw = _load_text(file_path)
    data = json.loads(raw)
    return json.dumps(data, ensure_ascii=False, indent=2)


def _load_html_xml(file_path: str) -> str:
    """解析 html htm xml，提取纯文本，去除标签"""
    from bs4 import BeautifulSoup
    raw = _load_text(file_path)
    soup = BeautifulSoup(raw, "lxml")
    return soup.get_text(separator="\n", strip=True)



