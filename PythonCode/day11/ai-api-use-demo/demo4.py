# 通义千问推荐使用 tiktoken 或 jieba 进行Token估算
# 由于中文分词特殊性，建议使用字符估算 + 经验系数

def count_tokens_cn(text: str) -> int:
    """
    估算中文文本的Token数
    
    经验估算：中文约1.5-2个字符 ≈ 1个Token
    英文约4个字符 ≈ 1个Token
    
    Args:
        text: 待计算的文本
        
    Returns:
        估算的Token数量
    """
    # 简单估算：按UTF-8字节数除以2（中文平均约2字节/字符）
    # 实际Token数会更准确，建议使用专门的tokenizer
    
    import re
    
    # 分离中英文
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    other_chars = len(text) - chinese_chars - english_chars
    
    # 估算Token
    # 中文：约1.5个字符 ≈ 1 token
    # 英文：约4个字符 ≈ 1 token
    # 标点/数字：约2个 ≈ 1 token
    estimated_tokens = chinese_chars / 1.5 + english_chars / 4 + other_chars / 2
    
    return int(estimated_tokens)

def count_tokens_messages(
    messages: list, 
    model: str = "qwen-turbo"
) -> int:
    """
    计算对话消息列表的总Token数
    
    Args:
        messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
        model: 模型名称
        
    Returns:
        总Token数（估算）
    """
    total_tokens = 0
    
    for message in messages:
        # 角色开销（约3-4 tokens）
        total_tokens += 4
        # 内容Token
        total_tokens += count_tokens_cn(message.get("content", ""))
    
    # 每条消息的开销
    total_tokens += 3
    
    return total_tokens

# ============ 使用示例 ============
if __name__ == "__main__":
    # 单段文本计算
    text = "成都教育科技公司开发的作业批改助手，可以帮助老师快速批改学生作业。"
    tokens = count_tokens_cn(text)
    print(f"文本Token数（估算）: {tokens}")
    
    # 消息列表计算
    messages = [
        {"role": "system", "content": "你是一位成都教育科技公司的数学老师。"},
        {"role": "user", "content": "请批改这道数学题：12 × 8 = 96"},
        {"role": "assistant", "content": "答案正确！解题思路清晰。"}
    ]
    
    total = count_tokens_messages(messages)
    print(f"对话总Token数（估算）: {total}")