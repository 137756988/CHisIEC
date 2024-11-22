# CHisIEC知识图谱问答系统

## 项目简介
本项目基于北京大学数字人文研究院开发的CHisIEC数据集，构建了一个古代历史文献知识图谱问答系统。该系统具有以下特点：
- 基于知识图谱的智能问答功能
- 可移植的对话系统架构
- 内置系统评估与优化功能

详细的系统使用说明请参考"操作手册.pdf"。

## 功能特点
- 支持历史文献知识检索
- 提供交互式问答界面
- 集成评估与优化模块

## 原始数据集
### NER数据
- 位置：./data/ner/
- 格式：CONLL格式

### RE数据
- 位置：./data/re/
- 格式：JSON格式

## 致谢
感谢北京大学数字人文研究院提供的CHisIEC数据集支持。

## 开发周期
迫于秋招压力，本项目开发周期为7小时，待秋招结束后会继续完善。
时间分配：
- 数据特征挖掘、数据处理、知识图谱构建  3小时
- RAG系统调试  1.5小时
- 增加优化评估模块  1小时
- 前端界面调整  1.5小时

## 使用说明

### 环境配置
克隆项目后，首先安装依赖：
```bash
pip install -r requirements.txt
```

在.env文件中填入您的open_key和langfuse_key。

### 1. 知识图谱搭建
![知识图谱示例1](/pictures/KG_1.png)
![知识图谱示例2](/pictures/KG_2.png)

基于四种实体节点（人物、地点、官衔、书籍）构建（注：由于关系抽取文件中"书籍"不在关系序列中，故"书籍"暂无数据）。

提供三种搭建或链接知识图谱的方式：

1. **桌面版方式**：使用Neo4j Desktop创建新项目，通过自带的neo4j.dump导入已有数据库

2. **服务器版方式**：将dump文件解码后导入neo4j-linux版本

3. **手动构建方式**：配置Build_KG.py中的端口和链接信息，执行：
```bash
python Build_KG.py
```

执行Build_KG.py将依次完成：
- 数据处理
- 知识图谱搭建
- 知识导入
- 测试问答

### 2. 启动界面
执行以下命令启动交互界面：
```bash
streamlit run app.py
```

![应用界面](/pictures/App_1.png)

本项目特别引入了基于langfuse平台的评估流程，可通过系统左侧按钮开启：

![评估界面](/pictures/App_2.png)

### Langfuse评估系统
![Langfuse示例1](/pictures/Langfuse_1.png)
![Langfuse示例2](/pictures/Langfuse_2.png)

Langfuse作为AI系统评估平台的优势：
- 可视化数据流通路径
- 监测系统性能指标
- 分析token消耗和延迟时间

### 引入Langfuse的目的
1. 优化数据流通路径
2. 优化现有的提示词工程
3. 系统模块化，便于后续优化

### 后续优化方向
1. 使用指令数据微调向量化模型
2. 建立知识图谱评价指标和反馈机制
3. 优化向量库缓存机制
4. 通过记忆机制制定个性化知识引导

## 引用
如果您使用了本数据集，请引用以下论文：
```
@inproceedings{tang-etal-2024-chisiec-information,
    title = "{CH}is{IEC}: An Information Extraction Corpus for {A}ncient {C}hinese History",
    author = "Tang, Xuemei  and
      Su, Qi  and
      Wang, Jun  and
      Deng, Zekun",
    booktitle = "Proceedings of the 2024 Joint International Conference on Computational Linguistics, Language Resources and Evaluation (LREC-COLING 2024)",
    month = may,
    year = "2024",
    pages = "3192--3202"
}
```

## 原始项目
本项目基于[CHisIEC](https://github.com/tangxuemei1995/CHisIEC)数据集开发。原始标注平台由北京大学数字人文研究院开发，访问地址：https://wyd.pkudh.net/