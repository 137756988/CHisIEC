import streamlit as st
from Create_KG import KnowledgeGraphCreator
from RAG import HistoricalQA, EvalConfig
import time
import os
from dotenv import load_dotenv
import streamlit.components.v1 as components
from urllib.parse import quote

# 加载环境变量
load_dotenv()

# 设置页面配置
st.set_page_config(
    page_title="中国古代史知识问答助手",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
    <style>
    /* 页面标题区域 */
    .main .block-container {
        padding-top: 2rem !important;
        max-width: 95% !important;
    }
    
    /* 主标题样式 */
    .main-title {
        padding-bottom: 1rem !important;
        border-bottom: 1px solid #e0e0e0 !important;
        margin-bottom: 2rem !important;
    }
    
    /* 两列布局样式 */
    div[data-testid="column"] {
        padding: 0 1rem !important;
    }
    
    /* 区域标题样式 */
    .section-title {
        display: flex !important;
        align-items: center !important;
        gap: 0.5rem !important;
        margin-bottom: 1rem !important;
        font-size: 1.5rem !important;
        font-weight: 500 !important;
    }
    
    /* 按钮统一样式 */
    .stButton > button {
        width: 100% !important;
        min-height: 40px !important;
        padding: 0.5rem 1rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: nowrap !important;
        font-size: 1rem !important;
    }
    
    /* 发送按钮样式 */
    .stButton > [data-testid="baseButton-primary"] {
        background-color: #FF4B4B !important;
        color: white !important;
        border: none !important;
    }
    
    /* 清空按钮样式 */
    .stButton > button:not([data-testid="baseButton-primary"]) {
        background-color: white !important;
        color: #333333 !important;
        border: 1px solid #d0d0d0 !important;
    }
    
    /* 示例问题区域 */
    div[data-testid="stExpander"] {
        margin: 0.2rem 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 示例问题
SAMPLE_QUESTIONS = {
    "人物关系类": [
        "裕的父母是谁？",
        "遺直的兄弟是谁？",
        "李德裕和元穎的关系如何？"
    ],
    "官职任命类": [
        "谁担任过东牟太守？",
        "輔國將軍是谁担任的？",
        "中散大夫有哪些人担任过？"
    ],
    "历史事件类": [
        "会昌年间发生了什么重要事件？",
        "李德裕在位期间有什么政策？",
        "元穎参与了哪些重要事件？"
    ]
}

def initialize_qa_system():
    """初始化问答系统"""
    creator = KnowledgeGraphCreator(
        neo4j_url="neo4j://localhost:7687/",
        username="neo4j",
        password="12345678"
    )
    creator.connect_to_neo4j()
    return HistoricalQA(creator.graph)

def display_chat_history():
    """显示聊天历史"""
    chat_container = st.container()
    with chat_container:
        for idx, message in enumerate(st.session_state.chat_history):
            if message["role"] == "user":
                st.markdown(f"**👤 问题：**\n{message['content']}")
            else:
                st.markdown(f"**🤖 助手：**\n{message['content']}")
            
            # 如果存在对应的知识图谱，显示在回答下方
            if 'current_graph' in st.session_state and idx == len(st.session_state.chat_history) - 1:
                components.html(st.session_state.current_graph, height=400, scrolling=True)
            
            st.markdown("---")  # 添加分隔线

def create_neo4j_iframe(cypher_query: str, params: dict = None) -> str:
    """创建Neo4j Browser iframe HTML"""
    # 构建完整的Cypher查询URL
    base_url = "http://localhost:7474/browser/"
    
    # 添加参数到查询
    if params:
        param_str = ", ".join([f"{k}: {v}" for k, v in params.items()])
        full_query = f":param {param_str};\n{cypher_query}"
    else:
        full_query = cypher_query
    
    encoded_query = quote(full_query)
    
    # 构建iframe HTML
    iframe_html = f"""
    <iframe
        src="{base_url}?cmd=play&arg={encoded_query}"
        width="100%"
        height="600px"
        frameborder="0"
        allowtransparency="true"
        style="background: white;"
    ></iframe>
    """
    return iframe_html

def main():
    # 初始化session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_question' not in st.session_state:
        st.session_state.current_question = ""
    if 'current_graph' not in st.session_state:
        st.session_state.current_graph = None
    if 'qa_system' not in st.session_state:
        st.session_state.qa_system = initialize_qa_system()
    
    # 侧边栏设置
    with st.sidebar:
        st.title("⚙️ 系统设置")
        
        # 评估模式关
        eval_mode = st.toggle(
            "启用评估模式", 
            value=False,
            help="评估模式是为了帮助开发者在Langfuse后台调整图谱结构和提示词，后期还会设计更多的指标来优化系统"
        )
        
    # 主标题
    st.markdown('<div class="main-title"><h1>📚 中国古代史知识问答助手</h1></div>', unsafe_allow_html=True)

    # 主页面布局：对话区域和示例问题区域
    chat_col, example_col = st.columns([1.5, 1])

    # 对话区域
    with chat_col:
        st.markdown('<div class="section-title">🤖 对话区域</div>', unsafe_allow_html=True)
        display_chat_history()
        
        # 问题输入区域
        user_input = st.text_input(
            "请输入您的问题：",
            key="user_input",
            value=st.session_state.get('current_question', ''),
        )
        
        # 按钮区域
        col1, col2, col3 = st.columns([2, 2, 4])
        with col1:
            send_button = st.button(
                "发送", 
                key="send", 
                type="primary",
                use_container_width=True,
            )
        with col2:
            clear_button = st.button(
                "清空",
                key="clear",
                use_container_width=True,
            )

    # 示例问题区域
    with example_col:
        st.markdown('<div class="section-title">💡 示例问题</div>', unsafe_allow_html=True)
        for category, questions in SAMPLE_QUESTIONS.items():
            with st.expander(category):
                for q in questions:
                    if st.button(q, key=f"btn_{q}"):
                        st.session_state.current_question = q
                        st.rerun()

    # 处理发送逻辑
    if send_button and user_input:
        try:
            with st.spinner('处理中...'):
                # 获取回答
                answer = st.session_state.qa_system.answer_question(user_input)
                
                # 添加到聊天历史
                st.session_state.chat_history.extend([
                    {"role": "user", "content": user_input},
                    {"role": "assistant", "content": answer}
                ])
                
                # 获取并保存知识图谱
                html_content = st.session_state.qa_system.get_visualization_data(user_input)
                st.session_state.current_graph = html_content
                
                # 清空当前输入
                st.session_state.current_question = ""
                
                # 强制重新渲染
                st.rerun()
                
        except Exception as e:
            st.error(f"处理问题时出错: {str(e)}")

    # 清空按钮逻辑
    if clear_button:
        st.session_state.chat_history = []
        st.session_state.current_graph = None
        st.rerun()

if __name__ == "__main__":
    main()