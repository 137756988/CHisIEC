# RAG.py
import os
import openai
import jieba
import jieba.posseg as pseg
import uuid
import asyncio
import nest_asyncio
nest_asyncio.apply()

from typing import Dict, List, Any, Optional
from opencc import OpenCC
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain


# 缓存
from redis import Redis
import pickle
import hashlib

# ragas imports
from ragas import evaluate
from ragas.metrics import (
    faithfulness, 
    answer_relevancy, 
    context_precision,
    context_utilization
)
from ragas.metrics.critique import SUPPORTED_ASPECTS, harmfulness
from ragas.run_config import RunConfig
from ragas.metrics.base import MetricWithLLM, MetricWithEmbeddings

# ragas langchain wrappers
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

# langfuse
from langfuse.callback import CallbackHandler
from langfuse.decorators import observe, langfuse_context
from dataclasses import dataclass
from langfuse import Langfuse
from contextlib import contextmanager

@dataclass
class EvalConfig:
    """评估配置类"""
    enable: bool = False
    trace_name: str = "historical_qa_eval"
    user_id: str = "default_user"
    metrics: List = None

class HistoricalQA:
    def __init__(
        self, 
        graph, 
        model_name="gpt-4-1106-preview", 
        openai_api_key=None,
        langfuse_public_key=None,
        langfuse_secret_key=None,
        eval_config: Optional[EvalConfig] = None
    ):
        """
        初始化问答系统
        Args:
            graph: 从KnowledgeGraphCreator传入的Neo4j图实例
            model_name: 使用的GPT模型名称
            openai_api_key: OpenAI API密钥
            langfuse_public_key: Langfuse公钥
            langfuse_secret_key: Langfuse私钥
            eval_config: 评估配置
        """
        self.graph = graph
        
        # 设置OpenAI API密钥
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        elif "OPENAI_API_KEY" not in os.environ:
            raise ValueError("请提供OpenAI API密钥!")
        
        # 设置Langfuse密钥
        if langfuse_public_key and langfuse_secret_key:
            os.environ["LANGFUSE_PUBLIC_KEY"] = langfuse_public_key
            os.environ["LANGFUSE_SECRET_KEY"] = langfuse_secret_key
        elif eval_config and eval_config.enable:
            if "LANGFUSE_PUBLIC_KEY" not in os.environ or "LANGFUSE_SECRET_KEY" not in os.environ:
                raise ValueError("评估模式需要提供Langfuse的公钥和私钥!")
        
        self._init_custom_dictionary()
        
        # 初始化LLM和Embedding模型
        self.llm = ChatOpenAI(
            model_name=model_name, 
            temperature=0,
            openai_api_key=openai_api_key
        )
        self.embedding_model = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=openai_api_key
        )
        
        # 初始化转换器（简体到繁体）
        self.cc = OpenCC('s2t')
        
        # 初始化提示模板
        self.prompt = ChatPromptTemplate.from_template("""
        你是一位专精于中国古代史的历史学家，请基于提供的史料信息回答问题。

        史料信息：
        {context}

        用户问题：{question}

        回答要求：
        1. 以"根据史料记载"、"据史书记载"、"史料显示"等专业用语开头
        2. 按照时间顺序或逻辑关系组织信息
        3. 如果涉及官职，需要说明具体的官职名称
        4. 如果涉及人物关系，需要明确说明关系类型（如父子、君臣、同僚等）
        5. 如果史料中有具体的历史背景或事件，也请简要说明
        6. 如果信息不完整或存在歧义，请明确指出
        7. 使用准确的历史术语和典故
        8. 回答要简明扼要，突出重点
        """)

        # 评估相关初始化
        self.eval_config = eval_config or EvalConfig()
        if self.eval_config.enable:
            self._init_evaluation()
        
        # 初始化 Langfuse 客户端
        if eval_config and eval_config.enable:
            self.langfuse = Langfuse(
                public_key=langfuse_public_key,
                secret_key=langfuse_secret_key
            )
        
        try:
            self.redis_client = Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=False
            )
            self.redis_client.ping()
            print("Redis缓存服务连接成功")
            self.cache_ttl = 3600  # 缓存过期时间(秒)
        except Exception as e:
            print(f"Redis连接失败: {e}")
            print("系统将在无缓存模式下运行")
            self.redis_client = None

    def _init_custom_dictionary(self):
        """初始化自定义词典"""
        query = """
        MATCH (n)
        RETURN DISTINCT n.name as name, labels(n) as labels
        """
        results = self.graph.query(query)
        
        for result in results:
            if result['name']:
                if '人物' in result['labels']:
                    jieba.add_word(result['name'], freq=1000, tag='nr')
                elif '地点' in result['labels']:
                    jieba.add_word(result['name'], freq=1000, tag='ns')
                elif '官衔' in result['labels']:
                    jieba.add_word(result['name'], freq=1000, tag='nz')
                else:
                    jieba.add_word(result['name'], freq=1000)
        
        # 添加常用词
        common_words = ['官职', '父母', '兄弟', '任职']
        for word in common_words:
            jieba.add_word(word, freq=1000)

    def _init_evaluation(self):
        """初始化评估系统"""
        # 设置默认指标
        if not self.eval_config.metrics:
            self.eval_config.metrics = [
                faithfulness, 
                answer_relevancy, 
                harmfulness,
                # context_precision,  # 可选，但是必须提前提供正确答案
                # context_utilization  # 可选，但是必须提前提供正确答案
            ]
        
        # 创建运行配置
        run_config = RunConfig()
        
        # 初始化指标
        for metric in self.eval_config.metrics:
            if isinstance(metric, MetricWithLLM):
                metric.llm = LangchainLLMWrapper(self.llm)
            if isinstance(metric, MetricWithEmbeddings):
                metric.embeddings = LangchainEmbeddingsWrapper(self.embedding_model)
            if hasattr(metric, 'init'):
                metric.init(run_config)

    async def _score_with_ragas(self, question: str, contexts: List[str], answer: str):
        """异步执行评估指标计算"""
        scores = {}
        for metric in self.eval_config.metrics:
            print(f"计算评估指标: {metric.name}")
            try:
                score_result = metric.ascore({
                    "question": question,
                    "contexts": contexts,
                    "answer": answer
                })
                if asyncio.iscoroutine(score_result):
                    scores[metric.name] = await score_result
                else:
                    scores[metric.name] = score_result
            except Exception as e:
                print(f"评估指标 {metric.name} 计算失败: {str(e)}")
        return scores

    @observe()
    def _get_contexts(self, question: str) -> List[str]:
        """获取相关上下文"""
        names = self._extract_names(question)
        all_results = []
        for name in names:
            results = self._query_graph(name)
            all_results.extend(results)
        
        return [
            f"{r['entity1']}与{r['entity2']}之间的关系是{r['relation']}。具体描述：{r['context']}" 
            for r in all_results
        ]

    @observe()
    def _generate_answer(self, chain, question: str, config: Dict) -> str:
        """生成答案"""
        response = chain.invoke(
            {
                "input": question,
                "question": question
            },
            config=config
        )
        return response["answer"]

    def _answer_with_evaluation(self, chain, question: str, session_id: Optional[str] = None) -> str:
        """带评估的问答处理"""
        # 创建Langfuse处理器
        handler = CallbackHandler(
            trace_name=self.eval_config.trace_name,
            user_id=self.eval_config.user_id,
            session_id=session_id or f"session-{str(uuid.uuid4())}"
        )
        
        # 配置回调
        config = {
            "configurable": {
                "session_id": self.eval_config.user_id
            },
            "callbacks": [handler]
        }
        
        # 执行问答
        response = chain.invoke(
            {
                "input": question,
                "question": question
            },
            config=config
        )
        answer = response["answer"]
        
        return answer

    def answer_question(self, question: str, session_id: Optional[str] = None) -> str:
        """处理问题并生成答案"""
        names = self._extract_names(question)
        if not names:
            return "抱歉，我无法从问题中识别出人名或地名。"
        
        all_results = []
        for name in names:
            results = self._query_graph(name)
            all_results.extend(results)
            
        if not all_results:
            return f"抱歉，我没有找到关于 {', '.join(names)} 的相关历史记载。"
        
        vector_store = self._create_vector_store(all_results)
        rag_chain = self._create_rag_chain(vector_store)
        
        # 根据是否启用评估模式来处理
        if self.eval_config.enable:
            return self._answer_with_evaluation(rag_chain, question, session_id)
        else:
            response = rag_chain.invoke({
                "input": question,
                "question": question
            })
            return response["answer"]

    def _extract_names(self, question: str) -> List[str]:
        """提取问题中的名字并转换为繁体"""
        words = pseg.cut(question)
        names = []
        for word, flag in words:
            if flag in ['nr', 'ns', 'nz', 'n']:
                traditional_word = self.cc.convert(word)
                names.append(traditional_word)
        return names

    def _query_graph(self, name: str) -> List[Dict]:
        """查询图数据库"""
        query = """
        MATCH (n1 {name: $name})-[r]->(n2)
        RETURN 
            n1.name as entity1,
            type(r) as relation,
            n2.name as entity2,
            r.context as context
        UNION
        MATCH (n1)-[r]->(n2 {name: $name})
        RETURN 
            n2.name as entity1,
            type(r) as relation,
            n1.name as entity2,
            r.context as context
        """
        return self.graph.query(query, {'name': name})

    def _create_vector_store(self, results: List[Dict]) -> FAISS:
        """创建或获取向量存储"""
        if not self.redis_client:
            print("⚠️ Redis缓存未启用，将直接创建向量存储")
            return self._create_vector_store_without_cache(results)
        
        # 为查询结果创建唯一标识
        results_str = str(sorted([
            f"{r['entity1']}{r['relation']}{r['entity2']}" 
            for r in results
        ]))
        cache_key = f"vector_store:{hashlib.md5(results_str.encode()).hexdigest()}"
        
        # 尝试从缓存获取
        cached_data = self.redis_client.get(cache_key)
        if cached_data:
            try:
                print("🎯 检测到缓存命中！正在从Redis加载向量存储...")
                vector_data = pickle.loads(cached_data)
                embeddings = vector_data['embeddings']
                texts = vector_data['texts']
                return FAISS.from_texts(
                    texts=texts,
                    embedding=self.embedding_model,
                    metadatas=[{"content": text} for text in texts]
                )
            except Exception as e:
                print(f"❌ 缓存加载失败: {e}")
        else:
            print("🔄 缓存未命中，正在创建新的向量存储...")
        
        # 创建新的向量存储
        texts = [
            f"{r['entity1']}与{r['entity2']}之间的关系是{r['relation']}。具体描述：{r['context']}" 
            for r in results
        ]
        
        docs = CharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        ).create_documents(texts)
        
        vector_store = FAISS.from_documents(docs, self.embedding_model)
        
        # 存储向量数据而不是整个向量存储对象
        try:
            vector_data = {
                'embeddings': [doc.page_content for doc in docs],  # 只存储文本内容
                'texts': [doc.page_content for doc in docs]
            }
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                pickle.dumps(vector_data)
            )
            print("✅ 向量存储已成功缓存")
        except Exception as e:
            print(f"❌ 缓存存储失败: {e}")
        
        return vector_store

    def _create_vector_store_without_cache(self, results: List[Dict]) -> FAISS:
        """不使用缓存创建向量存储"""
        texts = [
            f"{r['entity1']}与{r['entity2']}之间的关系是{r['relation']}。具体描述：{r['context']}" 
            for r in results
        ]
        
        docs = CharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        ).create_documents(texts)
        
        return FAISS.from_documents(docs, self.embedding_model)

    def _create_rag_chain(self, vector_store):
        """创建RAG链"""
        retriever = vector_store.as_retriever(search_kwargs={"k": 100})
        document_chain = create_stuff_documents_chain(
            llm=self.llm,
            prompt=self.prompt,
            document_variable_name="context"
        )
        return create_retrieval_chain(
            retriever=retriever,
            combine_docs_chain=document_chain
        )