from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from typing import List
import lancedb
from lancedb.pydantic import LanceModel, Vector
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
import os
from MetaData import MetaData



# ------------------------------
# insuring Gpu is running
# ------------------------------
print("Torch version:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
print("CUDA version:", torch.version.cuda)
print("Device name:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU found")


# ------------------------------
# Setup
# ------------------------------
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
tokenizer = AutoTokenizer.from_pretrained("nomic-ai/nomic-embed-text-v2-moe")
model = AutoModel.from_pretrained("nomic-ai/nomic-embed-text-v2-moe", trust_remote_code=True)
MAX_TOKENS = 512  # as required by nomic-embed-text-v2-moe


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# Move model to the device (GPU or CPU)
model = model.to(device)
# ------------------------------
# LanceDB Setup
# ------------------------------
db = lancedb.connect("data/lancedb")
TABLE_NAME = "docling"

# ------------------------------
# Define Schema
# ------------------------------

# Define a simplified metadata schema
class ChunkMetadata(LanceModel):
    """
    You must order the fields in alphabetical order.
    This is a requirement of the Pydantic implementation.
    """
    filename: str | None
    page_numbers: List[int] | None
    title: str | None


# Define the main Schema
class Chunks(LanceModel):
    text: str
    vector: Vector(768)  # match the actual output of nomic-embed-text-v2-moe
    metadata: ChunkMetadata


# ------------------------------
# Embedding Function
# ------------------------------
def generate_embeddings(text: str):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=MAX_TOKENS)
    inputs = {key: value.to('cuda') for key, value in inputs.items()}  # Move inputs to GPU
    with torch.no_grad():
        model_output = model(**inputs)
    token_embeddings = model_output[0]
    attention_mask = inputs['attention_mask']
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    embeddings = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    return embeddings.squeeze().cpu().numpy()

# ------------------------------
# Chunking And Embedding
# ------------------------------
def process_and_store_document(table,document_path: str):
    filename = os.path.basename(document_path)
    # --------------------------------------------------------------
    # Extract the data
    # --------------------------------------------------------------
    converter = DocumentConverter()
    result = converter.convert(document_path)
    print("done converting")
    # --------------------------------------------------------------
    # Apply hybrid chunking
    # --------------------------------------------------------------
    chunker = HybridChunker(
        tokenizer=tokenizer,
        max_tokens=MAX_TOKENS,
        merge_peers=True,  # prevent going over max tokens
    )
    chunk_iter = chunker.chunk(dl_doc=result.document)
    chunks = list(chunk_iter)
    print("done chunking")
    # ------------------------------
    # for debugging
    # ------------------------------
    # for i, chunk in enumerate(chunks):
    #     print(f"Chunk {i} text length before tokenization: {len(chunk.text)}")
    #     tokens = tokenizer.encode(chunk.text, truncation=False)
    #     print(f"Chunk {i} token count: {len(tokens)}")
    #     if len(tokens) > MAX_TOKENS:
    #         print(f"⚠️ Chunk {i} has {len(tokens)} tokens (too long), truncating...")
    #         chunk.text = tokenizer.decode(tokens[:MAX_TOKENS])  # Truncate to the max token length
    # print(f"length: "+str(len(chunks)))
    # print(chunks[48].text)
    # Get the OpenAI embedding function
    # func = get_registry().get("sentence-transformers").create(name="nomic-embed-text-v2-moe")
    # print(get_registry()._functions)

    # --------------------------------------------------------------
    # Prepare the chunks for the table
    # --------------------------------------------------------------
    processed_chunks = [
        {
            "text": chunk.text,
            "vector": generate_embeddings(chunk.text),  # Generate embeddings for each chunk
            "metadata": {
                "filename": chunk.meta.origin.filename,
                "page_numbers": [
                    page_no
                    for page_no in sorted(
                        set(
                            prov.page_no
                            for item in chunk.meta.doc_items
                            for prov in item.prov
                        )
                    )
                ]
                or None,
                "title": chunk.meta.headings[0] if chunk.meta.headings else None,
            },
        }
        for chunk in chunks
    ]

    table.add(processed_chunks)
    print("done chunking")
    MetaData().metaData_instance(document_path)
    print("done documenting")


