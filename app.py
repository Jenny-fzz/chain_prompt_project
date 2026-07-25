import gradio as gr
from crawler import fetch_webpage_content
from chain_prompt import chain_prompt_qa, call_gpt
from pdf_loader import extract_text_from_pdf
import datetime
import os

# ========== 单次提示（对照组） ==========
def single_prompt_qa(web_content, user_question):
    single_prompt = f"""
请根据以下网页内容回答用户问题，直接给出答案。

要求：
1. 严格基于提供的网页内容作答
2. 如果内容中没有相关信息，请直接说"未找到相关信息"
3. 不要添加外部知识

【网页内容】：
{web_content}

【用户问题】：
{user_question}

【你的回答】：
"""
    messages = [
        {"role": "system", "content": "你是一个严谨的问答助手，只能基于提供的信息作答。"},
        {"role": "user", "content": single_prompt}
    ]
    
    result = call_gpt(messages)
    return result


# ========== 保存结果到文件 ==========
def save_results_to_file(url, question, single_result, chain_answer, chain_intermediate):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    content = f"""
{'='*70}
📊 对比实验报告
生成时间: {timestamp}
{'='*70}

【测试信息】
网址: {url}
问题: {question}

{'='*70}
【对照组 - 单次提示】
{'-'*40}
{single_result}

{'='*70}
【实验组 - 链式提示】
{'-'*40}
最终回答：
{chain_answer}

中间提取信息（链式思考过程）：
{chain_intermediate}

{'='*70}
"""
    
    try:
        with open('results.txt', 'a', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"保存失败: {e}")
        return False


# ========== Gradio 核心函数 ==========
def process_chain_only(url, question):
    """仅链式提示模式（网页）"""
    if not url or not question:
        return "请填写完整的URL和问题", "", ""
    
    web_content = fetch_webpage_content(url)
    if "抓取失败" in web_content:
        return f"❌ {web_content}", "", ""
    
    final_answer, intermediate = chain_prompt_qa(web_content, question)
    
    return final_answer, intermediate, f"✅ 抓取成功，共 {len(web_content)} 字符"


def process_compare(url, question):
    """对比实验模式"""
    if not url or not question:
        return "请填写完整的URL和问题", "", "", "", ""
    
    web_content = fetch_webpage_content(url)
    if "抓取失败" in web_content:
        return f"❌ {web_content}", "", "", "", ""
    
    single_result = single_prompt_qa(web_content, question)
    chain_answer, chain_intermediate = chain_prompt_qa(web_content, question)
    
    save_results_to_file(url, question, single_result, chain_answer, chain_intermediate)
    
    return (
        single_result,
        chain_answer,
        chain_intermediate,
        f"✅ 对比完成！结果已保存到 results.txt",
        f"✅ 抓取成功，共 {len(web_content)} 字符"
    )


def process_pdf_qa(file_obj, question):
    """处理 PDF 上传问答"""
    if file_obj is None:
        return "请先上传一个 PDF 文件", "", ""
    
    if not question:
        return "请输入您的问题", "", ""
    
    try:
        file_path = file_obj.name
        pdf_content = extract_text_from_pdf(file_path)
        
        if "提取失败" in pdf_content or len(pdf_content.strip()) == 0:
            return f"❌ PDF 内容提取失败或为空", "", ""
        
        final_answer, intermediate = chain_prompt_qa(pdf_content, question)
        
        return final_answer, intermediate, f"✅ PDF 解析成功，共提取 {len(pdf_content)} 字符"
    
    except Exception as e:
        return f"❌ 处理失败: {str(e)}", "", ""


