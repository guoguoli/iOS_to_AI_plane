export DASHSCOPE_API_KEY="sk-6f8168916cc9407c90c37ad4a257e0e0"





缩写	英文全称	中文译名	通俗解释
SFT	Supervised Fine-Tuning	监督微调	用 “指令 - 标准答案” 数据教模型，让它从 “会说话” 变成 “会听人话、按要求回答”
RLHF	Reinforcement Learning from Human Feedback	基于人类反馈的强化学习	GPT 流派的核心对齐方法：用人类偏好数据，通过强化学习让模型更懂人类
Reward Model	Reward Model	奖励模型	给模型的回答 “打分” 的裁判模型，判断回答是否有用、安全、符合人类偏好
PPO	Proximal Policy Optimization	近端策略优化	强化学习里的一种算法，用来在不破坏模型原有能力的前提下，根据奖励信号优化回答偏好
Rejection Sampling	Rejection Sampling	拒绝采样	让模型生成多个回答，用奖励模型挑出最好的那些，扔掉差的，用优质样本再教模型
DPO	Direct Preference Optimization	直接偏好优化	替代 PPO 的轻量方法，跳过复杂强化学习循环，直接用人类偏好数据优化模型，更稳定高效


场景	推荐模型
日常快速编码 / 脚本	gpt-4o-mini / deepseek-v3
复杂算法 / 疑难 Bug	o1-mini / gpt-4o
长上下文 / 多文件项目	gpt-4-32k / deepseek-r1
中文友好 / 国内访问	deepseek-v3 / Qwen 系列
学习 / 代码解释	deepseek-r1 / o1-mini



以下按**国内资讯、国际资讯、学术/技术前沿、模型/开源社区、趋势/报告**五大类，整理最值得关注的AI前沿网站，覆盖新闻、技术、论文、模型、工具与趋势，方便你快速定位一手信息。

---

### 一、国内AI资讯平台（中文，快速看热点与落地）
#### 1. 量子位（QbitAI）
- **网址**：https://www.qbitai.com
- **特点**：AI领域**最快、最权威**的中文媒体，ChatGPT、Sora、GPT-4o等重大突破**首发报道**；深度技术解析+视频解读，覆盖大模型、多模态、自动驾驶、AI芯片；每日多次更新，重大事件即时推送。
- **适合**：快速获取全球AI热点、技术解读、行业动态。

#### 2. 机器之心（Synced）
- **网址**：https://www.jiqizhixin.com
- **特点**：专注AI**技术前沿**，覆盖大模型、机器学习、计算机视觉、机器人、AI芯片；“Synced Report”系列深度分析技术演进逻辑；学术+产业双视角，内容偏硬核。
- **适合**：想深入理解AI技术原理、研究进展的开发者/研究者。

#### 3. 新智元
- **网址**：https://www.zhidx.com
- **特点**：主打**AI+产业**，不仅报技术，更聚焦金融、医疗、制造等行业落地；定期发布**AI大模型排行榜**，跟踪国产模型进展；内容通俗，兼顾技术与商业。
- **适合**：关注AI商业化、行业应用、国产模型动态。

#### 4. AI科技评论
- **网址**：https://www.aitechtalk.com
- **特点**：偏**B端与产业深度**，聚焦AI技术趋势、企业战略、投融资、行业解决方案；长文深度分析，适合从业者把握行业方向。
- **适合**：产品经理、创业者、行业分析师。

#### 5. 36氪
- **网址**：https://36kr.com
- **特点**：科技创业风向标，AI报道聚焦**商业化、融资、创业生态**；独家消息多，覆盖AI工具、Agent、大模型应用；内容偏商业与产品。
- **适合**：关注AI创业、投资、产品落地。

#### 6. InfoQ中文站（AI频道）
- **网址**：https://xie.infoq.cn/ai
- **特点**：**开发者视角**，深度分析AI开发、架构设计、工程化实践；技术大会直播、案例拆解，偏工程落地。
- **适合**：AI工程师、架构师。

---

### 二、国际AI资讯平台（英文，一手全球动态）
#### 1. MIT Technology Review（AI专栏）
- **网址**：https://www.technologyreview.com/topic/artificial-intelligence
- **特点**：麻省理工主办，**深度、前瞻、硬核**；覆盖AI伦理、技术突破、社会影响；长文分析，适合理解技术本质与未来趋势。
- **适合**：想读深度、有前瞻性的AI分析。

#### 2. TechCrunch（AI板块）
- **网址**：https://techcrunch.com/artificial-intelligence
- **特点**：硅谷科技风向标，聚焦AI**创业、融资、产品动态**；报道及时，适合跟踪全球AI创业生态。
- **适合**：关注AI创业、投资、产品创新。