def is_document_already_processed(table, filename) -> bool:
    df = table.to_pandas()
    return filename in df['metadata'].apply(lambda m: m.get("filename") if isinstance(m, dict) else None).values



def retrieve_chunks(user_input: str, document_path: str):
    filename = os.path.basename(document_path)

    if TABLE_NAME not in db.table_names():
        table = db.create_table(TABLE_NAME, schema=Chunks, mode="overwrite")
    else:
        try:
            table = db.open_table(TABLE_NAME)
        except Exception as e:
            print(f"Table '{TABLE_NAME}' metadata exists but physical data is missing or corrupted: {e}")
            # Safely drop and recreate
            db.drop_table(TABLE_NAME)
            table = db.create_table(TABLE_NAME, schema=Chunks)

    if not is_document_already_processed(table, filename):
        print(f"Processing new document: {filename}")
        process_and_store_document(table, document_path)
    else:
        print(f"Using cached version of: {filename}")

    # --------------------------------------------------------------
    # Search the table
    # --------------------------------------------------------------

    query_embedding = generate_embeddings(user_input)
    result = table.search(query=query_embedding).limit(9)
    df = result.to_pandas()
    # Filter chunks based on distance
    filtered_chunks = []
    for _, row in df.iterrows():
        if row["_distance"] < 250:
            filtered_chunks.append(row)
        else:
            break  # Stop when distance >= 150

    # Optional: expand display settings
    pd.set_option("display.max_colwidth", None)  # Show full text in cells
    pd.set_option("display.max_rows", None)      # Show all rows
    pd.set_option("display.max_columns", None)   # Show all columns


    # Convert filtered chunks (list of rows) to a DataFrame
    filtered_df = pd.DataFrame(filtered_chunks)
    return filtered_df


class Chunking:
    def LLM_Response(user_input: str,filePath: str):
        if not api_key:
            raise ValueError("Missing OPENROUTER_API_KEY. Did you forget to set it in your .env file?")
        
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,  # Use environment variable instead of hardcoded key
        )
        
        retrived_chunks = retrieve_chunks(user_input,filePath)

        if retrived_chunks.empty:
            print("No relevant chunks found.")
            return "No relevant chunks found."

        context = "\n\n".join(
            f"{row['text']}\n(Source: {row['metadata']['filename']} - Section: {row['metadata']['title']} - p. {row['metadata']['page_numbers']})"
            for _, row in retrived_chunks.iterrows()
        )
        metadata_summary = "\n\n".join(
        f"(Source: {row['metadata'].get('filename', 'Unknown')} - "
        f"Section: {row['metadata'].get('title', 'Untitled')} - "
        f"p. {row['metadata'].get('page_numbers', '?')})"
        for _, row in retrived_chunks.iterrows()
        )
        print(metadata_summary)
        messages = [{"role": "system","content": (
            f"You are a helpful assistant. Answer based only on the following context:\n\n{context}. "
            "If you're unsure or the context doesn't contain the relevant information, say so."
        )}]

        
        messages.append({"role": "user", "content": user_input})

        chat5 = client.chat.completions.create(
                model="google/gemini-2.0-flash-exp:free",
                messages=messages,
            )
        reply_message = chat5.choices[0].message
        reply = reply_message.content
        # messages.append({"role": "assistant", "content": reply})
        print(f"LLM: "+reply)
        return reply

# userInput = input("enter your message")
# Chunking.LLM_Response(userInput,"uploads\2025-02-11 ★SS25-BSc Orientation")


# ----------------------------------------------------------------------
# tempMessages = [
        #     {
        #         "role": "system",
        #         "content": (
        #             "You are a helpful assistant optimizing queries for a semantic vector-based Retrieval-Augmented Generation (RAG) system. "
        #             "Rephrase the following user message into a single, short, semantically rich query that best matches document chunks using cosine similarity. "
        #             "Focus on preserving key terms and concepts. Do not include explanations or return multiple options — only return the rephrased query."
        #         )
        #     },
        #     {"role": "user", "content": user_input}
        # ]
        # chatTemp = client.chat.completions.create(
        #         model="google/gemini-2.0-flash-exp:free",
        #         messages=tempMessages
        #     )
        # tempReply_message = chatTemp.choices[0].message
        # tempReply = tempReply_message.content
        # print(f"look here: "+tempReply)