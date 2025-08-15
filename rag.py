import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings

class RagPipeline:
    def __init__(self):
        self.docs = None
        self.vectorstore = None
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")

    def ingest(self, file_path):
        """Load PDF, split text, and store embeddings."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found")

        loader = PyPDFLoader(file_path)
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.docs = text_splitter.split_documents(documents)

        self.vectorstore = FAISS.from_documents(self.docs, self.embeddings)

    def query(self, question, k=3):
        """Retrieve relevant chunks from PDF and return as context."""
        if not self.vectorstore:
            raise ValueError("No PDF ingested yet. Please upload a PDF first.")

        retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
        docs = retriever.get_relevant_documents(question)

        context = "\n\n".join(doc.page_content for doc in docs)
        return f"Context from document:\n{context}"

