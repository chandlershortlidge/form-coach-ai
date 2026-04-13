from langgraph.graph import StateGraph
from typing import TypedDict
import os 
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
if __package__:
    from .chat_memory import get_chat_history
    from .video_processing import analyze_video
else:
    from chat_memory import get_chat_history
    from video_processing import analyze_video
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage
try:
    from langchain_chroma import Chroma
except ModuleNotFoundError:
    from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langgraph.graph import StateGraph, START, END
import re

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=embeddings
)

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")


# Whisper speach to text 
from openai import OpenAI
client = OpenAI()


def clean_classification_text(r):
    create_string = r.content
    response_cleaned = re.sub(r"[^a-zA-Z]", " ", create_string)
    return response_cleaned


router_prompt = ChatPromptTemplate.from_messages([
    ("system", """Your job is to classify user queries into two buckets: 
     - memory
     - memory and vectorstore
     
     *Guidelines*
     Questions regarding exercises, exercise form, or technique: vectorstore & memory
     General question or statements: memory
   
     *Respond to queries with only the correct class*
     Examples: 
     User: how should I grip the bar for bench press?
     Agent: vectorstore & memory

     User: what muscles should I feel during the Romanian dead lift?
     Agent: vectorstore & memory

     User: How's this? 
     Agent: vectorstore & memory

     User: Is this good squat technique? 
     Agent: vectorstore & memory

     User: Was my bar path better?
     Agent: vectorstore & memory

     User: thakns for your help!
     Agent: memory

"""),

     ("human", "{query}")
     
])

llm = ChatOpenAI(model='gpt-5.4-nano')

output_parser = StrOutputParser()

router_chain = router_prompt | llm | output_parser


# Define the state

# the state is a dictionary

class GraphState(TypedDict):

    session_id: int 

    user_query: str

    user_video: str

    classification_image: str

    classified_keywords: str

    top_k_chunks: str

    encoded_images: list[str]

    response: str


workflow = StateGraph(GraphState) 


def video_encoder_node(state: GraphState):
    user_video = state["user_video"]
    user_video_encoded = analyze_video(filepath_in=user_video, frame_count=15, max_seconds=10) # encodes video
    encoded_images = [] # creates a list of encoded images for LLM
    for images in user_video_encoded:
        encoded_images.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{images}"}})
        classification_image = user_video_encoded[0] 
    
    return {"classification_image": classification_image, "encoded_images": encoded_images}


# video classification router NODE

def video_classification_node(state: GraphState):
    classification_image = state["classification_image"]

    router_llm = ChatOpenAI(model='gpt-5.4-nano')

    response = router_llm.invoke([

    {"role": "user", "content": 

    [{"type": "text", "text":  """Your job is to analyze images of users working out for proper form, and list the key checkpoints of their to body evaluate. 
    Give me ONLY the bodypart checkpoints. Do NOT include evaluation suggestions. Do NOT include an intro sentence. 
    Output format should be exactly the example below.
    **Example**
    Overhead press

    1. Feet & base
    2. Glutes & legs
    3. Core & Ribcage
    4. Shoulder position
    5. Bar path
    6. Head & Neck
    7. Lockout position
    8. Tempo and control
    """},


        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{classification_image}"}}
        ]}


    ])
    print(response.text)

    classified_keywords = clean_classification_text(response)

    return {"classified_keywords": classified_keywords, "classification_raw": response.content.strip()}


def vector_db_node(state: GraphState):
    user_query = state["user_query"]
    classified_keywords = state.get("classified_keywords", "")
    retrieval_query = classified_keywords

    if classified_keywords:
        results_user = vectorstore.similarity_search(user_query, k=5)
        results_video = vectorstore.similarity_search(retrieval_query, k=5)
        results = results_user + results_video

    if not classified_keywords: 
        results_user = vectorstore.similarity_search(user_query, k=5)
        results = results_user

    unique_results = []
    seen = set()

    for r in results:
        content = r.page_content
        if content not in seen:
            seen.add(content)
            unique_results.append(r)


    top_k_chunks = "\n".join([r.page_content for r in unique_results])

    return {"top_k_chunks": top_k_chunks}


