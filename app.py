import os
from flask import Flask, render_template, request, jsonify, session
import PyPDF2
from openai import OpenAI
from dotenv import load_dotenv
from langchain_openai import OpenAI as LangchainOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
import logging

app = Flask(__name__)
app.secret_key = os.urandom(24)

logging.basicConfig(level=logging.INFO)

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Function to read and extract text from the PDF file
def read_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return text

# Load the PDF and extract text for the RAG system
pdf_text = read_pdf('static/greendex_rag_info.pdf')

# Create vector store index
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
texts = text_splitter.split_text(pdf_text)
embeddings = OpenAIEmbeddings()
index = FAISS.from_texts(texts, embeddings)

# Initialize Langchain OpenAI LLM
llm = LangchainOpenAI(temperature=0.5)

def prompt_func(query, n):
    if n == 1:
        prompt = (
            "Greendex is a scoring system that companies fill out a form for. The score is about how environmentally friendly you are. The form that the companies have to fill out have these questions: "
            "1.1 Sirket Adi, 1.2 Sektor, 1.3 Merkez Lokasyonu, 1.4 Calisan Sayisi, 2.1 Birincil Enerji Kaynagi, 2.2 Atik Yonetim Sistemi Varligi, 2.3 Karbon Ayak Izi, 2.4 Su Kullanimi ve koruma uygulamalari, 3.1 Surdurebilirlik Projeleri, 3.2 Cevresel duzenlemelere uyumluluk"
            "Please classify the following query into one of the following categories, taking in consideration what greendex is and how the form is structured: "
            "'General Greendex Info', 'Greendex Form Specific Inquiry', 'Greeting', 'Not Understandable Word/Phrase', 'Other Topic'"
            "Examples for these intents are: 'Greendex General info: Why is Greendex Important?', 'Greendex Form Specific Inquiry: How do I answer question 3.2?', 'Not Understandable Word/Phrase: hfixnsi' and 'Other Topic: What is your favourite car model?'"
            "Your response should ONLY be one of the categories provided, with no additional words. So your output format is only the category from one of the provided ones, with no additional words"
            "Generate answers only and only in Turkish"
            "Your max token limit is 20, generate responses accordingly."
            "Query: " + query
        )
    elif n == 2:
        prompt = (
            "You are a virtual assistant chatbot that is programmed to support users that have questions about 'Greendex Basvuru Formu'."
            "Respond politely to this user input: " + query
        )

    return prompt

def openaiAPI(prompt, max_tokens=20):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an AI user query classifier that is very experienced. You classify user inputs to one of the provided classes accurately."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=max_tokens,
        temperature=0.5,
        top_p=0.9,  # Adjust this to potentially improve coherence
        frequency_penalty=0.0,
        presence_penalty=0.6, # Increased to reduce repetitive text
    )
    return response.choices[0].message.content.strip()

def get_best_matching_text(query, conversation_history):
    logging.info(f"Received query: {query}")
    logging.info(f"Conversation history: {conversation_history}")

    prompt = prompt_func(query, 1)
    category = openaiAPI(prompt)
    logging.info(f"Classified category: {category}")

    result = ""  # Initialize result with a default value

    if category in ["General Greendex Info", "Greendex Form Specific Inquiry"]:
        retriever = index.as_retriever()
        qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)
        
        # Include conversation history in the query
        full_query = f"Conversation history: {conversation_history}\n\nCurrent query: {query}"
        result = qa_chain.run(full_query)
        
        if result == "Bilmiyorum":
            result = "Özür dilerim, aradığınız bilgiye şu anda sahip değilim. Size yardımcı olabileceğim başka bir konu veya soru varsa lütfen bana bildirin."
    elif category == "Greeting":
        prompt2 = prompt_func(query, 2)
        result = openaiAPI(prompt2)
    elif category == "Not Understandable Word/Phrase":
        result = "Söylediğinizi tam olarak anlayamadım, lütfen tekrar sorabilir misiniz? Size en iyi şekilde yardımcı olmak istiyorum."
    elif category == "Other Topic":
        result = "Ne yazık ki bu konuda size yardımcı olamıyorum. Greendex Başvuru Formu ile ilgili herhangi bir sorunuz varsa, lütfen sormaktan çekinmeyin."
    else:
        result = "Üzgünüm, bu kategoriye uygun bir yanıt üretemiyorum. Lütfen sorunuzu farklı bir şekilde sormayı deneyin."

    logging.info(f"Generated result: {result}")
    return result

@app.route('/')
def home():
    if 'conversation_history' not in session:
        session['conversation_history'] = []
    return render_template('index.html', conversation_history=session['conversation_history'])

@app.route('/get_conversation_history')
def get_conversation_history():
    return jsonify(session.get('conversation_history', []))

@app.route('/ask_chatbot', methods=['POST'])
def ask_chatbot():
    data = request.get_json()
    question = data.get("question")

    if 'conversation_history' not in session:
        session['conversation_history'] = []

    session['conversation_history'].append({"role": "user", "content": question})

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in session['conversation_history']])

    answer = get_best_matching_text(question, conversation_history)

    session['conversation_history'].append({"role": "ai", "content": answer})

    if len(session['conversation_history']) > 10:
        session['conversation_history'] = session['conversation_history'][-10:]

    session.modified = True

    return jsonify({
        'answer': answer,
        'conversation_history': session['conversation_history']
    })

if __name__ == '__main__':
    app.run(debug=True)
