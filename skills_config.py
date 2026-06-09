"""
Skill configuration for Senior AI Engineer JD matching.
Tiers reflect importance to the role.
"""

# ── Tier A: Core AI/ML skills (direct JD requirements) ──────────────────────
TIER_A_SKILLS = {
    # Embeddings & retrieval (absolute must-haves per JD)
    "embeddings", "embedding", "sentence-transformers", "sentence transformers",
    "vector search", "vector database", "vector db", "vectordb",
    "semantic search", "dense retrieval", "bi-encoder", "cross-encoder",
    "faiss", "qdrant", "weaviate", "pinecone", "milvus", "opensearch",
    "elasticsearch", "typesense", "pgvector", "chroma", "chromadb",
    # RAG / LLM systems
    "rag", "retrieval augmented generation", "retrieval-augmented",
    "llm", "large language model", "fine-tuning", "fine tuning", "finetuning",
    "rlhf", "instruction tuning", "prompt engineering",
    "transformers", "huggingface", "hugging face",
    "bert", "gpt", "t5", "llama", "mistral", "phi",
    # Ranking & evaluation (explicit JD mention)
    "ranking", "learning to rank", "reranking", "re-ranking",
    "ndcg", "mrr", "map", "precision at k", "recall at k",
    "information retrieval", "ir system",
    "a/b testing", "a/b test", "online evaluation", "offline evaluation",
    # Core ML
    "pytorch", "tensorflow", "jax",
    "nlp", "natural language processing",
    "machine learning", "deep learning", "neural network",
    "python",  # Explicitly called out in JD
}

# ── Tier B: Strong signals (nice-to-haves, significant differentiators) ──────
TIER_B_SKILLS = {
    # Hybrid search
    "bm25", "hybrid search", "sparse retrieval", "tf-idf", "tfidf",
    # ML infra & ops
    "mlops", "ml pipeline", "model deployment", "model serving",
    "triton", "ray", "bentoml", "torchserve", "onnx",
    "docker", "kubernetes", "k8s",
    # APIs & backend for ML
    "fastapi", "flask", "rest api",
    # Data engineering
    "apache spark", "pyspark", "airflow", "kafka", "data pipeline",
    "feature store", "dbt",
    # Cloud platforms
    "aws", "gcp", "azure", "cloud",
    "sagemaker", "vertex ai", "azure ml",
    # Evaluation infra
    "wandb", "mlflow", "experiment tracking", "model monitoring",
    # Related ML domains
    "recommendation systems", "recommender", "collaborative filtering",
    "knowledge graph", "entity extraction", "named entity recognition",
    "text classification", "summarization",
    "computer vision",  # adjacent but shows ML depth
}

# ── Tier C: Adjacent skills (general engineering, some value) ─────────────────
TIER_C_SKILLS = {
    "sql", "postgresql", "mysql", "redis", "mongodb",
    "git", "github", "ci/cd", "devops",
    "java", "scala", "go", "rust", "c++",
    "typescript", "javascript",
    "linux", "bash", "shell scripting",
    "statistics", "probability", "linear algebra", "calculus",
    "pandas", "numpy", "scikit-learn", "sklearn",
    "matplotlib", "data visualization",
    "hadoop", "bigquery", "snowflake", "databricks",
    "system design", "distributed systems",
}

# ── Tier weights ─────────────────────────────────────────────────────────────
TIER_WEIGHTS = {
    "A": 3.0,
    "B": 1.5,
    "C": 0.5,
}

# ── Proficiency multipliers ───────────────────────────────────────────────────
PROFICIENCY_MULT = {
    "expert":       2.0,
    "advanced":     1.5,
    "intermediate": 1.0,
    "beginner":     0.4,
}

