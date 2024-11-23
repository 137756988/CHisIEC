import streamlit as st
from Create_KG import KnowledgeGraphCreator
from RAG import HistoricalQA, EvalConfig
import time
import os
from dotenv import load_dotenv

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
    /* 输入框样式 */
    .stTextInput input {
        background-color: white !important;  /* 默认白色背景 */
        border: 1px solid #e0e3e9;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        height: 40px;  /* 固定高度以确保对齐 */
        line-height: 40px;  /* 文字垂直居中 */
    }
    
    .stTextInput input:focus {
        border-color: #007bff;
        box-shadow: 0 0 0 2px rgba(0,123,255,.25);
    }
    
    /* 按钮容器样式 */
    .button-container {
        display: flex;
        align-items: center;  /* 垂直居中对齐 */
        gap: 1rem;
        height: 40px;  /* 与输入框相同高度 */
    }
    
    /* 清空按钮 */
    .stButton>button {
        height: 40px;  /* 固定高度 */
        padding: 0.5rem 1rem;
        background-color: #f0f2f6;
        border: none;
        border-radius: 10px;
        color: #31333F;
        font-size: 14px;
        line-height: 1;
        margin: 0;  /* 移除默认边距 */
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .stButton>button:hover {
        background-color: #e0e2e6;
    }
    
    /* 确保输入区域和按钮在同一行且对齐 */
    .input-row {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .input-col {
        flex: 1;
    }
    
    .button-col {
        width: auto;
    }
    
    /* 加载状态样式 */
    .stSpinner {
        text-align: center;
        color: #007bff;
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
    }
    
    /* 发送按钮在加载时的样式 */
    .stButton>button:disabled {
        background-color: #e9ecef;
        cursor: not-allowed;
    }
    
    /* 确保加载图标在按钮中居中 */
    .stSpinner > div {
        display: inline-block;
        vertical-align: middle;
    }
    
    /* 加载动画样式 */
    @keyframes spinner {
        to {transform: rotate(360deg);}
    }
    
    .loading-spinner {
        display: inline-block;
        width: 1em;
        height: 1em;
        border: 2px solid #f3f3f3;
        border-top: 2px solid #3498db;
        border-radius: 50%;
        animation: spinner 0.8s linear infinite;
        margin: 0 auto;
    }
    
    /* 发送按钮样式 */
    .send-button {
        width: 100%;
        height: 40px;
        background-color: #007bff;
        color: white;
        border: none;
        border-radius: 10px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
    }
    
    .send-button:hover {
        background-color: #0056b3;
    }
    </style>
""", unsafe_allow_html=True)

# 示例问题
SAMPLE_QUESTIONS = {
    "人物关系类": [
        "遺直的兄弟是谁？",
        "裕的父母是谁？",
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

def initialize_qa_system(eval_mode: bool = False):
    """
    初始化问答系统
    Args:
        eval_mode: 是否启用评估模式
    """
    if 'qa_system' not in st.session_state or st.session_state.get('eval_mode') != eval_mode:
        with st.spinner('正在初始化知识图谱...'):
            creator = KnowledgeGraphCreator(
                neo4j_url="neo4j://localhost:7687/",
                username="neo4j",
                password="12345678"
            )
            creator.connect_to_neo4j()

            # 从环境变量或Streamlit Secrets获取API密钥，或者直接手动输入
            openai_api_key = os.getenv('OPENAI_API_KEY')
            langfuse_public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
            langfuse_secret_key = os.getenv('LANGFUSE_SECRET_KEY')

            if eval_mode:
                if not (langfuse_public_key and langfuse_secret_key):
                    st.error("评估模式需要设置Langfuse密钥！")
                    return
                
                eval_config = EvalConfig(
                    enable=True,
                    trace_name="dissertation_evaluation",
                    user_id="researcher_001"
                )
            else:
                eval_config = None

            qa_system = HistoricalQA(
                graph=creator.graph,
                openai_api_key=openai_api_key,
                langfuse_public_key=langfuse_public_key if eval_mode else None,
                langfuse_secret_key=langfuse_secret_key if eval_mode else None,
                eval_config=eval_config
            )
            
            st.session_state.qa_system = qa_system
            st.session_state.eval_mode = eval_mode
        st.success('知识图谱加载完成！')

def display_chat_history():
    """显示聊天历史"""
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f"**👤 问题：**\n{message['content']}")
        else:
            st.markdown(f"**🤖 助手：**\n{message['content']}")
        st.markdown("---")  # 添加分隔线

def main():
    # 页面标题
    st.title("📚 中国古代史知识问答助手")
    
    # 在侧边栏添加评估模式开关
    with st.sidebar:
        st.title("⚙️ 系统设置")
        eval_mode = st.toggle("启用评估模式", value=False, help="开启后将记录问答质量评估数据")
        if eval_mode:
            st.info("📊 评估模式已启用，系统将记录问答质量数据")
        
        # 添加评估模式说明
        with st.expander("ℹ️ 关于评估模式"):
            st.write("""
            评估模式将启用以下指标：
            - 答案忠实度
            - 答案相关性
            - 有害性检测
            
            评估数据将被记录用于系统优化。
            """)
    
    st.markdown("---")

    # 初始化问答系统
    initialize_qa_system(eval_mode)

    # 创建两列布局
    col1, col2 = st.columns([2, 1])

    with col2:
        st.subheader("💡 示例问题")
        for category, questions in SAMPLE_QUESTIONS.items():
            with st.expander(f"📍 {category}"):
                for question in questions:
                    if st.button(question, key=question):
                        st.session_state.current_question = question
                        st.rerun()

    with col1:
        st.subheader("🤖 对话区域")
        
        # 初始化聊天历史
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

        # 在输入区域之前显示聊天历史
        display_chat_history()
        
        # 输入区域
        col1, col2, col3 = st.columns([5, 1, 1])
        with col1:
            user_input = st.text_input(
                "请输入您的问题：",
                key="user_input",
                value=st.session_state.get('current_question', ''),
                label_visibility="collapsed"
            )

        with col2:
            if st.session_state.get('is_sending', False):
                st.button(
                    "处理中...",
                    key="sending",
                    disabled=True,
                    use_container_width=True
                )
            else:
                send_button = st.button(
                    "发送",
                    key="send",
                    type="primary",
                    use_container_width=True
                )

        with col3:
            clear_button = st.button(
                "🗑️ 清空",
                key="clear",
                help="清空所有对话历史",
                use_container_width=True
            )

        # 处理发送逻辑
        if send_button and user_input:
            try:
                # 获取回答
                session_id = f"session-{len(st.session_state.chat_history)}"
                
                # 添加用户问题到聊天历史
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": user_input
                })
                
                # 获取回答（不需要设置 is_sending 状态）
                answer = st.session_state.qa_system.answer_question(
                    user_input,
                    session_id=session_id
                )
                
                # 添加助手回答到聊天历史
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer
                })
                
                # 清空当前输入
                st.session_state.current_question = ""
                
            except Exception as e:
                st.error(f"处理问题时出错: {str(e)}")
            finally:
                st.rerun()  # 只在最后重新运行一次

        if clear_button:
            st.session_state.chat_history = []
            st.rerun()

if __name__ == "__main__":
    main()