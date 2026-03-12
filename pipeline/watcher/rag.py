# rag.py

import pathway as pw
import os
from dotenv import load_dotenv
from pathway.xpacks.llm.embedders import LiteLLMEmbedder 
from pathway.xpacks.llm import splitters, llms, rerankers  
from pathway.xpacks.llm.vector_store import VectorStoreServer  
from pathway.udfs import DiskCache, ExponentialBackoffRetryStrategy  
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer  
from pathway.xpacks.llm.servers import QASummaryRestServer 

load_dotenv() 

RAG_INPUT_DIR = "./data"
OUTPUT_LOG_PATH = "./rag_output_log.csv"

DATA_PATH = "./data" 
LLM_MODEL = os.getenv("LLM_MODEL") 

class RAGinputSchema(pw.Schema):
        entity_id: str
        name: str
        web_prompt_old: str
        web_prompt_new: str

my_folder = pw.io.fs.read(
    path=DATA_PATH,
    format="json",
    schema = RAGinputSchema,
    with_metadata=True
)

@pw.udf
def make_data(web_prompt_old: str, web_prompt_new: str) -> str:
    # preserve both prompt fields inside data
    return f"Previous Prompt: {web_prompt_old}\nNew Prompt: {web_prompt_new}"

normalized_sources = my_folder.select(
    data=make_data(pw.this.web_prompt_old, pw.this.web_prompt_new),    

    _metadata=pw.this._metadata,

    entity_id=pw.this.entity_id,
    name=pw.this.name,
    web_prompt_old=pw.this.web_prompt_old,
    web_prompt_new=pw.this.web_prompt_new,
)

# Use the normalized table for the sources
sources = [normalized_sources]

app_host = "0.0.0.0"  
app_port = 8000  
text_splitter = splitters.TokenCountSplitter(max_tokens=400)  
embedder = LiteLLMEmbedder(
    model=os.getenv("EMBEDDING_MODEL"), 
    api_key=os.getenv("EMBEDDING_API_KEY"),
) 
# embedder = embedders.SentenceTransformerEmbedder(model="intfloat/e5-small-v2")  
vector_server = VectorStoreServer(  
    *sources,
    embedder=embedder,
    splitter=text_splitter,
    parser=None,
)
model = llms.LiteLLMChat(
        model=LLM_MODEL, 
        retry_strategy=ExponentialBackoffRetryStrategy(max_retries=6),
        cache_strategy=DiskCache(),
        api_key=os.getenv("MISTRAL_KEY"), 
    )

# model = llms.HFPipelineChat(model="LiquidAI/LFM2-350M")  
reranker = rerankers.CrossEncoderReranker(  
    model_name=os.environ["CROSS_ENCODER_MODEL"],
    cache_strategy=DiskCache(),
)

prompt_template = "Answer the question. Context: {context}. Question: {query}"  
rag = BaseRAGQuestionAnswerer(  
    llm=model,
    indexer=vector_server,
    reranker=reranker,
    prompt_template=prompt_template,
)
app = QASummaryRestServer(app_host, app_port, rag)  
app.run(with_cache=True, cache_backend=pw.persistence.Backend.filesystem('./RAGCache'))