"""Carrega dataset Spider e extrai schema + conteúdo do banco"""
import pandas as pd
import json
from loguru import logger
from typing import Dict, List

def load_spider_dataset(split="dev"):
    """Carrega dataset Spider"""
    logger.info(f"Carregando Spider ({split})...")
    df = pd.read_json(f"hf://datasets/aherntech/spider-realistic/{split}.json")
    logger.info(f"{len(df)} exemplos carregados")
    return df

def extract_database_schema(db_schema: Dict) -> str:
    """
    Extrai schema do banco de dados em formato legível.
    Formato: CREATE TABLE statements
    """
    schema_parts = []
    
    if not db_schema:
        return ""
    
    # Extrai informações de tabelas e colunas
    table_names = db_schema.get("table_names_original", [])
    column_names = db_schema.get("column_names_original", [])
    column_types = db_schema.get("column_types", [])
    primary_keys = db_schema.get("primary_keys", [])
    foreign_keys = db_schema.get("foreign_keys", [])
    
    # Organiza colunas por tabela
    tables = {}
    for col_idx, (table_idx, col_name) in enumerate(column_names):
        if table_idx == -1:  # Coluna especial "*"
            continue
        if table_idx not in tables:
            tables[table_idx] = []
        col_type = column_types[col_idx] if col_idx < len(column_types) else "text"
        is_pk = col_idx in primary_keys
        tables[table_idx].append((col_name, col_type, is_pk))
    
    # Gera CREATE TABLE statements
    for table_idx, table_name in enumerate(table_names):
        if table_idx not in tables:
            continue
        
        cols_def = []
        for col_name, col_type, is_pk in tables[table_idx]:
            pk_str = " PRIMARY KEY" if is_pk else ""
            cols_def.append(f"  {col_name} {col_type}{pk_str}")
        
        create_stmt = f"CREATE TABLE {table_name} (\n" + ",\n".join(cols_def) + "\n)"
        schema_parts.append(create_stmt)
    
    return "\n\n".join(schema_parts)

def extract_database_content(db_content: List[Dict], k: int = 5) -> str:
    """
    Extrai K primeiros registros de cada tabela do banco.
    Formato: SELECT * FROM table LIMIT K
    """
    if not db_content:
        return ""
    
    content_parts = []
    
    for table_data in db_content:
        table_name = table_data.get("table_name", "")
        rows = table_data.get("rows", [])
        
        if not rows:
            continue
        
        # Pega K primeiros registros
        sample_rows = rows[:k]
        
        content_parts.append(f"Table: {table_name}")
        for idx, row in enumerate(sample_rows, 1):
            content_parts.append(f"  Row {idx}: {row}")
    
    return "\n".join(content_parts)

def prepare_examples(df, limit=None):
    """
    Prepara exemplos com schema e conteúdo do banco
    """
    if limit:
        df = df.head(limit)
    
    examples = []
    for idx, row in df.iterrows():
        # Extrai schema e conteúdo
        db_schema_dict = row.get("db_schema", {})
        db_content_list = row.get("db_content", [])
        
        schema_str = extract_database_schema(db_schema_dict)
        content_str = extract_database_content(db_content_list, k=5)
        
        examples.append({
            "id": idx,
            "question": row.get("question", ""),
            "query": row.get("query", ""),
            "db_id": row.get("db_id", ""),
            "db_schema": schema_str,
            "db_content": content_str
        })
    
    return examples

if __name__ == "__main__":
    df = load_spider_dataset("dev")
    print("Colunas disponíveis:", df.columns.tolist())
    print("\nPrimeiro exemplo:")
    print(df.iloc[0].to_dict())