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
5. Expected output

Please format your response as follows:
objective: [main objective]
entities: [comma-separated list of entities]
relationships: [comma-separated list of relationships]
conditions: [query conditions]
output: [expected output]"""

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
        
        # 提取关键信息，添加错误处理
        try:
            # 提取查询目标
            objective_match = re.search(r'(?:objective|goal)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE)
            analysis["query_objective"] = objective_match.group(1).strip() if objective_match else "N/A"
            
            # 提取实体
            entities_match = re.search(r'(?:entities)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE)
            if entities_match:
                entities_str = entities_match.group(1).strip()
                analysis["entities"] = [e.strip() for e in re.split(r'[,，、]', entities_str)]
            else:
                analysis["entities"] = ["N/A"]
            
            # 提取关系
            relationships_match = re.search(r'(?:relationships)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE)
            if relationships_match:
                relationships_str = relationships_match.group(1).strip()
                analysis["relationships"] = [r.strip() for r in re.split(r'[,，、]', relationships_str)]
            else:
                analysis["relationships"] = ["N/A"]
        except Exception as e:
            # 如果解析失败，提供默认值
            analysis["query_objective"] = "N/A"
            analysis["entities"] = ["N/A"]
            analysis["relationships"] = ["N/A"]
            print(f"Error parsing analysis: {e}")
        
        return analysis
