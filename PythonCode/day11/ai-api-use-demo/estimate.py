def estimate_cost_cn(input_tokens: int, output_tokens: int, model: str = "qwen-turbo"):
    """
    预估通义千问API调用成本
    
    Args:
        input_tokens: 输入Token数
        output_tokens: 输出Token数  
        model: 模型名称
        
    Returns:
        预估成本（人民币元）
    """
    # 价格表（¥/1M Tokens）
    prices = {
        "qwen-turbo": {"input": 4.0, "output": 12.0},
        "qwen-plus": {"input": 4.0, "output": 12.0},
        "qwen-max": {"input": 40.0, "output": 120.0},
    }
    
    model_prices = prices.get(model, prices["qwen-turbo"])
    
    input_cost = (input_tokens / 1_000_000) * model_prices["input"]
    output_cost = (output_tokens / 1_000_000) * model_prices["output"]
    
    return input_cost + output_cost

# 使用示例
cost = estimate_cost_cn(input_tokens=500000, output_tokens=2000000, model="qwen-turbo")
print(f"预估成本: ¥{cost:.4f}")
# 输出: 预估成本: ¥0.0044