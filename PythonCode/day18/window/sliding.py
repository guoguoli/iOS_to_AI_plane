def sliding_window_context(messages: list, max_messages: int = 10) -> list:
    """
    滑动窗口：只保留最近N条消息
    
    适用场景：
    - 对话顺序重要
    - 旧信息价值递减
    - 简单对话系统
    """
    if len(messages) <= max_messages:
        return messages
    # 保留系统消息 + 最近消息
    system_msgs = [m for m in messages if m["role"] == "system"]
    other_msgs = [m for m in messages if m["role"] != "system"]
    return system_msgs + other_msgs[-max_messages:] #取倒数X条

import dashscope
from dashscope import Messages

def summarize_old_messages(messages: list, llm_api_key: str) -> str:
    """
    摘要压缩：使用LLM生成历史摘要
    
    适用场景：
    - 长程任务需要保持连贯性
    - 关键信息不能丢失
    - 对话主题需要保持
    """
    dashscope.api_key = llm_api_key
    
    # 提取需要摘要的消息（排除system和最近2条）
    old_messages = messages[1:-2]  # 保留最近2条全量
    if len(old_messages) <= 2:
        return ""
    
    # 构建摘要提示
    summary_prompt = f"""请将以下对话历史总结为简洁的摘要，保留关键信息和主题：
    
    {old_messages}
    
    摘要格式：
    - 对话主题：[主题]
    - 已完成讨论：[要点1, 要点2, ...]
    - 用户关键信息：[如用户偏好、已提供的数据等]
    """
    
    response = dashscope.Generation.call(
        model="qwen-turbo",
        messages=[{"role": "user", "content": summary_prompt}],
        result_format="message"
    )
    
    return response["output"]["choices"][0]["message"]["content"]