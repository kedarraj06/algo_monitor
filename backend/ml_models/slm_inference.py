import os
import gc

SLM_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), 
    "slm", 
    "Phi-3-mini-4k-instruct-q4.gguf"
)

_llm = None

def load_slm():
    global _llm
    if _llm is None:
        from llama_cpp import Llama
        _llm = Llama(
            model_path=SLM_MODEL_PATH,
            n_ctx=2048,
            n_threads=2,
            n_gpu_layers=0,
            verbose=False
        )
    return _llm

def generate_analysis(prompt: str, max_tokens: int = 256) -> str:
    llm = load_slm()
    output = llm(
        prompt,
        max_tokens=max_tokens,
        temperature=0.3,
        stop=["</s>", "Observation:"]
    )
    return output["choices"][0]["text"].strip()

def explain_vulnerability(vuln_type: str, contract_code: str = "") -> str:
    prompt = f"""You are a smart contract security expert. Explain the vulnerability type {vuln_type} in Algorand TEAL smart contracts.
Provide a clear explanation and suggest a fix. Contract code snippet (if any): {contract_code[:500]}"""
    return generate_analysis(prompt, max_tokens=384)

def summarize_contract(teal_code: str) -> str:
    prompt = f"""You are a smart contract security auditor. Analyze this Algorand TEAL contract and provide a security summary:
```
{teal_code[:1500]}
```
Provide: 1) Main purpose, 2) Potential risks, 3) Security recommendations."""
    return generate_analysis(prompt, max_tokens=512)

def suggest_improvements(teal_code: str, risk_level: str) -> str:
    prompt = f"""You are a smart contract security expert. This Algorand TEAL contract has been flagged as "{risk_level}" risk.
Analyze and suggest specific improvements:
```
{teal_code[:1500]}
```"""
    return generate_analysis(prompt, max_tokens=512)

def unload_slm():
    global _llm
    if _llm is not None:
        del _llm
        _llm = None
        gc.collect()