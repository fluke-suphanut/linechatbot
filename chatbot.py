import warnings
warnings.filterwarnings("ignore")
from flask import Flask, request, send_from_directory
from linebot import LineBotApi, WebhookHandler
from werkzeug.middleware.proxy_fix import ProxyFix
from linebot.models import (MessageEvent,
                            TextMessage,
                            TextSendMessage,
                            LocationSendMessage,
                            ImageSendMessage)
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains import RetrievalQA
import sys
import os
channel_secret = "your_line_channel_secret"
channel_access_token = "your_line_channel_access_token"

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

app = Flask(_name_)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1)
@app.route("/", methods=["GET","POST"])
def home():
    try:
        signature = request.headers["X-Line-Signature"]
        body = request.get_data(as_text=True)
        handler.handle(body, signature)
    except:
        pass
    
    return "Hello Line Chatbot"
class SuppressStdout:
    def __enter__(self):
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr

text_file_path = "text02new.txt"  
loader = TextLoader(text_file_path, encoding="utf-8")
data = loader.load()

from langchain.text_splitter import RecursiveCharacterTextSplitter
text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000,
                                           chunk_overlap=0)
all_splits = text_splitter.split_documents(data)

with SuppressStdout():
    vectorstore = Chroma.from_documents(documents=all_splits,
                                    embedding=GPT4AllEmbeddings())
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text
    print(text)
    if (text=="ประวัติ"):
        text_out = "ภาควิชาวิศวกรรมไฟฟ้า คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม มหาวิทยาลัยศิลปากร ก่อตั้งตั้งแต่ ปีพุทธศักราช 2550 เริ่มต้นพันธกิจการผสมผสานศักยภาพด้านการเรียนการสอนที่ล้ำสมัย มีผู้เชี่ยวชาญงานวิจัยในศาสตร์วิศวกรรมไฟฟ้าที่หลากหลาย ทั้งวิศวกรรมอิเล็กทรอนิกส์ วิศวกรรมคอมพิวเตอร์ วิศวกรรมไฟฟ้า และวิศวกรรมโทรคมนาคม มุ่งทำนุบำรุงศิลปวัฒนธรรม และเสริมสร้างการบริการวิชาการแก่ชุมชนให้สู่ความเป็นอัจฉริยะ เรามีจุดมุ่งหมายชัดเจนในการสร้างบัณฑิตและงานวิจัยให้มีอัตลักษณ์ที่โดดเด่น ภายใต้ สโลแกน ว่า ภาควิชาวิศวกรรมไฟฟ้าแห่งการสร้างสรรค์ เพื่อมุ่งมั่นเป็นผู้นำในการผลิตกำลังคนที่มีสมรรถนะสูงสู่โลกเทคโนโลยีแห่งการสร้างสรรค์และนวัตกรรมอัจฉริยะ"
        line_bot_api.reply_message(event.reply_token,
                                   TextSendMessage(text=text_out))
    if (text=="สถานที่ตั้ง"):
        title = "ภาควิชาวิศวกรรมไฟฟ้า"
        address = "คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม มหาวิทยาลัยศิลปากร"
        lati = 13.820267
        longi = 100.038116
        line_bot_api.reply_message(event.reply_token,
                                   LocationSendMessage(
                                       title=title,
                                       address=address,
                                       latitude=lati,
                                       longitude=longi))
    
    else:
        query=text



        # Prompt
        template = """Use the following pieces of context to answer the question at the end.
        These are your infomation. If you don't know the answer, just say that you don't know, don't try to make up an answer.
        Use three sentences maximum and keep the answer as concise as possible. Answer in Thai only.
        {context}
        Question: {question}
        Helpful Answer:"""
        QA_CHAIN_PROMPT = PromptTemplate(
            input_variables=["context", "question"],
            template=template,
        )

        llm = OllamaLLM(model="llama3.2:3b",
                     callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]))
        qa_chain = RetrievalQA.from_chain_type(
            llm,
            retriever=vectorstore.as_retriever(),
            chain_type_kwargs={"prompt": QA_CHAIN_PROMPT},
        )

        result = qa_chain.invoke({"query": query})
        

        line_bot_api.reply_message(event.reply_token,
                                   TextSendMessage(text=result['result']))

@app.route('/static/<path:path>')
def send_static_content(path):
    return send_from_directory('static', path)        
if _name_ == "_main_":          
    app.run()
