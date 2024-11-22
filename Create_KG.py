import json
import pandas as pd
from pathlib import Path
from langchain_community.graphs import Neo4jGraph
from typing import Dict, List, Optional

class KnowledgeGraphCreator:
    # 实体类型映射和颜色
    ENTITY_LABEL_MAP = {
        'PER': {'label': '人物', 'color': '#FF6B6B'},
        'LOC': {'label': '地点', 'color': '#4ECDC4'},
        'OFI': {'label': '官衔', 'color': '#45B7D1'},
        'BOOK': {'label': '书籍', 'color': '#96CEB4'}
    }

    # 关系类型颜色映射
    RELATION_COLOR_MAP = {
        '任职': '#FFA07A',
        '敌对攻伐': '#FF4500',
        '上下级': '#9370DB',
        '政治奥援': '#20B2AA',
        '管理': '#4682B4',
        '同僚': '#87CEEB',
        '到达': '#DDA0DD',
        '父母': '#F0E68C',
        '驻守': '#98FB98',
        '出生于某地': '#DEB887',
        '兄弟': '#F4A460',
        '别名': '#D8BFD8'
    }

    def __init__(self, neo4j_url: str, username: str, password: str):
        """初始化知识图谱创建器"""
        self.graph = None
        self.neo4j_url = neo4j_url
        self.username = username
        self.password = password

    def extract_triples(self, file_path: Path) -> List[tuple]:
        """从单个RE文件中提取三元组关系及实体类型"""
        triples = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content.startswith('0|'):
                    content = content[2:]
                if not content:
                    return []
                    
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    print(f"无法解析JSON文件: {file_path}")
                    return []
                
                if not isinstance(data, list):
                    data = [data]
                
                for item in data:
                    if isinstance(item, dict) and 'relations' in item:
                        entity_types = {
                            entity['span']: entity['type']
                            for entity in item.get('entities', [])
                        }
                        
                        for relation in item['relations']:
                            head_span = relation.get('head_span', '')
                            tail_span = relation.get('tail_span', '')
                            
                            triple = (
                                head_span,
                                entity_types.get(head_span, ''),
                                relation.get('type', ''),
                                tail_span,
                                entity_types.get(tail_span, ''),
                                item.get('tokens', '')
                            )
                            triples.append(triple)
                            
        except Exception as e:
            print(f"处理文件时出错 {file_path}: {str(e)}")
            return []
            
        return triples

    def json_to_csv(self, data_folder: str) -> pd.DataFrame:
        """将JSON数据处理并转换为CSV"""
        re_folder = Path(data_folder)
        all_triples = []
        
        target_files = [
            'coling_test.json',
            'coling_train.json',
            'coling_train_dev.json'
        ]
        
        for filename in target_files:
            file_path = re_folder / filename
            if file_path.exists():
                print(f"正在处理文件: {filename}")
                triples = self.extract_triples(file_path)
                if triples:
                    all_triples.extend(triples)
            else:
                print(f"文件不存在: {filename}")
        
        if all_triples:
            df = pd.DataFrame(all_triples, columns=[
                'head_entity', 
                'head_entity_label',
                'relation', 
                'tail_entity',
                'tail_entity_label',
                'context'
            ])
            df = df.drop_duplicates(subset=['head_entity', 'relation', 'tail_entity'])
            df.to_csv('triples.csv', index=False)
            print("\n结果已保存至 triples.csv")
            return df
        return pd.DataFrame()

    def connect_to_neo4j(self) -> None:
        """连接到Neo4j数据库"""
        try:
            self.graph = Neo4jGraph(
                url=self.neo4j_url,
                username=self.username,
                password=self.password,
                enhanced_schema=True
            )
            print("成功连接到Neo4j数据库")
        except Exception as e:
            print(f"连接Neo4j数据库失败: {str(e)}")
            raise

    def clear_database(self) -> None:
        """清空数据库"""
        try:
            self.graph.query("MATCH (n) DETACH DELETE n")
            self.graph.query("CALL apoc.schema.assert({},{}); ")
            print("数据库已完全清空")
        except Exception as e:
            print(f"清空数据库时出错: {str(e)}")

    def create_knowledge_graph(self, df: pd.DataFrame) -> None:
        """创建知识图谱"""
        # 创建索引
        for entity_info in self.ENTITY_LABEL_MAP.values():
            label = entity_info['label']
            self.graph.query(f"CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n.name)")
        
        # 创建实体节点
        for _, row in df.iterrows():
            # 头实体
            head_info = self.ENTITY_LABEL_MAP.get(row['head_entity_label'], {'label': 'Entity', 'color': '#CCCCCC'})
            self.graph.query("""
            MERGE (e:{label} {{name: $name}})
            SET e.color = $color
            """.format(label=head_info['label']), 
            {'name': row['head_entity'], 'color': head_info['color']})
            
            # 尾实体
            tail_info = self.ENTITY_LABEL_MAP.get(row['tail_entity_label'], {'label': 'Entity', 'color': '#CCCCCC'})
            self.graph.query("""
            MERGE (e:{label} {{name: $name}})
            SET e.color = $color
            """.format(label=tail_info['label']), 
            {'name': row['tail_entity'], 'color': tail_info['color']})
        
        # 创建关系
        for _, row in df.iterrows():
            head_info = self.ENTITY_LABEL_MAP.get(row['head_entity_label'], {'label': 'Entity'})
            tail_info = self.ENTITY_LABEL_MAP.get(row['tail_entity_label'], {'label': 'Entity'})
            relation_type = row['relation']
            relation_color = self.RELATION_COLOR_MAP.get(relation_type, '#CCCCCC')
            
            self.graph.query(f"""
            MATCH (head:{head_info['label']} {{name: $head_name}})
            MATCH (tail:{tail_info['label']} {{name: $tail_name}})
            MERGE (head)-[r:{relation_type}]->(tail)
            SET r.color = $relation_color,
                r.original_type = $original_type,
                r.context = $context
            """, {
                'head_name': row['head_entity'],
                'tail_name': row['tail_entity'],
                'relation_color': relation_color,
                'original_type': row['relation'],
                'context': row['context']
            })
        print("知识图谱创建完成")

    def verify_import(self) -> None:
        """验证导入结果"""
        print("\n知识图谱节点和关系统计:")
        # 验证各类型节点数量
        for label in ['人物', '地点', '官衔', '书籍']:
            result = self.graph.query(f"""
            MATCH (n:{label}) 
            RETURN count(n) as count
            """)
            print(f"{label}实体数量: {result[0]['count']}")
        
        # 验证关系数量
        result = self.graph.query("""
        MATCH ()-[r]->() 
        RETURN type(r) as type, count(r) as count
        """)
        print("\n关系统计:")
        for r in result:
            print(f"{r['type']}: {r['count']}")