# ========== 创建 Gradio 界面 ==========
with gr.Blocks(title="链式提示智能问答系统") as demo:
    gr.Markdown("""
    # 🔍 链式提示智能问答系统
    ### 输入网页链接或上传PDF，系统会先提取关键信息，再生成精准回答
    """)
    
    # ---- Tab 1: 链式提示问答（整合网页 + PDF） ----
    with gr.Tab("📝 链式提示问答"):
        gr.Markdown("""
        ### 选择输入方式：网页链接 或 上传 PDF
        """)
        
        # 选择输入方式的单选按钮
        input_choice = gr.Radio(
            choices=["🔗 网页链接", "📄 上传 PDF"],
            label="选择输入方式",
            value="🔗 网页链接"
        )
        
        # 网页链接输入区域（默认显示）
        with gr.Row(visible=True) as url_row:
            with gr.Column(scale=2):
                url_input = gr.Textbox(
                    label="🔗 网页链接",
                    placeholder="https://baike.baidu.com/item/生成式人工智能",
                    lines=1
                )
            with gr.Column(scale=1):
                question_input = gr.Textbox(
                    label="❓ 您的问题",
                    placeholder="请输入您想了解的问题...",
                    lines=2
                )
                submit_btn = gr.Button("🚀 开始问答", variant="primary")
        
        # PDF 上传区域（默认隐藏）
        with gr.Row(visible=False) as pdf_row:
            with gr.Column(scale=2):
                pdf_file_input = gr.File(
                    label="📄 上传 PDF 文件",
                    file_types=[".pdf"]
                )
            with gr.Column(scale=1):
                pdf_question_input = gr.Textbox(
                    label="❓ 您的问题",
                    placeholder="请输入您想了解的问题...",
                    lines=2
                )
                pdf_submit_btn = gr.Button("🚀 开始问答", variant="primary")
        
        # 输出区域（共用）
        with gr.Row():
            with gr.Column(scale=3):
                answer_output = gr.Textbox(
                    label="📌 最终回答",
                    lines=12
                )
        
        status_text = gr.Textbox(
            label="📡 状态",
            lines=1
        )
        intermediate_output = gr.Textbox(
            label="🔍 中间提取信息（链式思考过程）",
            lines=8
        )
        
        # 切换输入方式：显示/隐藏对应的行
        def toggle_input(choice):
            if choice == "🔗 网页链接":
                return gr.update(visible=True), gr.update(visible=False)
            else:
                return gr.update(visible=False), gr.update(visible=True)
        
        input_choice.change(
            fn=toggle_input,
            inputs=[input_choice],
            outputs=[url_row, pdf_row]
        )
        
        # 网页链接提交
        submit_btn.click(
            fn=process_chain_only,
            inputs=[url_input, question_input],
            outputs=[answer_output, intermediate_output, status_text]
        )
        
        # PDF 提交
        pdf_submit_btn.click(
            fn=process_pdf_qa,
            inputs=[pdf_file_input, pdf_question_input],
            outputs=[answer_output, intermediate_output, status_text]
        )
    
    # ---- Tab 2: 对比实验 ----
    with gr.Tab("🧪 对比实验"):
        gr.Markdown("""
        ### 对比单次提示 vs 链式提示
        看看链式提示在准确性、完整性、可追溯性上的优势！
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                compare_url = gr.Textbox(
                    label="🔗 网页链接",
                    placeholder="https://baike.baidu.com/item/生成式人工智能",
                    lines=1
                )
                compare_question = gr.Textbox(
                    label="❓ 您的问题",
                    placeholder="请输入您想了解的问题...",
                    lines=2
                )
                compare_btn = gr.Button("🧪 开始对比实验", variant="primary")
            
            with gr.Column(scale=3):
                with gr.Row():
                    with gr.Column():
                        single_output = gr.Textbox(
                            label="【对照组】单次提示",
                            lines=10
                        )
                    with gr.Column():
                        chain_output = gr.Textbox(
                            label="【实验组】链式提示 - 最终回答",
                            lines=10
                        )
        
        compare_status = gr.Textbox(
            label="📡 状态",
            lines=1
        )
        compare_fetch_status = gr.Textbox(
            label="📡 抓取状态",
            lines=1
        )
        chain_intermediate_output = gr.Textbox(
            label="【实验组】链式提示 - 中间提取信息",
            lines=6
        )
        
        compare_btn.click(
            fn=process_compare,
            inputs=[compare_url, compare_question],
            outputs=[
                single_output,
                chain_output,
                chain_intermediate_output,
                compare_status,
                compare_fetch_status
            ]
        )
    
    # ---- Tab 3: 项目说明 ----
    with gr.Tab("📖 项目说明"):
        gr.Markdown("""
        ## 🎯 项目背景
        大模型在处理长文档、复杂逻辑问答时容易出现 **"幻觉"** 和 **信息遗漏** 问题。
        
        ## 💡 解决方案：链式提示
        将"一次问答"拆解为两步：
        1. **信息提取**：先精准提取与问题相关的关键信息
        2. **精准回答**：基于提取的信息生成回答
        
        ## 📊 对比实验
        | 维度 | 单次提示 | 链式提示（本方案） |
        |------|----------|-------------------|
        | 可追溯性 | ❌ 不知道依据什么回答 | ✅ 显示提取的关键信息 |
        | 幻觉风险 | ⚠️ 较高 | ✅ 较低 |
        | 回答结构 | 平铺直叙 | 结构化呈现 |
        
        ## 📁 支持的输入方式
        | 方式 | 说明 |
        |------|------|
        | 网页链接 | 输入URL，自动抓取网页内容 |
        | PDF文档 | 上传PDF文件，自动提取文本内容 |
        
        ## 🛠️ 技术栈
        - Python
        - ModelScope API
        - BeautifulSoup（网页抓取）
        - PyMuPDF（PDF文本提取）
        - Gradio（Web界面）
        """)


# ========== 启动 ==========
if __name__ == "__main__":
    demo.launch(share=True)
