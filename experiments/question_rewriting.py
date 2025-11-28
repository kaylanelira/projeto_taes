"""Question Rewriting seguindo metodologia DART-SQL"""
from loguru import logger
from openai import OpenAI
from core.config import settings

client = OpenAI(api_key=settings.PROJETO_TAES_OPENAI_API_KEY)

# Modelo usado no experimento
MODEL = "gpt-5-nano"

def build_rewriting_prompt(question: str, db_content: str) -> str:
    """
    Constrói prompt de Question Rewriting conforme DART-SQL.
    
    Estrutura:
    1. Instrução
    2. Especificações (exemplos)
    3. Input (questão + conteúdo do banco)
    """
    
    instruction = """Formule consultas de linguagem natural para dados do banco de dados com base nas informações fornecidas. Certifique-se de que as questões reescritas sejam claras, concisas e alinhadas com as especificações dos dados dentro do banco de dados. Se você achar que a frase está clara o suficiente, pode retornar à original sem reescrevê-la."""
    
    specifications = """### Especificações:

1. **Reescrita de ambiguidade**: Alinhe os termos com as especificações dos dados.
   - Exemplo: Se o banco armazena gênero como 'F'/'M', converta "female" para "F".
   - Exemplo: Se o banco usa códigos (0/1), converta termos descritivos para os códigos corretos.

2. **Preservação de informações**: NÃO omita informações-chave ou notas presentes na questão original.
   - Mantenha todos os detalhes, condições e restrições mencionadas.

3. **Evite modificações desnecessárias**: Se a questão já está clara e alinhada com o schema, retorne a original.
   - Não reescreva apenas por reescrever.
"""
    
    user_input = f"""### Questão Original:
{question}

### Conteúdo do Banco de Dados (K=5 primeiros registros):
{db_content}

### Questão Reescrita:"""
    
    full_prompt = f"{instruction}\n\n{specifications}\n\n{user_input}"
    return full_prompt

def rewrite_question(question: str, db_content: str = "") -> str:
    """
    Reescreve pergunta usando LLM com conteúdo do banco.
    
    Args:
        question: Questão original
        db_content: K=5 registros de cada tabela
    
    Returns:
        Questão reescrita
    """
    logger.info(f"Reescrevendo: {question}")
    
    prompt = build_rewriting_prompt(question, db_content)
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=500
        )
        
        rewritten = response.choices[0].message.content.strip()
        logger.info(f"Reescrita: {rewritten}")
        return rewritten
        
    except Exception as e:
        logger.error(f"Erro ao reescrever: {e}")
        # Fallback: retorna original
        return question

def generate_sql_from_question(question: str, db_schema: str) -> str:
    """
    Gera SQL a partir da pergunta (original ou reescrita) + schema.
    Usa o mesmo prompt zero-shot para ambos os baselines.
    
    Args:
        question: Questão (original ou reescrita)
        db_schema: Schema do banco (CREATE TABLE statements)
    
    Returns:
        Query SQL gerada
    """
    logger.info(f"Gerando SQL para: {question}")
    
    # Prompt Zero-Shot padrão (similar ao DAIL-SQL sem exemplos)
    system_prompt = """You are a SQL expert. Generate a SQL query based on the question and database schema provided.

Rules:
- Return ONLY the SQL query, no explanations
- Use proper SQL syntax
- Follow the schema exactly as provided"""

    user_prompt = f"""### Database Schema:
{db_schema}

### Question:
{question}

### SQL Query:"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_completion_tokens=500
        )
        
        sql = response.choices[0].message.content.strip()
        
        # Remove markdown se presente
        if sql.startswith("```"):
            lines = sql.split("\n")
            sql = "\n".join(lines[1:-1]) if len(lines) > 2 else sql
            sql = sql.replace("```sql", "").replace("```", "").strip()
        
        logger.info(f"SQL gerado: {sql[:100]}...")
        return sql
        
    except Exception as e:
        logger.error(f"Erro ao gerar SQL: {e}")
        raise

def generate_sql_with_rewriting(question: str, db_schema: str, db_content: str) -> dict:
    """
    Pipeline RW-Enhanced Zero-Shot:
    1. Reescreve a questão usando conteúdo do banco
    2. Gera SQL da questão reescrita + schema
    
    Returns:
        Dict com questão original, reescrita e SQL gerado
    """
    # Etapa 1: Question Rewriting
    rewritten_question = rewrite_question(question, db_content)
    
    # Etapa 2: SQL Generation da questão reescrita
    sql = generate_sql_from_question(rewritten_question, db_schema)
    
    return {
        "original_question": question,
        "rewritten_question": rewritten_question,
        "generated_sql": sql
    }