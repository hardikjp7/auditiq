import torch

LLM_MODEL_ID   = "Qwen/Qwen2.5-7B-Instruct"
EMBED_MODEL_ID = "BAAI/bge-small-en-v1.5"
TORCH_DTYPE    = torch.float16
MAX_NEW_TOKENS = 512
TEMPERATURE    = 0.05
TOP_P          = 0.9
TOP_K_RULES    = 3
CHUNK_SIZE     = 500
CHUNK_OVERLAP  = 50

COMPLIANCE_FRAMEWORKS = ["GDPR", "SOX", "Insurance_Compliance"]
