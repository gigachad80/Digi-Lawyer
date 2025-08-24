import streamlit as st
import os
from typing import List, Dict, Any
import time
from pathlib import Path
from google import genai
from google.genai import types
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import markdown
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()

class CybercrimeRAGChatbot:
    def __init__(self, api_key: str = None, model_name: str = None):
        """Initialize the RAG chatbot with Google Generative AI (NEW SDK)"""
        # Use .env values with LATEST models as defaults
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.model_name = model_name or os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')  # LATEST MODEL
        
        if not self.api_key:
            raise ValueError("Google API key not found. Set GOOGLE_API_KEY in .env file")

        self.client = genai.Client(api_key=self.api_key)
        
        # Initialize embedding model with caching
        if 'embedding_model' not in st.session_state:
            with st.spinner("Loading embedding model..."):
                st.session_state.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_model = st.session_state.embedding_model
        
        # Storage for documents and embeddings
        self.documents = []
        self.embeddings = []
        self.metadata = []
    
    def extract_text_from_pdf(self, pdf_file) -> str:
        """Extract text from PDF file object"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            st.error(f"Error reading PDF: {str(e)}")
            return ""
    
    def extract_text_from_md(self, md_content: str) -> str:
        """Extract text from Markdown content"""
        try:
            html = markdown.markdown(md_content)
            soup = BeautifulSoup(html, 'html.parser')
            return soup.get_text()
        except Exception as e:
            st.error(f"Error processing Markdown: {str(e)}")
            return ""
    
    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """Split text into overlapping chunks - optimized for legal documents"""
        chunk_size = chunk_size or int(os.getenv('CHUNK_SIZE', 250))
        overlap = overlap or int(os.getenv('OVERLAP_SIZE', 40))
        
        # Legal document preprocessing
        text = text.replace('\n\n', ' [PARA_BREAK] ')
        text = text.replace('Section ', ' [SECTION] Section ')
        text = text.replace('Rule ', ' [RULE] Rule ')
        text = text.replace('Chapter ', ' [CHAPTER] Chapter ')
        
        # Split by sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        
        chunks = []
        current_chunk = ""
        current_word_count = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            sentence_words = sentence.split()
            sentence_word_count = len(sentence_words)
            
            is_section_start = '[SECTION]' in sentence or '[RULE]' in sentence or '[CHAPTER]' in sentence
            
            if is_section_start and current_chunk and current_word_count > 100:
                chunks.append(current_chunk.replace('[SECTION]', '').replace('[RULE]', '').replace('[CHAPTER]', '').replace('[PARA_BREAK]', '\n').strip())
                current_chunk = sentence
                current_word_count = sentence_word_count
            elif current_word_count + sentence_word_count > chunk_size and current_chunk:
                chunks.append(current_chunk.replace('[SECTION]', '').replace('[RULE]', '').replace('[CHAPTER]', '').replace('[PARA_BREAK]', '\n').strip())
                overlap_text = current_chunk.split()[-overlap:]
                current_chunk = ' '.join(overlap_text) + ' ' + sentence
                current_word_count = len(overlap_text) + sentence_word_count
            else:
                current_chunk += ' ' + sentence
                current_word_count += sentence_word_count
        
        if current_chunk.strip():
            chunks.append(current_chunk.replace('[SECTION]', '').replace('[RULE]', '').replace('[CHAPTER]', '').replace('[PARA_BREAK]', '\n').strip())
        
        # Filter and clean chunks
        clean_chunks = []
        for chunk in chunks:
            if len(chunk.split()) < 15:
                continue
            word_ratio = len([w for w in chunk.split() if w.isalpha()]) / len(chunk.split())
            if word_ratio < 0.6:
                continue
            clean_chunks.append(chunk)
        
        return clean_chunks
    
    def process_uploaded_files(self, uploaded_files) -> None:
        """Process uploaded files from Streamlit"""
        self.documents = []
        self.metadata = []
        
        for uploaded_file in uploaded_files:
            text = ""
            if uploaded_file.name.lower().endswith('.pdf'):
                text = self.extract_text_from_pdf(uploaded_file)
            elif uploaded_file.name.lower().endswith('.md'):
                text = self.extract_text_from_md(uploaded_file.getvalue().decode('utf-8'))
            else:
                continue
            
            if text.strip():
                chunks = self.chunk_text(text)
                for chunk_id, chunk in enumerate(chunks):
                    self.documents.append(chunk)
                    self.metadata.append({
                        'file': uploaded_file.name,
                        'chunk_id': chunk_id
                    })
        
        self._create_embeddings()
    
    def _create_embeddings(self) -> None:
        """Create embeddings for all documents"""
        if self.documents:
            batch_size = 32
            embeddings_list = []
            
            for i in range(0, len(self.documents), batch_size):
                batch = self.documents[i:i + batch_size]
                batch_embeddings = self.embedding_model.encode(batch, show_progress_bar=False)
                embeddings_list.append(batch_embeddings)
            
            self.embeddings = np.vstack(embeddings_list)
    
    def retrieve_relevant_chunks(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve most relevant document chunks for the query"""
        if not self.documents:
            return []
        
        query_embedding = self.embedding_model.encode([query])
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                'content': self.documents[idx],
                'similarity': similarities[idx],
                'metadata': self.metadata[idx]
            })
        
        return results
    
    def generate_response(self, query: str) -> str:
        """Generate response using RAG approach with NEW SDK"""
        relevant_chunks = self.retrieve_relevant_chunks(query, top_k=5)
        
        if not relevant_chunks:
            return "I don't have relevant information to answer your query. Please upload law documents first."
        
        context = "\n\n".join([f"Source: {chunk['metadata']['file']}\n{chunk['content']}" 
                              for chunk in relevant_chunks])
        
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
        
        try:

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"