#### 3. The Verge（AI）
- **网址**：https://www.theverge.com/ai
- **特点**：科技媒体中的“深度报道派”，AI新闻**及时、全面**，兼顾技术与消费级产品。
- **适合**：快速获取全球AI产品与技术动态。

#### 4. VentureBeat AI
- **网址**：https://venturebeat.com/category/ai/
- **特点**：专注AI**企业应用、行业解决方案、技术商业化**；深度访谈与案例，偏B端。
- **适合**：企业决策者、行业分析师。

---

### 三、学术/技术前沿（论文、预印本，最硬核一手技术）
#### 1. arXiv（康奈尔预印本）
- **网址**：https://arxiv.org
- **特点**：全球AI**最核心论文发布平台**，OpenAI、Google DeepMind、Meta等机构论文**优先发布于此**；分类：cs.AI（人工智能）、cs.LG（机器学习）、cs.CV（计算机视觉）、cs.CL（NLP）；每日更新，免费开放。
- **适合**：研究者、工程师，获取**最前沿技术原理**。

#### 2. Papers With Code
- **网址**：https://paperswithcode.com
- **特点**：**论文+代码+SOTA排行榜**三位一体；关联论文与开源实现，可直接跑代码；维护各AI任务（如LLM、CV、NLP）的**当前最优模型排行榜**。
- **适合**：想复现论文、对比模型效果、找开源实现。

#### 3. Semantic Scholar
- **网址**：https://www.semanticscholar.org
- **特点**：AI学术搜索引擎，收录超2亿篇论文；提供引用网络、影响力评分、AI生成摘要；方便追踪论文脉络与领域发展。
- **适合**：文献调研、学术研究。

#### 4. 顶会官网/社区
- **NeurIPS**：https://neurips.cc
- **ICML**：https://icml.cc
- **ICLR**：https://iclr.cc
- **CVPR/ICCV/ECCV**（计算机视觉）、**ACL/EMNLP**（NLP）
- **特点**：AI领域**顶级会议**，收录年度最重磅研究；会议论文代表领域最高水平；可看最新技术方向与突破。

---

### 四、模型/开源社区（看最新模型、开源项目、工具）
#### 1. Hugging Face
- **网址**：https://huggingface.co
- **特点**：全球最大**AI模型社区**；最新开源LLM、多模态、扩散模型；**Open LLM Leaderboard**（模型能力客观标尺）；Spaces可直接在线跑Demo；支持模型下载、微调、部署。
- **适合**：找模型、看排行榜、跑Demo、做开发。

#### 2. GitHub Trending（AI/ML）
- **网址**：https://github.com/trending
- **特点**：开源世界**实时脉搏**；每日/每周热门AI开源项目；跟踪新框架、工具、模型（如LangChain、Llama、Qwen、Sora相关项目）。
- **适合**：发现热门开源项目、学习最新工具链。

#### 3. GitHub Daily
- **网址**：https://githubdaily.com
- **特点**：精选GitHub热门AI/ML项目，每日推送；聚焦**新工具、新模型、新框架**，适合快速扫开源动态。

#### 4. Future Tools
- **网址**：https://futuretools.io
- **特点**：AI工具聚合平台，收录数千款AI工具；按分类（生成、开发、设计、办公）整理，提供评测与推荐；跟踪最新AI工具爆发。
- **适合**：找AI工具、测评、效率提升。

---

### 五、趋势/报告/聚合平台（看行业趋势、权威报告）
#### 1. Gartner
- **网址**：https://www.gartner.com
- **特点**：全球顶级咨询公司；发布**AI技术成熟度曲线（Hype Cycle）**、市场分析报告；判断技术所处阶段（萌芽/成长/成熟/衰退）。
- **适合**：把握AI技术趋势、行业格局。

#### 2. RadarAI
- **网址**：https://radarai.ai
- **特点**：AI动态聚合平台；自动抓取GitHub、Hugging Face、官方博客等源头；按“能力更新、开源项目、落地信号”分类；RSS订阅，10分钟掌握全球动态。
- **适合**：高效追踪AI前沿，减少信息过载。

#### 3. OpenAI Blog / Google AI Blog / Meta AI Blog
- **OpenAI**：https://openai.com/blog
- **Google DeepMind**：https://deepmind.google/discover/blog
- **Meta AI**：https://ai.meta.com/blog
- **特点**：**官方一手技术发布**；大模型、多模态、Agent、技术原理、研究进展；最权威的技术解读。
- **适合**：获取顶级机构**官方技术动态**。

