from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModel
from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter
import torch
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

if not api_key:
    raise ValueError("Missing OPENROUTER_API_KEY. Did you forget to set it in your .env file?")
        
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,  # Use environment variable instead of hardcoded key
)

# Load the tokenizer and model
model_name = "google/long-t5-tglobal-base"
# model_name = "allenai/longformer-large-4096"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
MAX_TOKENS = 4096   # as required by longformer-large-4096

# Move model to the device (GPU or CPU)
model = model.to(device)


Chunkertokenizer = AutoTokenizer.from_pretrained("nomic-ai/nomic-embed-text-v2-moe")
Chunkermodel = AutoModel.from_pretrained("nomic-ai/nomic-embed-text-v2-moe", trust_remote_code=True)
Chunkermodel = Chunkermodel.to(device)

#this function will be removed as it is duplicate in chunking file. instead when chunking is done in chunksing file, the summariztion function will be evoked inside it passing the chunks that was already created
def chunk_document(doc):

    filename = os.path.basename(doc)
    # --------------------------------------------------------------
    # Extract the data
    # --------------------------------------------------------------
    converter = DocumentConverter()
    result = converter.convert(doc)
    # --------------------------------------------------------------
    # Apply hybrid chunking
    # --------------------------------------------------------------
    chunker = HybridChunker(
        tokenizer=Chunkertokenizer,
        max_tokens=MAX_TOKENS,
        merge_peers=True,  # prevent going over max tokens
    )
    chunk_iter = chunker.chunk(dl_doc=result.document)
    chunks = list(chunk_iter)

    return chunks

def summarize_chunks(chunks):
    messages = [{"role": "system","content": (
            "You are a helpful assistant. Summarize the following user messages "
            "into one descriptive summary. This will be stored in a metadata file for future retrieval."
        )}]
    print(f"length: "+str(len(chunks)))
    for i, chunk in enumerate(chunks):
        chunk_text = chunk.text
        input_text = "summarize: " + chunk_text
        inputs = tokenizer(input_text, return_tensors="pt", max_length=MAX_TOKENS, truncation=True)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        summary_ids = model.generate(inputs["input_ids"], max_length=200)
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        messages.append({"role": "user", "content": summary})
        # print(f"Chunk {i+1} Summary:", summary)
    
    chat5 = client.chat.completions.create(
        model="google/gemini-2.0-flash-exp:free",
        messages=messages,
    )
    reply_message = chat5.choices[0].message
    reply = reply_message.content
    # print(f"\n📦 Final Aggregated Summary:\n ",reply)
    return reply

class Summarization:
    def Summarize(self,document_path):
        filename = os.path.basename(document_path)
        converter = DocumentConverter()
        result = converter.convert(document_path)
        document = result.document
        document_text = "\n".join(
            item.text for item in document.texts if hasattr(item, "text") and item.text
        )

        # print(f"Extracted Text:\n{document_text[:500]}...")  # Optional preview
        # Tokenize the input text
        # Tokenize input with prefix "summarize: " (required for T5-like models)
        input_text = "summarize: " + document_text

        # Tokenize input to count tokens
        input_ids = tokenizer.encode(input_text, truncation=False)
        print(f"Token count: {len(input_ids)}")

        if len(input_ids) > MAX_TOKENS:
            print(f"⚠️ Document exceeds max token limit of {MAX_TOKENS}. Consider chunking.")
            chunks = chunk_document(document_path)
            summary = summarize_chunks(chunks)
            return summary

        inputs = tokenizer(input_text, return_tensors="pt", max_length=MAX_TOKENS, truncation=True)
        # Move input tensors to the GPU (if available)
        inputs = {key: value.to(device) for key, value in inputs.items()}
        # Generate the summary
        summary_ids = model.generate(inputs["input_ids"], max_length=1000, num_beams=4, length_penalty=2.0, early_stopping=True)

        # Decode the generated summary
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)

        messages = [{"role": "system","content": (
                "You are a helpful assistant. Summarize the following user message"
                "into one descriptive summary. This will be stored in a metadata file for future retrieval."
            )}]
        messages.append({"role": "user", "content": summary})
        chat5 = client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free",
            messages=messages,
        )
        reply_message = chat5.choices[0].message
        reply = reply_message.content
        # print(f"\n📦 Final Aggregated Summary:\n ",reply)
        # print("Summary:", summary)
        return summary

# Summarization().Summarize("uploads/Abdelrahman_Zakzouk_Resume.pdf")



