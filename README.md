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
数据特征挖掘、数据处理、知识图谱构建  3小时
RAG系统调试  1.5小时
增加优化评估模块  1小时
前端界面调整  1.5小时


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