---

### 快速选型指南
| 需求场景 | 优先看 |
|---|---|
| 快速看全球AI热点 | 量子位、机器之心、TechCrunch |
| 深入技术原理/论文 | arXiv、Papers With Code、顶会 |
| 找模型/开源项目 | Hugging Face、GitHub Trending |
| 看行业趋势/商业化 | Gartner、36氪、AI科技评论 |
| 高效聚合、减少信息差 | RadarAI、Future Tools |

---

需要我帮你整理一份**每日10分钟AI资讯追踪清单**，按“早/中/晚”优先级排序，附RSS订阅与关键词设置，让你高效不漏重点吗？










以下是你指定的8个大模型相关主题，在**知乎、B站、YouTube**上的核心资料汇总，按主题分类整理，方便你直接检索学习。

---

### 一、大模型微调——李沐
#### 核心资料
- **B站**：《跟李沐学AI》系列，含大模型微调、LoRA/QLoRA、SFT、RLHF等实战
  - 主页：https://space.bilibili.com/1567748477
  - 关键词：`李沐 大模型微调`、`李沐 LoRA`、`李沐 RLHF`
- **知乎**：李沐专栏《动手学深度学习》及大模型微调技术解析
  - 主页：https://www.zhihu.com/people/mli
  - 关键词：`李沐 后训练`、`李沐 微调`、`李沐 LLaMA`
- **YouTube**：李沐团队大模型训练与微调分享
  - 主页：https://www.youtube.com/@mli666
  - 关键词：`Li Mu LLM fine-tuning`、`Li Mu LoRA`

#### 推荐内容
- 视频：《大模型微调实战：LoRA vs 全参数微调》《RLHF从入门到放弃》
- 文章：《预训练是工程问题，后训练才是技术问题》
- 代码：GitHub https://github.com/mli/ 含微调示例

---

### 二、Prompt工程——吴恩达
#### 核心资料
- **B站**：《ChatGPT Prompt Engineering for Developers》中/英双语全集
  - 中文：https://www.bilibili.com/video/BV16g41177XK
  - 英文：https://www.bilibili.com/video/BV1GY411778N
- **YouTube**：吴恩达官方课程（原版）
  - 链接：https://www.youtube.com/playlist?list=PLkFD6_40KJIxJMR-j5A1mkxK26gh_qg37
- **配套资源**
  - 代码：https://github.com/madroidmaq/ChatGPT-Prompt-Engineering-for-Developers
  - 笔记：掘金《吴恩达Prompt工程课精讲》系列

#### 核心知识点
- 两大黄金法则：**清晰具体指令**、**复杂任务分步思考**
- 实战场景：文本总结、推理、转换、扩展、聊天机器人
- 工具：`PromptTemplate`、`Chain-of-Thought`、结构化输出

---

### 三、大模型应用开发——Andrej Karpathy
#### 核心资料
- **YouTube**：Karpathy官方频道，LLM与应用开发核心课程
  - 主页：https://www.youtube.com/@AndrejKarpathy
  - 系列：`Neural Networks: Zero to Hero`（从零到LLM）
  - 链接：https://www.youtube.com/playlist?list=PLAqhIrjkxbuWI23v9cThsA9GvCAUhRvKZ
- **B站**：Karpathy课程中文搬运与解析
  - 关键词：`Karpathy LLM`、`Karpathy 软件3.0`、`Karpathy Agent`
- **GitHub**：Karpathy开源项目（LLM、nanoGPT、autoresearch）
  - 主页：https://github.com/karpathy

#### 推荐内容
- 视频：《Software 3.0》《The Unreasonable Effectiveness of Recurrent Neural Networks》
- 观点：**提示词即应用**、**Agent十年**、**LLM是操作系统**
- 实战：从零实现GPT、大模型应用架构设计

---

### 四、知识库构建与检索——陈皓
#### 核心资料
- **知乎**：陈皓（左耳朵耗子）专栏，RAG与知识库技术深度解析
  - 主页：https://www.zhihu.com/people/haoel
  - 关键词：`陈皓 RAG`、`陈皓 向量数据库`、`陈皓 检索增强`
- **B站**：陈皓RAG实战与企业级知识库分享
  - 主页：https://space.bilibili.com/233946662
  - 关键词：`陈皓 知识库`、`陈皓 检索优化`
- **GitHub**：陈皓RAG与检索相关开源项目
  - 主页：https://github.com/haoel

