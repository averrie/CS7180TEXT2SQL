from spider_agent.agent.models import call_llm

class SQLValidatorAgent:
    def __init__(self, model="gpt-4"):
        self.model = model
    
    def validate_result(self, result, sql_strategy):
        system_prompt = """You are a SQL validation expert. Check if the result:
1. Matches the strategy
2. Is complete
3. Is accurate

Please format your response as follows:
valid: [yes/no]
reason: [explanation]
suggestions: [improvement suggestions]"""

        messages = [
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "text", "text": f"""
SQL Strategy: {sql_strategy}
Result: {result}
"""}]}
        ]
        
        status, response = call_llm({
            "model": self.model,
            "messages": messages,
            "temperature": 0.3
        })
        
        return self._parse_validation(response)
    
    def _parse_validation(self, response: str):
        import re
        validation = {}
        
        # 提取关键信息，添加错误处理
        try:
            # 提取验证结果
            valid_match = re.search(r'(?:valid)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE)
            if valid_match:
                validation["is_valid"] = "yes" in valid_match.group(1).lower()
            else:
                validation["is_valid"] = False
            
            # 提取原因
            reason_match = re.search(r'(?:reason)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE)
            if reason_match:
                validation["reason"] = reason_match.group(1).strip()
            else:
                validation["reason"] = "N/A"
            
            # 提取建议
            suggestions_match = re.search(r'(?:suggestions)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE)
            if suggestions_match:
                suggestions_str = suggestions_match.group(1).strip()
                validation["suggestions"] = [s.strip() for s in re.split(r'[,，、]', suggestions_str)]
            else:
                validation["suggestions"] = ["N/A"]
        except Exception as e:
            # 如果解析失败，提供默认值
            validation = {
                "is_valid": False,
                "reason": "Error parsing validation response",
                "suggestions": ["N/A"]
            }
            print(f"Error parsing validation: {e}")
        
        return validation
