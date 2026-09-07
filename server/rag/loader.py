"""文档加载器 - 支持 txt/doc/pdf/markdown/ppt/csv/xls/xlsx/json/xml/html/css/js/sql/other

统一入口: load_document(file_path, max_chars=None)

格式映射:
    纯文本类    .txt .md .markdown .css .js .sql          -> 按文本读取(自动探测编码)
    结构化文本  .json                                     -> 解析后格式化输出
                .xml                                      -> 提取元素文本
                .html .htm                                -> 去除标签提取正文
    表格类      .csv                                      -> 按分隔符解析为行
                .xls .xlsx                                -> 逐 Sheet 逐行输出
    办公文档    .doc .docx                                -> 段落 + 表格文本
                .ppt .pptx                                -> 逐页幻灯片文本
                .pdf                                      -> 逐页抽取文本
    其他        other                                     -> 尝试文本读取, 失败按二进制提取可打印字符

依赖(缺失时对应格式会给出明确安装提示, 不影响其他格式):
    pypdf / python-docx / python-pptx / openpyxl / xlrd
"""

import argparse
import csv
import io
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Dict, Optional

__all__ = ["load_document", "load_documents", "SUPPORTED_EXTS"]

# 尝试解码的编码顺序, 覆盖中英文常见文件
_ENCODINGS = ("utf-8", "gbk", "gb2312", "utf-16", "big5", "latin-1")

SUPPORTED_EXTS = {
    ".txt", ".md", ".markdown", ".css", ".js", ".sql",
    ".json", ".xml", ".html", ".htm",
    ".csv", ".xls", ".xlsx",
    ".doc", ".docx", ".ppt", ".pptx", ".pdf",
}


def load_document(file_path: str, max_chars: Optional[int] = None) -> str:
    """加载并解析文档内容。

    :param file_path: 文件绝对路径
    :param max_chars: 可选, 限制返回的最大字符数
    :return: 提取到的文本内容
    :raises FileNotFoundError: 文件不存在
    :raises ValueError: 解析失败
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    ext = Path(file_path).suffix.lower()
    handler = _HANDLERS.get(ext)
    text = handler(file_path) if handler else _load_other(file_path)

    if max_chars is not None and len(text) > max_chars:
        text = text[:max_chars]
    return text


def load_documents(paths, max_chars: Optional[int] = None) -> Dict[str, str]:
    """批量加载多个文档, 返回 {文件路径: 文本内容}。

    单个文件解析失败时, 该条目记录为 'ERROR: <原因>', 不中断整体流程。
    """
    result: Dict[str, str] = {}
    for p in paths:
        try:
            result[p] = load_document(p, max_chars=max_chars)
        except Exception as e:  # noqa: BLE001 - 批量场景下收集所有错误
            result[p] = f"ERROR: {e}"
    return result


# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------

def _read_text_bytes(file_path: str) -> str:
    """读取文件原始字节并按候选编码顺序解码。"""
    with open(file_path, "rb") as f:
        raw = f.read()
    for encoding in _ENCODINGS:
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


def _keep_printable(text: str) -> str:
    """过滤不可打印字符(保留换行/制表), 用于二进制文件的内容提取。"""
    kept = [c for c in text if c.isprintable() or c in "\n\r\t"]
    return "".join(kept)


def _cells_to_line(values) -> str:
    """把一行单元格统一为 'a | b | c' 形式, 便于后续文本处理。"""
    cleaned = ["" if v is None else str(v).strip() for v in values]
    return " | ".join(cleaned)


# ---------------------------------------------------------------------------
# 纯文本类
# ---------------------------------------------------------------------------

def _load_text(file_path: str) -> str:
    """加载纯文本 / markdown / css / js / sql 文件。"""
    return _read_text_bytes(file_path)


# ---------------------------------------------------------------------------
# 结构化文本类
# ---------------------------------------------------------------------------

def _load_json(file_path: str) -> str:
    """加载 JSON, 解析成功后格式化输出(保留中文)。"""
    text = _read_text_bytes(file_path)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 解析失败: {e}") from e
    return json.dumps(data, ensure_ascii=False, indent=2)


def _load_xml(file_path: str) -> str:
    """加载 XML, 递归提取元素文本与尾文本。"""
    text = _read_text_bytes(file_path)
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        raise ValueError(f"XML 解析失败: {e}") from e
    return _xml_to_text(root)


def _xml_to_text(elem: ET.Element) -> str:
    parts: list = []
    if elem.text and elem.text.strip():
        parts.append(elem.text.strip())
    for child in elem:
        parts.append(_xml_to_text(child))
        if child.tail and child.tail.strip():
            parts.append(child.tail.strip())
    return "\n".join(p for p in parts if p)


class _HTMLTextExtractor(HTMLParser):
    """去除 HTML 标签/脚本/样式, 只保留正文文本。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list = []
        self._skip = 0  # 处于 <script>/<style> 内部时为 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in ("script", "style"):
            self._skip += 1
        if tag in ("p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5",
                   "h6", "table", "section", "article"):
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self._skip > 0:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if self._skip == 0:
            self._parts.append(data)

    def text(self) -> str:
        raw = "".join(self._parts)
        lines = re.split(r"[ \t]*\n[ \t]*", raw)
        return "\n".join(line.strip() for line in lines if line.strip())


