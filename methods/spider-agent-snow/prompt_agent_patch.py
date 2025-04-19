# prompt_agent_patch.py
import os
import re
import json

def apply_prompt_agent_patch():
    """
    Patches the PromptAgent class to handle compressed table schemas
    """
    try:
        # Import the PromptAgent class
        from spider_agent.agent.agents import PromptAgent
        
        # Store the original set_env_and_task method
        original_set_env_and_task = PromptAgent.set_env_and_task
        
        # Define the new method that adds compressed table handling
        def set_env_and_task_with_compression(self, env):
            """Enhanced set_env_and_task that handles compressed tables"""
            # Initialize compression attributes
            self.compressed_tables = {}
            self.use_compressed_schema = False
            
            # Call the original method first
            original_set_env_and_task(self, env)
            
            # Try to find the schema directory
            db_schema_path = None
            if hasattr(env, 'task_config') and 'instance_id' in env.task_config:
                instance_id = env.task_config['instance_id']
                # Look for compressed_reference.json in possible schema locations
                possible_paths = [
                    os.path.join(self.work_dir, instance_id),
                    os.path.join(self.work_dir, env.task_config.get('db_id', '')),
                ]
                
                for path in possible_paths:
                    compressed_ref_path = os.path.join(path, 'compressed_reference.json')
                    if os.path.exists(compressed_ref_path):
                        db_schema_path = path
                        break
            
            if db_schema_path:
                compressed_ref_path = os.path.join(db_schema_path, 'compressed_reference.json')
                if os.path.exists(compressed_ref_path):
                    try:
                        with open(compressed_ref_path, 'r') as f:
                            self.compressed_tables = json.load(f)
                        self.use_compressed_schema = True
                        print(f"Found compressed schema reference in {db_schema_path}, enabling compressed table support")
                        
                        # Update system message to include compression instructions
                        compression_note = """
# Table Compression Note #
Some tables with similar structures that differ only by date have been compressed.
These are indicated as TABLE_NAME_[DATE] in the schema overview.
When writing queries, replace [DATE] with a specific date from the available_dates listed.
For example, instead of using GA_SESSIONS_[DATE], use GA_SESSIONS_20160801 (or another date from the available dates).
The available dates for compressed tables are provided in the schema information.
"""
                        # Add compression note to system message
                        system_msg = self.system_message
                        
                        # Check if Tips section exists
                        if "# Tips #" in system_msg:
                            # Insert compression note after the Tips section
                            system_msg = system_msg.replace("# Tips #", "# Tips #" + compression_note)
                        else:
                            # Add at the end if Tips section not found
                            system_msg += "\n" + compression_note
                        
                        self.system_message = system_msg
                        
                        # Update the history messages with the new system message
                        if self.history_messages and self.history_messages[0]['role'] == 'system':
                            if isinstance(self.history_messages[0]['content'], list) and len(self.history_messages[0]['content']) > 0:
                                self.history_messages[0]['content'][0]['text'] = self.system_message
                            elif isinstance(self.history_messages[0]['content'], str):
                                self.history_messages[0]['content'] = self.system_message
                        
                    except Exception as e:
                        print(f"Error loading compressed reference: {e}")
                        self.compressed_tables = {}
                        self.use_compressed_schema = False
        
        # Define the decompression method
        def decompress_sql_query(self, sql_query):
            """
            Replace compressed table references in SQL query with actual table names
            """
            if not hasattr(self, 'use_compressed_schema') or not self.use_compressed_schema or not sql_query:
                return sql_query
            
            # Find compressed table patterns in the query
            for base_name, info in self.compressed_tables.items():
                compressed_name = info.get('compressed_name', f"{base_name}_[DATE]")
                
                # Pattern for compressed table name with [DATE]
                pattern = f"{base_name}_\\[DATE\\]"
                
                # Check if this pattern exists in the query
                if re.search(pattern, sql_query, re.IGNORECASE) or compressed_name in sql_query:
                    # Choose the first available date if there are any
                    available_dates = info.get('available_dates', [])
                    actual_tables = info.get('actual_tables', [])
                    
                    if available_dates and actual_tables:
                        # Use first date/table by default
                        first_date = available_dates[0]
                        actual_table = actual_tables[0]
                        
                        # Replace in the query
                        sql_query = re.sub(pattern, actual_table, sql_query, flags=re.IGNORECASE)
                        sql_query = sql_query.replace(compressed_name, actual_table)
                        print(f"Decompressing table reference: {compressed_name} -> {actual_table}")
            
            return sql_query
        
        # Store the original parse_action method
        original_parse_action = PromptAgent.parse_action
        
        # Define the new method that adds SQL decompression
        def parse_action_with_decompression(self, output):
            """Enhanced parse_action that decompresses SQL queries"""
            # Call the original method first
            action = original_parse_action(self, output)
            
            # Apply decompression for SQL queries
            if action is not None and hasattr(action, 'sql_query') and hasattr(self, 'use_compressed_schema') and self.use_compressed_schema:
                action.sql_query = self.decompress_sql_query(action.sql_query)
            
            return action
        
        # Replace the original methods with the enhanced ones
        PromptAgent.set_env_and_task = set_env_and_task_with_compression
        PromptAgent.decompress_sql_query = decompress_sql_query
        PromptAgent.parse_action = parse_action_with_decompression
        
        print("PromptAgent patched to handle compressed tables")
        return True
    except Exception as e:
        print(f"Failed to patch PromptAgent: {e}")
        return False