# ── Title scoring: keyword → score (0-1) ─────────────────────────────────────
TITLE_SCORES = {
    # Perfect matches
    "ai engineer":           1.00,
    "ml engineer":           1.00,
    "machine learning engineer": 1.00,
    "applied ml":            0.95,
    "applied scientist":     0.90,
    "nlp engineer":          0.95,
    "research engineer":     0.85,
    "senior ai":             1.00,
    "senior ml":             1.00,
    "senior machine learning": 1.00,
    "founding engineer":     0.90,
    "staff ml":              0.90,
    "staff ai":              0.90,
    "principal ml":          0.90,
    "principal ai":          0.90,
    # Good matches
    "data scientist":        0.65,
    "senior data scientist": 0.70,
    "lead data scientist":   0.72,
    "data science":          0.62,
    "deep learning":         0.80,
    "backend engineer":      0.40,   # engineering but not ML-focused
    "software engineer":     0.35,
    "full stack":            0.25,
    "frontend":              0.10,
    "junior ml":             0.35,   # too junior
    "junior ai":             0.35,
}

# ── Summary/headline keyword weights ─────────────────────────────────────────
SUMMARY_KEYWORDS = {
    # High-value AI keywords found in summary/headline text
    "embedding": 3.0, "embeddings": 3.0, "vector": 2.5, "retrieval": 3.0,
    "rag": 3.5, "ranking": 2.5, "reranking": 2.5, "re-ranking": 2.5,
    "llm": 3.0, "language model": 2.5, "fine-tun": 3.0,
    "production": 2.0, "deployed": 2.0, "production ml": 3.5,
    "faiss": 3.0, "qdrant": 3.0, "weaviate": 3.0, "pinecone": 3.0,
    "sentence-transformer": 3.0, "huggingface": 2.5, "pytorch": 2.5,
    "information retrieval": 3.0, "semantic search": 3.0,
    "nlp": 2.0, "natural language": 2.0,
    "startup": 1.5, "early-stage": 1.5, "founding": 1.5,
    "a/b test": 2.0, "ndcg": 3.0, "evaluation": 1.5,
    "research": -0.5,  # slight penalty for pure research framing
    "academic": -1.0,  # penalty for academic-only profiles
}

# ── Industry relevance scores ─────────────────────────────────────────────────
INDUSTRY_SCORES = {
    "artificial intelligence": 1.0,
    "machine learning": 1.0,
    "ai": 1.0,
    "technology": 0.85,
    "software": 0.85,
    "it services": 0.75,
    "saas": 0.85,
    "edtech": 0.75,
    "fintech": 0.75,
    "healthtech": 0.70,
    "e-commerce": 0.65,
    "internet": 0.70,
    "data analytics": 0.80,
    "research": 0.50,   # academia/research = slight concern per JD
    "consulting": 0.55,
    "banking": 0.50,
    "finance": 0.50,
    "manufacturing": 0.30,
    "retail": 0.30,
    "paper products": 0.20,
}

# ── India Tier-1 cities ───────────────────────────────────────────────────────
INDIA_TIER1_CITIES = {
    "pune", "noida", "bengaluru", "bangalore", "hyderabad", "mumbai",
    "delhi", "gurgaon", "gurugram", "chennai", "kolkata", "ahmedabad",
    "new delhi", "navi mumbai", "thane", "greater noida", "faridabad",
}

INDIA_TIER2_CITIES = {
    "jaipur", "chandigarh", "lucknow", "kochi", "indore", "bhubaneswar",
    "coimbatore", "nagpur", "visakhapatnam", "surat", "vadodara",
}

# ── Expected salary range for Senior AI Engineer (rough market rate, INR LPA) ─
SALARY_MIN_EXPECTED = 18  # minimum reasonable ask for a senior role
SALARY_MAX_BUDGET = 60    # rough upper budget for Series A startup

# ── Production ML signals in job description text ────────────────────────────
PRODUCTION_ML_SIGNALS = [
    "production", "deployed", "real-time", "real time", "at scale", "serving",
    "inference", "latency", "throughput", "a/b test", "api", "microservice",
    "pipeline", "batch processing", "streaming", "model monitoring", "mlops",
    "drift", "regression", "rollout", "canary",
]

RESEARCH_ANTI_SIGNALS = [
    "phd thesis", "dissertation", "academic", "research paper", "arxiv",
    "lab", "university research", "research assistant",
]
