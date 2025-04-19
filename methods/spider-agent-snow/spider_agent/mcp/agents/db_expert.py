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
5. Optimization tips

Please format your response as follows:
tables: [comma-separated list of tables]
fields: [comma-separated list of fields]
relationships: [comma-separated list of relationships]
joins: [join conditions]
optimization: [optimization tips]"""

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
        
        # 提取关键信息，添加错误处理
        try:
            # 提取相关表
            tables_match = re.search(r'(?:tables)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE)
            if tables_match:
                tables_str = tables_match.group(1).strip()
                analysis["relevant_tables"] = [t.strip() for t in re.split(r'[,，、]', tables_str)]
            else:
                analysis["relevant_tables"] = ["N/A"]
            
            # 提取关键字段
            fields_match = re.search(r'(?:fields)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE)
            if fields_match:
                fields_str = fields_match.group(1).strip()
                analysis["key_fields"] = [f.strip() for f in re.split(r'[,，、]', fields_str)]
            else:
                analysis["key_fields"] = ["N/A"]
        except Exception as e:
            # 如果解析失败，提供默认值
            analysis["relevant_tables"] = ["N/A"]
            analysis["key_fields"] = ["N/A"]
            print(f"Error parsing database analysis: {e}")
        
        return analysis
