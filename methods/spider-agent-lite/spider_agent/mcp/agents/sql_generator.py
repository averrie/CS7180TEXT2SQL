from spider_agent.agent.models import call_llm

class SQLGeneratorAgent:
    def __init__(self, model="gpt-4"):
        self.model = model
    
    def design_strategy(self, problem_analysis, db_insights, db_type):
        system_prompt = f"""You are a SQL strategy expert. Design:
1. Query approach
2. Query steps
3. Optimization tips"""

        messages = [
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "text", "text": f"""
Problem Analysis:
- Objective: {problem_analysis.get('query_objective', 'N/A')}
- Entities: {', '.join(problem_analysis.get('entities', []))}

Database Insights:
- Tables: {', '.join(db_insights.get('relevant_tables', []))}
- Fields: {', '.join(db_insights.get('key_fields', []))}
"""}]}
        ]
        
        status, response = call_llm({
            "model": self.model,
            "messages": messages,
            "temperature": 0.4
        })
        
        return self._parse_strategy(response)
    
    def _parse_strategy(self, response: str):
        import re
        strategy = {}
        
        # 提取关键信息
        strategy["approach"] = re.search(r'(?:approach)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE).group(1).strip()
        strategy["steps_summary"] = re.search(r'(?:steps)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE).group(1).strip()
        
        return strategy