def _load_html(file_path: str) -> str:
    """加载 HTML/HTM, 提取可见正文。"""
    text = _read_text_bytes(file_path)
    extractor = _HTMLTextExtractor()
    try:
        extractor.feed(text)
    except Exception as e:  # 容错: 部分畸形 HTML 可能中断解析
        raise ValueError(f"HTML 解析失败: {e}") from e
    result = extractor.text()
    if result:
        return result
    # 极端情况下 parser 无输出, 退化为纯文本
    return _keep_printable(text)


# ---------------------------------------------------------------------------
# 表格类
# ---------------------------------------------------------------------------

def _load_csv(file_path: str) -> str:
    """加载 CSV, 自动探测分隔符(支持 , ; \\t |), 逐行输出。"""
    text = _read_text_bytes(file_path)
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel  # 默认逗号分隔

    rows = []
    for row in csv.reader(io.StringIO(text), dialect):
        rows.append(_cells_to_line(row))
    return "\n".join(rows)


def _load_xlsx(file_path: str) -> str:
    """加载 XLSX, 逐 Sheet 逐行输出(公式取计算值)。"""
    try:
        from openpyxl import load_workbook
    except ImportError:
        raise ValueError("读取 XLSX 需要安装 openpyxl: pip install openpyxl") from None

    wb = load_workbook(file_path, read_only=True, data_only=True)
    try:
        parts = []
        for ws in wb.worksheets:
            parts.append(f"# Sheet: {ws.title}")
            for row in ws.iter_rows(values_only=True):
                line = _cells_to_line(row)
                if line.strip(" |"):
                    parts.append(line)
        return "\n".join(parts)
    finally:
        wb.close()


def _load_xls(file_path: str) -> str:
    """加载 XLS(旧版二进制格式), 逐 Sheet 逐行输出。"""
    try:
        import xlrd
    except ImportError:
        raise ValueError("读取 XLS 需要安装 xlrd: pip install xlrd") from None

    wb = xlrd.open_workbook(file_path)
    parts = []
    for sheet in wb.sheets():
        parts.append(f"# Sheet: {sheet.name}")
        for row_idx in range(sheet.nrows):
            values = [sheet.cell_value(row_idx, col_idx) for col_idx in range(sheet.ncols)]
            line = _cells_to_line(values)
            if line.strip(" |"):
                parts.append(line)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 办公文档类
# ---------------------------------------------------------------------------

def _load_pdf(file_path: str) -> str:
    """加载 PDF, 逐页抽取文本(扫描件无文本层时返回空串)。"""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ValueError("读取 PDF 需要安装 pypdf: pip install pypdf") from None

    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:  # 单页抽取失败不中断整体
            pages.append("")
    return "\n".join(pages)


def _load_docx(file_path: str) -> str:
    """加载 DOCX: 段落文本 + 表格文本。"""
    try:
        from docx import Document
    except ImportError:
        raise ValueError("读取 DOCX 需要安装 python-docx: pip install python-docx") from None

    doc = Document(file_path)
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            parts.append(_cells_to_line(cell.text.replace("\n", " ") for cell in row.cells))
    return "\n".join(parts)


