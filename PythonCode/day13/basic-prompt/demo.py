from dashscope import Generation
from typing import List, Dict, Tuple

class DynamicFewShotSelector:
    """
    动态Few-shot选择器
    根据用户问题类型自动选择最相关的示例
    
    iOS类比：这相当于UITableView的数据源方法 tableView(_:cellForRowAt:),
    根据indexPath返回不同的cell配置
    """
    
    def __init__(self):
        # 示例库：按类别组织
        self.example_library = {
            "swift": [
                {"question": "什么是可选类型？", 
                 "answer": "可选类型表示值可以是该类型或者nil，使用?标记"},
                {"question": "如何避免循环引用？", 
                 "answer": "使用[weak self]或[unowned self]修饰闭包中的self"},
            ],
            "uikit": [
                {"question": "UITableView性能优化？", 
                 "answer": "1.使用reuseIdentifier 2.避免透明视图 3.异步绘制"},
                {"question": "ViewController生命周期？", 
                 "answer": "init -> loadView -> viewDidLoad -> viewWillAppear -> viewDidAppear"},
            ],
            "architecture": [
                {"question": "MVC vs MVVM区别？", 
                 "answer": "MVC中ViewController承担太多职责；MVVM通过ViewModel解耦逻辑和UI"},
                {"question": "何时使用VIPER？", 
                 "answer": "大型复杂项目，需要严格职责分离和可测试性时"},
            ]
        }
    
    def classify_query(self, query: str) -> str:
        """
        根据问题关键词分类
        
        iOS类比：这相当于路由方法，根据URL路由到不同的Handler
        """
        query_lower = query.lower()
        
        if any(k in query_lower for k in ['swift', 'struct', 'class', 'enum', 'protocol']):
            return "swift"
        elif any(k in query_lower for k in ['uitableview', 'uiview', 'viewcontroller', 'navigation']):
            return "uikit"
        elif any(k in query_lower for k in ['架构', 'mvvm', 'mvc', 'viper', 'architecture']):
            return "architecture"
        return "general"
    
    def select_examples(self, query: str, k: int = 2) -> List[Dict]:
        """
        根据查询选择top-k个最相关示例
        
        iOS类比：这是数据源的过滤方法，只返回需要的数据
        """
        category = self.classify_query(query)
        examples = self.example_library.get(category, [])
        # 返回前k个示例
        return examples[:min(k, len(examples))]
    
    def build_prompt(self, query: str) -> str:
        """
        构建包含动态示例的Prompt
        
        iOS类比：这相当于Cell的配置方法，根据数据返回完整的cell
        """
        examples = self.select_examples(query, k=2)
        
        # 构建示例部分
        examples_text = "\n\n".join([
            f"示例{i+1}:\n问：{ex['question']}\n答：{ex['answer']}"
            for i, ex in enumerate(examples)
        ])
        
        return f"""
你是一位资深的iOS开发专家。请根据以下示例的风格回答问题。

{examples_text}

现在请回答：
问：{query}
答：
"""
