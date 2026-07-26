import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import PyPDF2
import streamlit as st
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
from markdown import markdown
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

# Fallback chain if the configured model ever gets deprecated/shut down.
DEFAULT_MODEL = "gemini-3.6-flash"
FALLBACK_MODELS = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-2.5-flash"]


def get_api_key() -> str | None:
    """Get the API key from env vars first, then Streamlit secrets (cloud deploys)."""
    key = os.getenv("GOOGLE_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("GOOGLE_API_KEY")
    except Exception:
        return None


@st.cache_resource(show_spinner="Loading embedding model...")
def load_embedding_model() -> SentenceTransformer:
    return SentenceTransformer("all-MiniLM-L6-v2")


class CybercrimeRAGChatbot:
    def __init__(self, api_key: str, model_name: str | None = None):
        self.api_key = api_key
        self.model_name = model_name or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
        self.client = genai.Client(api_key=self.api_key)
        self.embedding_model = load_embedding_model()

        self.documents: List[str] = []
        self.embeddings: np.ndarray | None = None
        self.metadata: List[Dict[str, Any]] = []

    # ---------- Extraction ----------

    def extract_text_from_pdf(self, pdf_file) -> str:
        try:
            reader = PyPDF2.PdfReader(pdf_file)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
            return ""

    def extract_text_from_md(self, md_content: str) -> str:
        try:
            html = markdown(md_content)
            return BeautifulSoup(html, "html.parser").get_text()
        except Exception as e:
            st.error(f"Error processing Markdown: {e}")
            return ""

    # ---------- Chunking ----------

    def chunk_text(self, text: str, chunk_size: int | None = None, overlap: int | None = None) -> List[str]:
        chunk_size = chunk_size or int(os.getenv("CHUNK_SIZE", 250))
        overlap = overlap or int(os.getenv("OVERLAP_SIZE", 40))

        text = text.replace("\n\n", " [PARA_BREAK] ")
        text = re.sub(r"\bSection\s", " [SECTION] Section ", text)
        text = re.sub(r"\bRule\s", " [RULE] Rule ", text)
        text = re.sub(r"\bChapter\s", " [CHAPTER] Chapter ", text)

        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)

        def clean(chunk: str) -> str:
            for tag in ("[SECTION]", "[RULE]", "[CHAPTER]"):
                chunk = chunk.replace(tag, "")
            return chunk.replace("[PARA_BREAK]", "\n").strip()

        chunks: List[str] = []
        current_chunk = ""
        current_word_count = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_words = sentence.split()
            sentence_word_count = len(sentence_words)
            is_section_start = any(tag in sentence for tag in ("[SECTION]", "[RULE]", "[CHAPTER]"))

            if is_section_start and current_chunk and current_word_count > 100:
                chunks.append(clean(current_chunk))
                current_chunk = sentence
                current_word_count = sentence_word_count
            elif current_word_count + sentence_word_count > chunk_size and current_chunk:
                chunks.append(clean(current_chunk))
                overlap_words = current_chunk.split()[-overlap:]
                current_chunk = " ".join(overlap_words) + " " + sentence
                current_word_count = len(overlap_words) + sentence_word_count
            else:
                current_chunk += " " + sentence
                current_word_count += sentence_word_count

        if current_chunk.strip():
            chunks.append(clean(current_chunk))

        clean_chunks = []
        for chunk in chunks:
            words = chunk.split()
            if len(words) < 15:
                continue
            alpha_ratio = len([w for w in words if w.isalpha()]) / len(words)
            if alpha_ratio < 0.6:
                continue
            clean_chunks.append(chunk)

        return clean_chunks

    # ---------- Ingestion ----------

    def process_uploaded_files(self, uploaded_files) -> None:
        self.documents = []
        self.metadata = []

        for uploaded_file in uploaded_files:
            suffix = Path(uploaded_file.name).suffix.lower()
            if suffix == ".pdf":
                text = self.extract_text_from_pdf(uploaded_file)
            elif suffix == ".md":
                text = self.extract_text_from_md(uploaded_file.getvalue().decode("utf-8"))
            else:
                continue

            if not text.strip():
                continue

            for chunk_id, chunk in enumerate(self.chunk_text(text)):
                self.documents.append(chunk)
                self.metadata.append({"file": uploaded_file.name, "chunk_id": chunk_id})

        self._create_embeddings()

    def _create_embeddings(self) -> None:
        if not self.documents:
            self.embeddings = None
            return

        batch_size = 32
        batches = []
        for i in range(0, len(self.documents), batch_size):
            batch = self.documents[i:i + batch_size]
            batches.append(self.embedding_model.encode(batch, show_progress_bar=False))

        self.embeddings = np.vstack(batches)

    # ---------- Retrieval + generation ----------

    def retrieve_relevant_chunks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.documents or self.embeddings is None:
            return []

        query_embedding = self.embedding_model.encode([query])
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        top_indices = np.argsort(similarities)[::-1][:top_k]

        return [
            {
                "content": self.documents[idx],
                "similarity": float(similarities[idx]),
                "metadata": self.metadata[idx],
            }
            for idx in top_indices
        ]

    def generate_response(self, query: str) -> str:
        relevant_chunks = self.retrieve_relevant_chunks(query, top_k=5)

        if not relevant_chunks:
            return "I don't have relevant information to answer your query. Please upload law documents first."

        context = "\n\n".join(
            f"Source: {chunk['metadata']['file']}\n{chunk['content']}" for chunk in relevant_chunks
        )

        prompt = f"""You are an expert and professional lawyer & legal assistant specializing in Indian cybercrime laws. Based on the provided legal documents, answer the user's query comprehensively.

Context from Legal Documents:
{context}

User Query: {query}

Instructions:
1. Provide specific law recommendations (Act names, Section numbers, Rule numbers)
2. Explain which legal provisions apply to this cybercrime case
3. Suggest the appropriate complaint filing procedure and jurisdiction
4. Mention penalties if applicable
5. Be precise and cite specific sections when possible

Provide a comprehensive legal recommendation:"""

        models_to_try = [self.model_name] + [m for m in FALLBACK_MODELS if m != self.model_name]
        last_error = None

        for model in models_to_try:
            try:
                response = self.client.models.generate_content(model=model, contents=prompt)
                if response and response.text:
                    return response.text
                last_error = "Model returned an empty response (possibly blocked by safety filters)."
            except Exception as e:
                last_error = str(e)
                continue

        return f"Error generating response after trying available models: {last_error}"