def response_generator(state: GraphState):
    top_k_chunks = state['top_k_chunks']
    encoded_images = state.get("encoded_images", [])
    session_id = state["session_id"]
    user_query = state["user_query"]
    classified_keywords = state.get("classified_keywords", "")

    response_generator_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a world-class fitness coach. You have extensive experience in helping weight lifters achieve perfect form and maximum hypertrophy. 
    Your job is to analyze images of users lifting weights, offer them advice from your context, and to answer any questions they might have. 
    Inspect each image CLOSELY and carefully. Look for issues realted to form, safety, and unhelpful camera angles.
    Be specific about what you observe and include that in your feedback.
    Do not make any mention to "frames". To the user, you are watching a video.
             
    # BEHAVIOR INSTRUCTIONS
        1. Tone
        - You're eager and excited to help 
        2. How to analyze
            Main fixes
                - Cover all significant issues you observe
            Wrap it up with a follow-up quesion
                - Offer one thing you can do next to help them time 
                    Eg, "If you want, I can also..."


    # ANSWER CONTEXT
    First describe what you observe in the images.         
    Then use the ONLY following context to provide coaching advice:
 
    {top_k_chunks}
    
    If the query or image isn't in context, reply, 'I don't have expert coaching advice for this exercise yet. 
    Currently I can analyze: bench press, overhead press, incline bench press...'"
        
    ---  


    """),
        MessagesPlaceholder(variable_name="history"),
        MessagesPlaceholder(variable_name="input"),
    ])

    user_msg = HumanMessage(content=[
        {"type": "text", "text": user_query},
        *encoded_images,   # <- your list of {"type":"image_url",...}
    ])

    response_generator_llm = ChatOpenAI(model='gpt-5.4',
                    temperature=0.5)

    response_generator_output_parser = StrOutputParser()

    response_generator_chain = response_generator_prompt | response_generator_llm | response_generator_output_parser


    message_history = get_chat_history(session_id)

    fitness_analysis = response_generator_chain.invoke(
        {   "input": [user_msg], 
            'history': message_history.messages, 
            "top_k_chunks": top_k_chunks, 
            "classified_keywords": classified_keywords}
            )


    memory_summary_prompt = ChatPromptTemplate.from_messages([
        ("system", """
    Summarize this fitness analysis for future follow-up questions.
    Keep only facts needed for chat continuity.

    Return:
    - exercise
    - main issues
    - priority fixes
    - important uncertainties
    - concise coaching summary

    Maximum 150 words.
    """),
        ("human", "{fitness_analysis}")
    ])

    memory_summary_llm = ChatOpenAI(model='gpt-5.4-nano')
    memory_summary_output_parser = StrOutputParser()
    memory_summary_chain = memory_summary_prompt | memory_summary_llm | memory_summary_output_parser

    summarized_response = memory_summary_chain.invoke({"fitness_analysis": fitness_analysis})
    message_history.add_user_message(user_query) # save user query to memory
    message_history.add_ai_message(summarized_response) # save summarized response to memory


    return {"response": fitness_analysis} # return full analysis to user
     
    
    

# module level - built once when file loads 
chat_memory_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a world-class fitness coach. 
             You have extensive experience in helping weight lifters achieve perfect form and maximum hypertrophy. 
    Your job is to analyze images of users lifting weights, offer them advice from your context, and to answer any questions they might have. 


    """),
        MessagesPlaceholder(variable_name="history"),
        MessagesPlaceholder(variable_name="input"),
    ])

   
chat_memory_llm = ChatOpenAI(model='gpt-5.4-nano', temperature=0.5)
chat_memory_output_parser = StrOutputParser()

chat_memory_chain = chat_memory_prompt | chat_memory_llm | chat_memory_output_parser

chat_memory_with_history = RunnableWithMessageHistory(
    chat_memory_chain,
    get_session_history=get_chat_history,
    input_messages_key="input",
    history_messages_key="history"

)

# Function: calls only what changes
def chat_memory(state: GraphState):
    user_query = state["user_query"]
    session_id = state["session_id"]

    user_msg = HumanMessage(content=[
        {"type": "text", "text": user_query}
    ])

    response = chat_memory_with_history.invoke(
    {"input": [user_msg]},
    config={"configurable": {"session_id": session_id}}
)
    return {"response": response}
    
    

def route_query(state: GraphState):
    # first check: is there a video?
    if state["user_video"]:
        return "video_encoder"
    
    # no video — ask the LLM which path
    route = router_chain.invoke({"query": state["user_query"]})
    route = route.lower().strip()
    
    if "vectorstore" in route:
        return "vector_db"
    else:
        return "chat_memory"


# conditional edge
workflow.add_conditional_edges(START, route_query)

# add nodes
workflow.add_node("video_encoder", video_encoder_node)
workflow.add_node("video_classification_router", video_classification_node)
workflow.add_node("vector_db", vector_db_node)
workflow.add_node("response_generator", response_generator)
workflow.add_node("chat_memory", chat_memory)



# connect them
workflow.add_edge("chat_memory", END)
workflow.add_edge("video_encoder", "video_classification_router")
workflow.add_edge("video_classification_router", "vector_db")
workflow.add_edge("vector_db", "response_generator")
workflow.add_edge("response_generator", END)

app = workflow.compile()


def transcribe_audio(audio_path):
    audio_file = open(audio_path, "rb") # rb = read binary. audio files are binary data (raw bytes). this tells python gto open as binary instaed of text
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )

    return transcription.text
    
