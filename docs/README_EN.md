# CHisIEC Knowledge Graph QA System

## Project Introduction
This project builds an ancient Chinese historical literature knowledge graph QA system based on the CHisIEC dataset developed by the Digital Humanities Research Institute of Peking University. The system features:
- Knowledge graph-based intelligent Q&A functionality
- Portable dialogue system architecture
- Built-in system evaluation and optimization

## Features
- Historical literature knowledge retrieval
- Interactive Q&A interface
- Integrated evaluation and optimization modules

## Original Dataset
### NER Data
- Location: ./data/ner/
- Format: CONLL format

### RE Data
- Location: ./data/re/
- Format: JSON format

## Acknowledgments
Thanks to the Digital Humanities Research Institute of Peking University for providing the CHisIEC dataset support.

## Development Timeline
### Phase 1 (7 hours) 20241122
Initial development phase completed in 7 hours due to job hunting pressure.
Time allocation:
- Data feature mining, processing, and knowledge graph construction: 3 hours
- RAG system debugging: 1.5 hours
- Evaluation module implementation: 1 hour
- Frontend interface adjustment: 1.5 hours

### Phase 2 Update (8 hours) 20241124
This update includes three main optimizations:

1. **Data Preprocessing Optimization**
   - Improved entity recognition and relationship extraction preprocessing
   - Added data cleaning and standardization steps
   - Optimized traditional-simplified Chinese conversion

2. **System Cache Optimization**
   - Implemented local caching for vector data
   - Optimized knowledge graph query result caching
   - Reduced computational overhead for re

3. **Knowledge Graph Visualization Interaction**
   - Added knowledge graph zoom control
   - Enhanced node and relationship display
   - Improved graph layout algorithm
   - Enhanced user interaction experience

### Future Optimization
### Phase 3 Updates
1. Establish semantic word segmentation vector library, deepen ancient Chinese semantic network connections, add periodic factors
2. Combine periodic factors with time attributes of relationship edges to enhance knowledge graph construction quality
3. Use instruction data to fine-tune vectorization models

### Phase 4 Updates
1. Attempt to build automated knowledge graph process (based on LightRAG, construct "Auto-CKG method" for ancient Chinese)
2. Establish knowledge graph evaluation metrics and feedback mechanism
3. Develop personalized knowledge guidance through memory mechanisms for educational applications

## Usage Instructions

### Environment Setup
After cloning the project, first install dependencies:
```bash
pip install -r requirements.txt
```

Fill in your open_key and langfuse_key in the .env file.

### 1. Knowledge Graph Construction
![Knowledge Graph Example 1](/docs/images/KG_1.png)
![Knowledge Graph Example 2](/docs/images/KG_2.png)

Built based on four entity nodes (People, Places, Official Titles, Books) (Note: "Books" currently has no data as it's not in the relationship sequence).

Three ways to build or connect to the knowledge graph:

1. **Desktop Version**: Create new project using Neo4j Desktop, import existing database via neo4j.dump

2. **Server Version**: Import decoded dump file to neo4j-linux version

3. **Manual Construction**: Configure port and connection information in Build_KG.py, execute:
```bash
python Build_KG.py
```

Build_KG.py will complete:
- Data processing
- Knowledge graph construction
- Knowledge import
- Test Q&A

### 2. Launch Interface
Execute the following command to start the interactive interface:
```bash
streamlit run app.py
```

[Rest of the content including Langfuse evaluation system, citations, etc.]

![Interface Start](/docs/images/run_1.png)
![Application Interface](/docs/images/run_2.png)
![Application Interface](/docs/images/App_1.png)

This project specially introduces an evaluation process based on the Langfuse platform, which can be enabled through the button on the left side of the system:

![Evaluation Interface](/docs/images/App_2.png)

### Langfuse Evaluation System
![Langfuse Example 1](/docs/images/Langfuse_1.png)
![Langfuse Example 2](/docs/images/Langfuse_2.png)

Advantages of Langfuse as an AI system evaluation platform:
- Visualization of data flow paths
- Monitoring of system performance metrics
- Analysis of token consumption and latency

### Purpose of Introducing Langfuse
1. Optimize data flow paths
2. Improve existing prompt engineering
3. System modularization for future optimization

## Citation
If you use this dataset, please cite the following paper:

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

## Original Project
This project is developed based on the [CHisIEC](https://github.com/tangxuemei1995/CHisIEC) dataset. The original annotation platform was developed by the Digital Humanities Research Institute of Peking University, accessible at: https://wyd.pkudh.net/
