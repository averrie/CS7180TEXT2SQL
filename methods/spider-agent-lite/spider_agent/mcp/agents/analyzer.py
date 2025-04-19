from spider_agent.agent.models import call_llm

class ProblemAnalyzerAgent:
    def __init__(self, model="gpt-4"):
        self.model = model
    
    def analyze(self, instruction: str):
        system_prompt = """You are a professional problem analysis expert. Analyze the database query problem and extract:
1. Main objective
2. Key entities
3. Entity relationships
4. Query conditions
5. Expected output"""

        messages = [
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "text", "text": f"Analyze:\n\n{instruction}"}]}
        ]
        
        status, response = call_llm({
            "model": self.model,
            "messages": messages,
            "temperature": 0.2
        })
        
        return self._parse_analysis(response)
    
    def _parse_analysis(self, response: str):
        import re
        analysis = {}
        
        # 提取关键信息
        analysis["query_objective"] = re.search(r'(?:objective|goal)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE).group(1).strip()
        analysis["entities"] = [e.strip() for e in re.split(r'[,，、]', re.search(r'(?:entities)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE).group(1).strip())]
        analysis["relationships"] = [r.strip() for r in re.split(r'[,，、]', re.search(r'(?:relationships)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE).group(1).strip())]
        
        return analysis
