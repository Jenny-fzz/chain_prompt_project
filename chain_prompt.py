import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 使用ModelScope的API
client = OpenAI(
    api_key=os.getenv("MODELSCOPE_API_KEY"),
    base_url="https://api-inference.modelscope.cn/v1/"
)

def call_gpt(messages, model="Qwen/Qwen3.5-35B-A3B", temperature=0.3):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content

def chain_prompt_qa(web_content, user_question):
    extraction_prompt = f"""
你是一个精准的信息提取器。请阅读以下网页内容，提取与用户问题相关的关键信息。

要求：
1. 只提取与问题直接相关的事实、数据、定义
2. 忽略无关的修饰语和背景介绍
3. 如果内容中没有相关信息，请直接回复"未找到相关信息"

【用户问题】：
{user_question}

【网页内容】：
{web_content}

【提取的关键信息】：
"""
    
    messages_step1 = [
        {"role": "system", "content": "你是一个严谨的信息提取助手，只输出基于原文的事实。"},
        {"role": "user", "content": extraction_prompt}
    ]
    
    print("🔄 Step 1: 正在提取关键信息...")
    extracted_info = call_gpt(messages_step1)
    print(f"✅ Step 1 完成，提取到 {len(extracted_info)} 字符")
    
    if "未找到相关信息" in extracted_info or len(extracted_info) < 10:
        return "❌ 根据提供的网页内容，无法回答您的问题。", extracted_info
    
    answering_prompt = f"""
请基于【提取的关键信息】回答用户的问题。

规则：
1. 严格基于下方提供的信息，不要添加外部知识
2. 如果信息不完整，诚实地说明"根据现有信息，只能部分回答"
3. 引用信息中的具体内容来支撑你的答案

【提取的关键信息】：
{extracted_info}

【用户问题】：
{user_question}

【你的回答】：
"""
    
    messages_step2 = [
        {"role": "system", "content": "你是一个严谨的问答助手，只能基于提供的信息作答。"},
        {"role": "user", "content": answering_prompt}
    ]
    
    print("🔄 Step 2: 正在生成最终回答...")
    final_answer = call_gpt(messages_step2)
    print("✅ Step 2 完成")
    
    return final_answer, extracted_info