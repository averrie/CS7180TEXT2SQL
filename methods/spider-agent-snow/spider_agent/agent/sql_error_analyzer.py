from typing import Dict, Optional, Any
from dataclasses import dataclass
import json
from .prompts import SNOWFLAKE_ERROR_ANALYSIS_SYSTEM

@dataclass
class SnowflakeErrorAnalysis:
    error_type: str
    root_cause: str
    fix_suggestion: str
    revised_query: Optional[str]
    prevention_tips: str
    requires_cte: bool

class SnowflakeErrorAnalyzer:
    def __init__(self, llm_agent):
        self.llm_agent = llm_agent
        
    def _extract_schema_context(self, schema_info: Dict[str, Any]) -> str:
        """Extract relevant schema information for error analysis."""
        context = []
        if schema_info.get('tables'):
            for table in schema_info['tables']:
                table_info = f"Table: {table['name']}\n"
                table_info += "Columns:\n"
                for col in table.get('columns', []):
                    table_info += f"  - {col['name']} ({col['type']})\n"
                context.append(table_info)
        return "\n".join(context)
    
    def _parse_llm_response(self, response: str) -> SnowflakeErrorAnalysis:
        """Parse LLM response into structured error analysis."""
        try:
            # Clean up the response to ensure it's valid JSON
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            analysis_dict = json.loads(response.strip())
            
            return SnowflakeErrorAnalysis(
                error_type=analysis_dict['error_type'],
                root_cause=analysis_dict['root_cause'],
                fix_suggestion=analysis_dict['fix_suggestion'],
                revised_query=analysis_dict.get('revised_query'),
                prevention_tips=analysis_dict['prevention_tips'],
                requires_cte=analysis_dict.get('requires_cte', False)
            )
        except Exception as e:
            # Fallback for parsing errors
            return SnowflakeErrorAnalysis(
                error_type="Unknown",
                root_cause=f"Failed to parse LLM response: {str(e)}",
                fix_suggestion="Please review the query manually",
                revised_query=None,
                prevention_tips="Ensure proper query structure and syntax",
                requires_cte=False
            )
    
    async def analyze_error(self, 
                          query: str, 
                          error_message: str, 
                          schema_info: Dict[str, Any]) -> SnowflakeErrorAnalysis:
        """
        Analyze Snowflake SQL error and provide structured feedback.
        
        Args:
            query: The original SQL query that caused the error
            error_message: The error message from Snowflake
            schema_info: Dictionary containing relevant schema information
            
        Returns:
            SnowflakeErrorAnalysis object containing the analysis
        """
        schema_context = self._extract_schema_context(schema_info)
        
        # Prepare prompt for LLM
        prompt = SNOWFLAKE_ERROR_ANALYSIS_SYSTEM.format(
            query=query,
            error_message=error_message,
            schema_context=schema_context
        )
        
        # Get analysis from LLM
        response = await self.llm_agent.get_completion(prompt)
        
        # Parse and return structured result
        return self._parse_llm_response(response)
    
    def get_error_summary(self, analysis: SnowflakeErrorAnalysis) -> str:
        """
        Get a human-readable summary of the error analysis.
        """
        summary = f"""
Snowflake SQL Error Analysis:
----------------------------
Error Type: {analysis.error_type}

Root Cause:
{analysis.root_cause}

How to Fix:
{analysis.fix_suggestion}

Prevention Tips:
{analysis.prevention_tips}
"""
        if analysis.revised_query:
            summary += f"\nSuggested Query:\n{analysis.revised_query}"
            
        if analysis.requires_cte:
            summary += "\n\nNote: This query might benefit from using Common Table Expressions (CTEs)."
            
        return summary.strip() 