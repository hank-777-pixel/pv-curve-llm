"""
This script is used to train the vector database stored in `/vector_db` that serves the RAG agent.
Currently the raw data used to train the LLM in `/data` is excluded from the open-source repository.

To upload custom data to the vector database, see `agent/data/README.md` for formatting requirements.
After including data in `/data`, run this script to update the vector database.
"""
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
import glob
import shutil
import re

def extract_markdown_metadata(content):
    lines = content.split('\n')
    metadata = {}
    
    for line in lines[:15]:
        line = line.strip()
        if line.startswith('**Source**:'):
            metadata['source'] = line.split(':', 1)[1].strip().replace('**', '')
        elif line.startswith('**Type**:'):
            metadata['doc_type'] = line.split(':', 1)[1].strip().replace('**', '')
        elif line.startswith('**Domain**:'):
            metadata['domain'] = line.split(':', 1)[1].strip().replace('**', '')
        elif line.startswith('**Topic**:'):
            metadata['topic'] = line.split(':', 1)[1].strip().replace('**', '')
        elif line.startswith('**Author**:'):
            metadata['author'] = line.split(':', 1)[1].strip().replace('**', '')
    
    return metadata

def process_markdown_file(file_path):
    filename = os.path.basename(file_path)
    print(f"Processing markdown file: {filename}...")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    metadata = extract_markdown_metadata(content)
    metadata['filename'] = filename
    
    lines = content.split('\n')
    documents = []
    ids = []
    current_section = ""
    current_title = "Introduction"
    chunk_id = 0
    
    for line in lines:
        if line.strip().startswith('**') and ':' in line:
            continue
            
        if re.match(r'^#{1,6}\s', line):
            if current_section.strip():
                doc_metadata = metadata.copy()
                doc_metadata.update({
                    'section': current_title,
                    'chunk_id': f"{filename}_{chunk_id}"
                })
                
                documents.append(Document(
                    page_content=current_section.strip(),
                    metadata=doc_metadata
                ))
                ids.append(f"{filename}_{chunk_id}")
                chunk_id += 1
            
            current_title = re.sub(r'^#{1,6}\s', '', line).strip()
            current_section = ""
        else:
            current_section += line + "\n"
    
    if current_section.strip():
        doc_metadata = metadata.copy()
        doc_metadata.update({
            'section': current_title,
            'chunk_id': f"{filename}_{chunk_id}"
        })
        
        documents.append(Document(
            page_content=current_section.strip(),
            metadata=doc_metadata
        ))
        ids.append(f"{filename}_{chunk_id}")
    
    print(f"✓ Created {len(documents)} chunks from {filename}")
    return documents, ids

def create_vector_database(db_location="./vector_db"):
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    
    add_documents = not os.path.exists(db_location)

    if os.path.exists(db_location):
        print(f"Database already exists at {db_location}")
        overwrite = input("Do you want to overwrite the existing database? (y/n): ").lower().strip()
        
        if overwrite in ['y', 'yes', '']:
            print("Deleting existing database...")
            shutil.rmtree(db_location)
            add_documents = True
            print("Existing database deleted")
        else:
            print("Using existing database")
            add_documents = False

    if add_documents:
        all_documents = []
        all_ids = []

        print("Processing markdown files from ./data/ directory...")
        
        md_files = glob.glob("./data/*.md")
        print(f"Found {len(md_files)} markdown files")
        
        for file_path in md_files:
            docs, ids = process_markdown_file(file_path)
            all_documents.extend(docs)
            all_ids.extend(ids)
        
        if not all_documents:
            print("❌ No valid content found in .md files")
            return False
        
        print(f"Total documents created: {len(all_documents)}")
        
    vector_store = Chroma(
        collection_name="pv-curves",
        persist_directory=db_location,
        embedding_function=embeddings
    )

    if add_documents:
        vector_store.add_documents(documents=all_documents, ids=all_ids)
        print(f"✅ Added {len(all_documents)} documents to vector database")
    
    print("✅ Vector database ready")
    return True

if __name__ == "__main__":
    print("🔄 PV-Curve Database Training Script")
    print("=" * 40)
    
    success = create_vector_database()
    
    if success:
        print("\n🎉 Training completed successfully!")
        print("📊 The database now supports markdown (.md) files only")
        print("📋 Each markdown section becomes one chunk")
    else:
        print("\n❌ Training failed. Please check your data files.")