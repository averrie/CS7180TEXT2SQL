from spider_agent.agent.models import call_llm

class SQLValidatorAgent:
    def __init__(self, model="gpt-4"):
        self.model = model
    
    def validate_result(self, result, sql_strategy):
        system_prompt = """You are a SQL validation expert. Check:
1. Result validity
2. Potential issues
3. Improvement suggestions"""

        messages = [
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "text", "text": f"""
Strategy: {sql_strategy.get('approach', 'N/A')}
Result: {result}
"""}]}
        ]
        
        status, response = call_llm({
            "model": self.model,
            "messages": messages,
            "temperature": 0.2
        })
        
        return self._parse_validation(response)
    
    def _parse_validation(self, response: str):
        import re
        validation = {}
        
        # 提取关键信息
        validation["is_valid"] = "yes" in re.search(r'(?:valid)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE).group(1).lower()
        
        return validation
