# utils/build_vectorstore.py
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings

DATA_PATH = "./data/raw"
DB_PATH = "./vectorstore/chroma"

def build_vectorstore():
    print("🧠 Construction de la base vectorielle...")
    loader = DirectoryLoader(DATA_PATH, glob="**/*.txt", loader_cls=TextLoader)
    docs = loader.load()

    embedding = HuggingFaceEmbeddings(model_name="embaas/sentence-transformers-multilingual-e5-base")

    vectordb = Chroma.from_documents(
        documents=docs,
        embedding=embedding,
        persist_directory=DB_PATH
    )
    vectordb.persist()
    print(f"✅ Base construite et sauvegardée dans {DB_PATH}")
    return vectordb

if __name__ == "__main__":
    build_vectorstore()