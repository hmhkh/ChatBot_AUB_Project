import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import os

load_dotenv()

# App configs
st.set_page_config(page_title="Streaming bot", page_icon="📄")
st.title("بوت البث")

# Apply RTL styling
st.markdown(
    """
    <style>
    body {
        direction: RTL;
        text-align: right;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Directory to store uploaded TXT files
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def extract_text_from_txt(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as file:
        return file.read()

def find_answer_from_txt(txt_path, query):
    text = extract_text_from_txt(txt_path)
    if query.lower() in text.lower():
        start_index = text.lower().find(query.lower())
        end_index = start_index + 200  # Arbitrary length for demo purposes
        return text[start_index:end_index]
    else:
        return "لم يتم العثور على الإجابة في الملف النصي."

def get_response(user_query, chat_history):
    template = """Use the following pieces of context to answer the question at the end. 
    Always reply in Arabic
    Chat history: {chat_history}
    User question: {user_question}
    Helpful Answer:"""
    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatOpenAI()
    chain = prompt | llm | StrOutputParser()

    # Find answer in TXT files
    txt_files = [os.path.join(UPLOAD_FOLDER, f) for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.txt')]
    for txt_file in txt_files:
        answer = find_answer_from_txt(txt_file, user_query)
        if "لم يتم العثور على الإجابة في الملف النصي." not in answer:
            break

    # Combine TXT answer with language model response
    return chain.stream({
        "chat_history": chat_history,
        "user_question": user_query,
        "txt_answer": answer
    })

# Sidebar components for TXT management
st.sidebar.header("إدارة الملفات النصية")

# Upload TXT
uploaded_file = st.sidebar.file_uploader("تحميل ملف نصي", type="txt")
if uploaded_file is not None:
    with open(os.path.join(UPLOAD_FOLDER, uploaded_file.name), "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success(f"تم تحميل {uploaded_file.name}")

# List TXT files
if st.sidebar.button("عرض الملفات النصية"):
    files = os.listdir(UPLOAD_FOLDER)
    st.sidebar.write(files)

# Delete TXT file
delete_filename = st.sidebar.text_input("أدخل اسم الملف النصي للحذف")
if st.sidebar.button("حذف الملف النصي"):
    if delete_filename:
        file_path = os.path.join(UPLOAD_FOLDER, delete_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            st.sidebar.success(f"تم حذف {delete_filename}")
        else:
            st.sidebar.error(f"لم يتم العثور على {delete_filename}")

# Session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="مرحبًا، أنا روبوت. كيف يمكنني مساعدتك؟"),
    ]

# Conversation
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.write(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.write(message.content)

# User input
user_query = st.chat_input("اكتب رسالتك هنا...")
if user_query is not None and user_query != "":
    st.session_state.chat_history.append(HumanMessage(content=user_query))
    with st.chat_message("Human"):
        st.markdown(user_query)
    with st.chat_message("AI"):
        response = st.write_stream(get_response(user_query, st.session_state.chat_history))
    st.session_state.chat_history.append(AIMessage(content=response))
