from crawler import fetch_webpage_content
from chain_prompt import chain_prompt_qa, call_gpt  # 导入call_gpt
# 🆕 新增：导入时间模块
import datetime


# 🆕 新增：save_results 函数（放在 single_prompt_qa 前面）
def save_results(url, question, single_result, chain_answer, chain_intermediate):
    """
    将对比实验结果保存到 results.txt 文件
    """
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
【评估建议】
1. 准确性：哪个回答更准确？
2. 完整性：哪个回答更完整？
3. 幻觉：哪个回答出现了文档中没有的内容？
{'='*70}

"""
    
    try:
        with open('results.txt', 'a', encoding='utf-8') as f:
            f.write(content)
        print(f"\n✅ 结果已保存到 results.txt")
        return True
    except Exception as e:
        print(f"\n❌ 保存失败: {e}")
        return False

def single_prompt_qa(web_content, user_question):
    """
    单次提示（对照组）
    直接让模型回答问题，不做分步提取
    """
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
    
    print("🔄 [对照组] 单次提示：直接生成回答...")
    result = call_gpt(messages)
    print("✅ [对照组] 完成")
    return result


def compare_qa(web_content, user_question,url=""):
    """
    对比单次提示 vs 链式提示
    """
    print("\n" + "="*70)
    print("🧪 开始对比实验：单次提示 vs 链式提示")
    print("="*70 + "\n")
    
    # 对照组：单次提示
    print("【对照组】单次提示")
    print("-" * 40)
    single_result = single_prompt_qa(web_content, user_question)
    
    print("\n" + "-"*70 + "\n")
    
    # 实验组：链式提示
    print("【实验组】链式提示")
    print("-" * 40)
    chain_answer, chain_intermediate = chain_prompt_qa(web_content, user_question)
    
    # 输出对比结果
    print("\n" + "="*70)
    print("📊 对比结果")
    print("="*70)
    
    print("\n【对照组 - 单次提示】")
    print(single_result)
    
    print("\n【实验组 - 链式提示】")
    print("最终回答：")
    print(chain_answer)
    print("\n中间提取信息（证明分步思考）：")
    print(chain_intermediate)
    
    print("\n" + "="*70)
    print("💡 评估建议：")
    print("1. 准确性：哪个回答更准确？")
    print("2. 完整性：哪个回答更完整？")
    print("3. 幻觉：哪个回答出现了文档中没有的内容？")
    print("="*70)

    # 🆕 自动保存到文件
    save_results(url, user_question, single_result, chain_answer, chain_intermediate)
    return single_result, chain_answer, chain_intermediate
   
def main():
    # 选择模式
    print("="*60)
    print("🔍 链式提示智能问答系统")
    print("="*60)
    print("请选择模式：")
    print("1. 仅链式提示（问答模式）")
    print("2. 对比实验（单次提示 vs 链式提示）")
    choice = input("请输入 1 或 2: ").strip()
    
    # 获取输入
    url = input("请输入网页链接: ").strip()
    question = input("请输入您的问题: ").strip()
    
    # 抓取网页
    print("\n📡 正在抓取网页内容...")
    web_content = fetch_webpage_content(url)
    
    if "抓取失败" in web_content:
        print(f"❌ {web_content}")
        return
    
    print(f"✅ 抓取成功，共 {len(web_content)} 字符")
    
    # 根据选择执行
    if choice == "2":
        compare_qa(web_content, question,url)
    else:
        # 仅链式提示
        final_answer, intermediate = chain_prompt_qa(web_content, question)
        print("\n" + "="*60)
        print("📌 最终回答：")
        print(final_answer)
        print("\n" + "="*60)
        print("🔍 中间提取信息（展示链式思考过程）：")
        print(intermediate)


if __name__ == "__main__":
    main()