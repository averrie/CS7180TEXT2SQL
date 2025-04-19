import os
import re
import pandas as pd
import json
import shutil
import argparse

def find_schema_directories(base_dir):
    """Find all directories containing DDL.csv files"""
    schema_dirs = []
    
    for root, dirs, files in os.walk(base_dir):
        if 'DDL.csv' in files:
            schema_dirs.append(root)
    
    return schema_dirs

def compress_tables_in_directory(schema_dir, create_backup=True):
    """Compress tables in a single schema directory"""
    print(f"Processing: {schema_dir}")
    
    # Create backup if requested
    if create_backup:
        backup_dir = schema_dir + '_backup'
        if not os.path.exists(backup_dir):
            shutil.copytree(schema_dir, backup_dir)
            print(f"Created backup at: {backup_dir}")
    
    # Read DDL file
    ddl_path = os.path.join(schema_dir, 'DDL.csv')
    if not os.path.exists(ddl_path):
        print(f"DDL file not found at {ddl_path}")
        return False
    
    try:
        ddl_df = pd.read_csv(ddl_path)
    except Exception as e:
        print(f"Error reading DDL file: {e}")
        return False
    
    if 'table_name' not in ddl_df.columns:
        print(f"DDL file doesn't have 'table_name' column")
        return False
    
    # Group tables by patterns
    pattern_groups = {}
    # Pattern for date-based tables like GA_SESSIONS_20160801
    pattern_regex = r'^(.+?)_(\d{8})$'  
    
    tables_to_remove = []
    
    for _, row in ddl_df.iterrows():
        table_name = row['table_name']
        match = re.match(pattern_regex, table_name)
        
        if match:
            base_name = match.group(1)
            date_suffix = match.group(2)
            
            if base_name not in pattern_groups:
                pattern_groups[base_name] = []
            
            # Store table info
            pattern_groups[base_name].append({
                'table_name': table_name,
                'date_suffix': date_suffix,
                'row_index': _  # Store row index for later reference
            })
            
            # Mark all but the first table for removal
            if len(pattern_groups[base_name]) > 1:
                tables_to_remove.append(table_name)
    
    # If no patterns found, no compression needed
    if not pattern_groups:
        print(f"No compressible patterns found in {schema_dir}")
        return False
    
    # Create compressed DDL entries and remove redundant ones
    for base_name, tables in pattern_groups.items():
        if len(tables) < 3:  # Skip if not enough similar tables
            continue
            
        # Sort by date
        tables.sort(key=lambda x: x['date_suffix'])
        
        # Get representative row (first table)
        rep_index = tables[0]['row_index']
        rep_row = ddl_df.iloc[rep_index].copy()
        
        # Update representative row
        compressed_name = f"{base_name}_[DATE]"
        rep_row['table_name'] = compressed_name
        if 'description' in rep_row:
            rep_row['description'] = f"Time-series table with dates from {tables[0]['date_suffix']} to {tables[-1]['date_suffix']}"
        
        # Update the representative row
        ddl_df.iloc[rep_index] = rep_row
        
        # Create available dates reference file
        ref_data = {
            'base_name': base_name,
            'compressed_name': compressed_name,
            'available_dates': [t['date_suffix'] for t in tables],
            'actual_tables': [t['table_name'] for t in tables]
        }
        
        ref_path = os.path.join(schema_dir, f"{base_name}_DATE_reference.json")
        with open(ref_path, 'w') as f:
            json.dump(ref_data, f, indent=2)
            
        # Also create a combined reference file
        all_compressed = os.path.join(schema_dir, 'compressed_reference.json')
        if os.path.exists(all_compressed):
            with open(all_compressed, 'r') as f:
                all_ref = json.load(f)
        else:
            all_ref = {}
            
        all_ref[base_name] = ref_data
        with open(all_compressed, 'w') as f:
            json.dump(all_ref, f, indent=2)
        
        # Process JSON files for this pattern group
        for table in tables:
            json_path = os.path.join(schema_dir, f"{table['table_name']}.json")
            if os.path.exists(json_path):
                # For first table, update it as representative
                if table == tables[0]:
                    try:
                        with open(json_path, 'r') as f:
                            table_info = json.load(f)
                            
                        # Update as compressed table
                        table_info['table_name'] = compressed_name
                        table_info['available_dates'] = [t['date_suffix'] for t in tables]
                        
                        # Save as new JSON
                        compressed_path = os.path.join(schema_dir, f"{base_name}_DATE.json")
                        with open(compressed_path, 'w') as f:
                            json.dump(table_info, f, indent=2)
                    except Exception as e:
                        print(f"Error processing JSON file {json_path}: {e}")
    
    # Remove redundant rows from DDL
    rows_to_drop = []
    for i, row in ddl_df.iterrows():
        if row['table_name'] in tables_to_remove:
            rows_to_drop.append(i)
    
    ddl_df_compressed = ddl_df.drop(rows_to_drop)
    
    # Save compressed DDL
    ddl_df_compressed.to_csv(ddl_path, index=False)
    
    print(f"Compressed {len(tables_to_remove)} tables in {schema_dir}")
    return True

def compress_all_schemas(base_dir):
    """Find and compress all schema directories"""
    schema_dirs = find_schema_directories(base_dir)
    print(f"Found {len(schema_dirs)} schema directories")
    
    compressed_count = 0
    for schema_dir in schema_dirs:
        if compress_tables_in_directory(schema_dir):
            compressed_count += 1
    
    print(f"Compressed {compressed_count} out of {len(schema_dirs)} schema directories")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compress tables in Spider Agent schema directories')
    parser.add_argument('--base-dir', type=str, default='methods/spider-agent-snow/examples',
                        help='Base directory containing schema directories')
    
    args = parser.parse_args()
    compress_all_schemas(args.base_dir)
    print("Schema compression complete!")