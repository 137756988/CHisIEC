# run.py
from Create_KG import KnowledgeGraphCreator
from RAG import HistoricalQA

def main():
    # 1. 创建知识图谱
    creator = KnowledgeGraphCreator(
        neo4j_url="neo4j://localhost:7687/",  # 根据实际端口修改，若为第一次在本地创建，端口大多为7687
        username="neo4j", # 默认用户名
        password="12345678" # 为创建过程中的初始密码
    )
    
    print("正在处理JSON数据...")
    df = creator.json_to_csv("./data/re")
    
    print("\n正在连接知识图谱数据库...")
    creator.connect_to_neo4j()
    
    print("\n正在清空数据库...")
    creator.clear_database()
    
    print("\n正在导入数据至知识图谱...")
    creator.create_knowledge_graph(df)
    creator.verify_import()

    # 2. 初始化问答系统
    qa_system = HistoricalQA(creator.graph)
    
    # 3. 测试问答
    questions = [
        "裕的父母是谁",
    ]
    
    print("\n开始问答测试:")
    for question in questions:
        print(f"\n问题：{question}")
        answer = qa_system.answer_question(question)
        print(f"回答：{answer}")

if __name__ == "__main__":
    main()