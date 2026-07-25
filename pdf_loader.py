import pymupdf  # PyMuPDF
import os

def extract_text_from_pdf(pdf_path: str) -> str:
    """使用 PyMuPDF 从 PDF 文件中提取纯文本"""
    try:
        doc = pymupdf.open(pdf_path)
        full_text = []
        for page in doc:
            text = page.get_text()
            if text.strip():  # 只保留非空页
                full_text.append(text)
        doc.close()
        
        result = "\n".join(full_text)
        
        # 控制长度，防止超出模型上下文窗口
        if len(result) > 8000:
            result = result[:8000] + "\n... (内容过长，已截断)"
        
        return result
    except Exception as e:
        return f"PDF提取失败: {str(e)}"

def save_uploaded_file(file_obj, save_path: str) -> str:
    """保存 Gradio 上传的文件到本地临时路径"""
    try:
        # file_obj 是 Gradio 上传的文件对象
        with open(save_path, 'wb') as f:
            f.write(file_obj.read())
        return save_path
    except Exception as e:
        return f"文件保存失败: {str(e)}"