def initialize_session_state():
    """Initialize Streamlit session state"""
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'documents_loaded' not in st.session_state:
        st.session_state.documents_loaded = False

def main():
    st.set_page_config(
        page_title="Cybercrime Law Assistant", 
        page_icon="⚖️",
        layout="wide"
    )
    
    initialize_session_state()
    
    st.title("⚖️ CyberLex AI Assistant")
    
    # Check for .env configuration
    if not os.path.exists('.env'):
        st.error("⚠️ .env file not found!")
        st.info("Create a .env file with the following content:")
        st.code("""GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-2.5-flash
CHUNK_SIZE=250
OVERLAP_SIZE=40""")
        st.stop()
    
    # Initialize chatbot
    try:
        if st.session_state.chatbot is None:
            st.session_state.chatbot = CybercrimeRAGChatbot()
    except ValueError as e:
        st.error(f"Configuration error: {e}")
        st.info("Please check your .env file and ensure GOOGLE_API_KEY is set correctly.")
        st.stop()
    
    # File upload section
    if not st.session_state.documents_loaded:
        st.header("📁 Upload Documents")
        uploaded_files = st.file_uploader(
            "Upload PDF or Markdown files containing cybercrime laws",
            accept_multiple_files=True,
            type=['pdf', 'md']
        )
        
        if uploaded_files:
            if st.button("Process Documents", type="primary"):
                with st.spinner("Processing documents..."):
                    st.session_state.chatbot.process_uploaded_files(uploaded_files)
                    st.session_state.documents_loaded = True
                    st.success(f"✅ Processed {len(uploaded_files)} files into {len(st.session_state.chatbot.documents)} chunks")
                    time.sleep(1)
                    st.rerun()
        
        # Show example queries while waiting
        if not uploaded_files:
            st.info("Upload your law documents to get started.")
            with st.expander("📝 Example Queries"):
                examples = [
                    "What law applies to online fraud cases?",
                    "How to file complaint for cyberbullying?",
                    "Which section covers data theft under IT Act?",
                    "What are the penalties for hacking?"
                ]
                for example in examples:
                    st.code(example)
        
        return
    
    # Chat interface
    st.header("💬 Ask Questions")
    
    # Display chat history
    for query, response in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(query)
        with st.chat_message("assistant"):
            st.write(response)
    
    # Query input
    user_query = st.chat_input("Ask about cybercrime laws...")
    
    if user_query:
        # Add user message to chat
        st.session_state.chat_history.append((user_query, ""))
        
        with st.chat_message("user"):
            st.write(user_query)
        
        with st.chat_message("assistant"):
            with st.spinner("Generating response..."):
                response = st.session_state.chatbot.generate_response(user_query)
                st.write(response)
                
                # Update chat history with response
                st.session_state.chat_history[-1] = (user_query, response)
    
    # Clear chat button
    if st.session_state.chat_history:
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

if __name__ == "__main__":
    main()
