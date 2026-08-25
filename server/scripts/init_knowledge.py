"""批量向量化示例知识库文档"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.session import SessionLocal
from models.knowledge import KnowledgeFile
from services.rag_service import get_rag_service
from core.config import settings


def init_knowledge():
    """将 docs_seed 目录下的文档向量化入库"""
    seed_dir = Path(__file__).parent.parent / "docs_seed"
    if not seed_dir.exists():
        print("docs_seed 目录不存在")
        return
    db = SessionLocal()
    rag = get_rag_service()
    for file_path in seed_dir.glob("*"):
        if file_path.suffix.lower() not in (".txt", ".md", ".pdf", ".doc", ".docx"):
            continue
        existing = db.query(KnowledgeFile).filter(KnowledgeFile.file_name == file_path.name).first()
        if existing:
            print(f"跳过已存在: {file_path.name}")
            continue
        record = KnowledgeFile(
            file_name=file_path.name,
            file_type="markdown" if file_path.suffix.lower() in (".md", ".markdown") else file_path.suffix[1:],
            file_size=file_path.stat().st_size,
            file_path=str(file_path).replace("\\", "/"),
            upload_by=1,
            upload_role="admin",
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        try:
            count = rag.process_file(db, record)
            print(f"向量化完成: {file_path.name} -> {count} 块")
        except Exception as e:
            print(f"向量化失败: {file_path.name} -> {e}")
    db.close()
    print("知识库初始化完成！")


if __name__ == "__main__":
    init_knowledge()