def initialize_session_state():
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "documents_loaded" not in st.session_state:
        st.session_state.documents_loaded = False


def main():
    app_name = os.getenv("APP_NAME", "CyberLex AI Assistant")
    st.set_page_config(page_title=app_name, page_icon="⚖️", layout="wide")

    initialize_session_state()

    st.title(f"⚖️ {app_name}")

    api_key = get_api_key()
    if not api_key:
        st.error("⚠️ GOOGLE_API_KEY not found.")
        st.info("Add it to a local `.env` file, or set it as a Streamlit secret / environment variable:")
        st.code(
            "GOOGLE_API_KEY=your_google_api_key_here\n"
            "GEMINI_MODEL=gemini-3.6-flash\n"
            "CHUNK_SIZE=250\n"
            "OVERLAP_SIZE=40\n"
            "APP_NAME=CyberLex AI Assistant"
        )
        st.stop()

    if st.session_state.chatbot is None:
        try:
            st.session_state.chatbot = CybercrimeRAGChatbot(api_key=api_key)
        except Exception as e:
            st.error(f"Failed to initialize the assistant: {e}")
            st.stop()

    chatbot = st.session_state.chatbot

    with st.sidebar:
        st.subheader("Settings")
        st.caption(f"Model: `{chatbot.model_name}`")
        if st.session_state.documents_loaded:
            st.caption(f"{len(chatbot.documents)} chunks loaded")
            if st.button("Upload new documents"):
                st.session_state.documents_loaded = False
                chatbot.documents = []
                chatbot.metadata = []
                chatbot.embeddings = None
                st.rerun()

    if not st.session_state.documents_loaded:
        st.header("📁 Upload Documents")
        uploaded_files = st.file_uploader(
            "Upload PDF or Markdown files containing cybercrime laws",
            accept_multiple_files=True,
            type=["pdf", "md"],
        )

        if uploaded_files:
            if st.button("Process Documents", type="primary"):
                with st.spinner("Processing documents..."):
                    chatbot.process_uploaded_files(uploaded_files)

                if not chatbot.documents:
                    st.warning("No usable text was extracted from the uploaded files. Try a different file.")
                else:
                    st.session_state.documents_loaded = True
                    st.success(f"✅ Processed {len(uploaded_files)} files into {len(chatbot.documents)} chunks")
                    time.sleep(1)
                    st.rerun()

        if not uploaded_files:
            st.info("Upload your law documents to get started.")
            with st.expander("📝 Example Queries"):
                for example in [
                    "What law applies to online fraud cases?",
                    "How to file complaint for cyberbullying?",
                    "Which section covers data theft under IT Act?",
                    "What are the penalties for hacking?",
                ]:
                    st.code(example)

        return

    st.header("💬 Ask Questions")

    for query, response in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(query)
        with st.chat_message("assistant"):
            st.write(response)

    user_query = st.chat_input("Ask about cybercrime laws...")

    if user_query:
        with st.chat_message("user"):
            st.write(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Generating response..."):
                response = chatbot.generate_response(user_query)
                st.write(response)

        st.session_state.chat_history.append((user_query, response))

    if st.session_state.chat_history:
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()


if __name__ == "__main__":
    main()
