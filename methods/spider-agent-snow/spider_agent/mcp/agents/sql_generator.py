from spider_agent.agent.models import call_llm

class SQLGeneratorAgent:
    def __init__(self, model="gpt-4"):
        self.model = model
    
    def design_strategy(self, problem_analysis, db_insights, db_type):
        system_prompt = f"""You are a {db_type} SQL expert. Design a query strategy based on:
1. Problem analysis
2. Database insights
3. Best practices

Please format your response as follows:
approach: [query approach]
steps: [step-by-step plan]
joins: [join strategy]
filters: [filter conditions]
aggregations: [aggregation methods]"""

        messages = [
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "text", "text": f"""
Problem Analysis: {problem_analysis}
Database Insights: {db_insights}
"""}]}
        ]
        
        status, response = call_llm({
            "model": self.model,
            "messages": messages,
            "temperature": 0.3
        })
        
        return self._parse_strategy(response)
    
    def _parse_strategy(self, response: str):
        import re
        strategy = {}
        
        # 提取关键信息，添加错误处理
        try:
            # 提取查询方法
            approach_match = re.search(r'(?:approach)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE)
            if approach_match:
                strategy["approach"] = approach_match.group(1).strip()
            else:
                strategy["approach"] = "N/A"
            
            # 提取步骤
            steps_match = re.search(r'(?:steps)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE)
            if steps_match:
                steps_str = steps_match.group(1).strip()
                strategy["steps"] = [s.strip() for s in re.split(r'[,，、]', steps_str)]
            else:
                strategy["steps"] = ["N/A"]
            
            # 提取连接策略
            joins_match = re.search(r'(?:joins)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE)
            if joins_match:
                strategy["joins"] = joins_match.group(1).strip()
            else:
                strategy["joins"] = "N/A"
            
            # 提取过滤条件
            filters_match = re.search(r'(?:filters)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE)
            if filters_match:
                strategy["filters"] = filters_match.group(1).strip()
            else:
                strategy["filters"] = "N/A"
            
            # 提取聚合方法
            aggregations_match = re.search(r'(?:aggregations)[:：]\s*(.*?)(?:\n|$)', response, re.IGNORECASE)
            if aggregations_match:
                strategy["aggregations"] = aggregations_match.group(1).strip()
            else:
                strategy["aggregations"] = "N/A"
        except Exception as e:
            # 如果解析失败，提供默认值
            strategy = {
                "approach": "N/A",
                "steps": ["N/A"],
                "joins": "N/A",
                "filters": "N/A",
                "aggregations": "N/A"
            }
            print(f"Error parsing SQL strategy: {e}")
        
        return strategy