def _load_doc(file_path: str) -> str:
    """加载 DOC(旧版 OLE 二进制格式)。

    Word 的 .doc 内部文本多以 UTF-16LE 存储, 直接整体解码会产生噪声;
    这里按二进制提取可打印字符(含中文), 得到尽量干净的文本。
    """
    with open(file_path, "rb") as f:
        raw = f.read()

    candidates = []
    # 优先尝试 UTF-16LE 解码(Word 二进制文本的常见存储方式)
    candidates.append(_keep_printable(raw.decode("utf-16-le", errors="ignore")))
    # 再尝试 UTF-8 / Latin-1
    candidates.append(_keep_printable(raw.decode("utf-8", errors="ignore")))
    candidates.append(_keep_printable(raw.decode("latin-1", errors="ignore")))

    best = max(candidates, key=lambda s: len(s.strip()))
    # 压缩多余空白
    return re.sub(r"[ \t]{2,}", " ", best).strip()


def _load_pptx(file_path: str) -> str:
    """加载 PPTX: 逐页输出文本框与表格内容, 每页以 [Slide N] 标记。"""
    try:
        from pptx import Presentation
    except ImportError:
        raise ValueError("读取 PPTX 需要安装 python-pptx: pip install python-pptx") from None

    prs = Presentation(file_path)
    parts = []
    for idx, slide in enumerate(prs.slides, 1):
        slide_lines = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    line = para.text.strip()
                    if line:
                        slide_lines.append(line)
            if getattr(shape, "has_table", False) and shape.has_table:
                for row in shape.table.rows:
                    slide_lines.append(
                        _cells_to_line(cell.text.replace("\n", " ") for cell in row.cells)
                    )
        if slide_lines:
            parts.append(f"[Slide {idx}]")
            parts.extend(slide_lines)
    return "\n".join(parts)


def _load_ppt(file_path: str) -> str:
    """加载 PPT(旧版二进制格式), 按可打印字符提取文本。"""
    with open(file_path, "rb") as f:
        raw = f.read()
    text = _keep_printable(raw.decode("utf-16-le", errors="ignore"))
    if not text.strip():
        text = _keep_printable(raw.decode("utf-8", errors="ignore"))
    return re.sub(r"[ \t]{2,}", " ", text).strip()


# ---------------------------------------------------------------------------
# 其他 / 未知类型
# ---------------------------------------------------------------------------

def _load_other(file_path: str) -> str:
    """未知扩展名: 先尝试按文本读取, 失败则按二进制提取可打印字符。"""
    try:
        return _read_text_bytes(file_path)
    except Exception:
        with open(file_path, "rb") as f:
            raw = f.read()
        return _keep_printable(raw.decode("utf-8", errors="ignore"))


# 格式 -> 处理函数 映射表
_HANDLERS: Dict[str, Callable[[str], str]] = {
    ".txt": _load_text,
    ".md": _load_text,
    ".markdown": _load_text,
    ".css": _load_text,
    ".js": _load_text,
    ".sql": _load_text,
    ".json": _load_json,
    ".xml": _load_xml,
    ".html": _load_html,
    ".htm": _load_html,
    ".csv": _load_csv,
    ".xls": _load_xls,
    ".xlsx": _load_xlsx,
    ".doc": _load_doc,
    ".docx": _load_docx,
    ".ppt": _load_ppt,
    ".pptx": _load_pptx,
    ".pdf": _load_pdf,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="文档加载器: 提取 txt/doc/pdf/markdown/ppt/csv/xls/xlsx/json/xml/html/css/js/sql 等文件文本")
    parser.add_argument("file", nargs="+", help="一个或多个文件路径")
    parser.add_argument("--max-chars", type=int, default=None, help="限制每个文件输出的最大字符数")
    args = parser.parse_args()

    for path in args.file:
        print(f"===== {path} =====")
        try:
            print(load_document(path, max_chars=args.max_chars))
        except Exception as e:  # noqa: BLE001 - CLI 场景打印错误后继续下一个文件
            print(f"[错误] {e}", file=sys.stderr)
        print()


if __name__ == "__main__":
    main()
