from spider_agent.agent.models import call_llm

class DatabaseExpertAgent:
    def __init__(self, model="gpt-4"):
        self.model = model
    
    def analyze_database(self, entities, relationships, db_type):
        system_prompt = f"""You are a {db_type} database expert. Analyze:
1. Relevant tables
2. Key fields
3. Table relationships
4. Join conditions
5. Optimization tips"""

        messages = [
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "text", "text": f"""
Entities: {', '.join(entities)}
Relationships: {', '.join(relationships)}
"""}]}
        ]
        
        status, response = call_llm({
            "model": self.model,
            "messages": messages,
            "temperature": 0.3
        })
        
        return self._parse_db_analysis(response)
    
    def _parse_db_analysis(self, response: str):
        import re
        analysis = {}
        
        # 提取关键信息
        analysis["relevant_tables"] = [t.strip() for t in re.split(r'[,，、]', re.search(r'(?:tables)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE).group(1).strip())]
        analysis["key_fields"] = [f.strip() for f in re.split(r'[,，、]', re.search(r'(?:fields)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE).group(1).strip())]
        
        return analysis