#### 推荐内容
- 文章：《RAG技术全解：从原理到工程实践》《企业级知识库构建最佳实践》
- 实战：**文档清洗→语义分段→向量索引→检索问答**全流程
- 工具：Chroma、Pinecone、Milvus、LangChain RAG模块

---

### 五、多模态应用开发——何恺明
#### 核心资料
- **YouTube**：何恺明团队多模态与生成模型研究分享
  - 主页：https://www.youtube.com/results?search_query=Kaiming+He+multimodal
  - 关键词：`Kaiming He MAE`、`Kaiming He JiT`、`Kaiming He diffusion`
- **B站/知乎**：何恺明论文解读与多模态应用实战
  - 关键词：`何恺明 MAE`、`何恺明 JiT`、`何恺明 多模态`
- **论文/代码**
  - MAE：https://github.com/facebookresearch/mae
  - JiT：https://github.com/facebookresearch/jit

#### 推荐内容
- 论文：《Masked Autoencoders Are Scalable Vision Learners》《Back to Basics》
- 技术：**MAE自监督学习**、**JiT扩散模型**、**多模态Transformer**
- 应用：图像生成、视频理解、跨模态检索、AI for Science

---

### 六、大模型部署优化——字节跳动技术团队公开课
#### 核心资料
- **B站**：字节跳动技术团队大模型部署与优化系列公开课
  - 主页：https://space.bilibili.com/628661211（字节跳动技术团队）
  - 关键词：`字节跳动 大模型部署`、`字节跳动 Triton`、`字节跳动 推理优化`
- **知乎**：字节跳动技术博客，大模型部署实战与性能优化
  - 主页：https://www.zhihu.com/org/bytedancetech
  - 关键词：`字节跳动 模型压缩`、`字节跳动 量化`、`字节跳动 分布式推理`
- **技术博客**：https://bytedance.feishu.cn/ 含部署优化深度文章

#### 推荐内容
- 视频：《大模型推理优化：从理论到实践》《Triton-distributed框架详解》
- 技术：**量化（INT4/INT8）**、**模型蒸馏**、**分布式推理**、**虚拟宽度网络**
- 工具：Triton、MATXScript、T-PPO算法

---

### 七、AIGC应用落地——小红书AI开发者实战分享
#### 核心资料
- **小红书**：AI开发者实战、AIGC落地案例、变现方法
  - 关键词：`AI绘画`、`AIGC变现`、`小红书AI工具`、`AI内容创作`
- **B站**：小红书AIGC应用实战教程
  - 关键词：`小红书 AI创作`、`小红书 AIGC变现`、`小红书 AI工具`
- **掘金/知乎**：小红书AIGC技术解析与商业案例
  - 关键词：`小红书 InstanceAssemble`、`小红书 AIGC 算法`、`小红书 AI 商业化`

#### 推荐内容
- 实战：**AI绘画接单**、**AI内容矩阵**、**AI视频生成**、**AI热点卡片**
- 变现：广告植入、知识付费、私域转化、电商带货
- 工具：DeepSeek、Runway Gen-3、N8N+AGI工作流

---

### 八、LangChain框架实操——掘金顶尖开发者
#### 核心资料
- **掘金**：LangChain实战教程、最佳实践、项目案例
  - 关键词：`LangChain 实战`、`LangChain 1.0`、`LangChain RAG`、`LangChain Agent`
  - 推荐作者：`老K`、`码农小胖哥`、`AI前线`
- **B站**：LangChain视频教程、项目演示
  - 关键词：`LangChain 入门`、`LangChain 实战`、`LangChain 项目`
- **GitHub**：掘金开发者LangChain开源项目
  - 关键词：`LangChain 实战项目`、`LangChain RAG 示例`、`LangChain Agent 教程`

#### 推荐内容
- 教程：《LangChain 1.0实战指南》《从零构建RAG应用》《LangChain多智能体协作》
- 核心：**LCEL链式编程**、**PromptTemplate**、**OutputParser**、**向量数据库集成**
- 实战：AI问答、文档总结、智能客服、自动化工作流

---

### 检索建议
1. **B站**：直接搜索关键词+“实战/教程/全集”，优先看播放量高、UP主认证的内容。
2. **YouTube**：优先官方账号（如Andrej Karpathy、吴恩达、李沐），英文原版+中文字幕。
3. **知乎/掘金**：搜索关键词+“深度解析/最佳实践/源码”，关注专栏与高赞回答。
4. **GitHub**：配套代码优先，边看边练，快速掌握实战技能。

需要我把以上资料整理成一份可直接复制的**检索关键词清单**，并按**入门→进阶→实战**排序，方便你快速开始学习吗？