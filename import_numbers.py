#!/usr/bin/env python3
"""
Import phone numbers from Excel or CSV files
"""

import sys
import json
import re
import pandas as pd
from pathlib import Path


def clean_phone_number(number):
    """Clean and format phone number to E.164 format"""
    if pd.isna(number):
        return None
    
    # Convert to string and remove whitespace
    number = str(number).strip()
    
    # Remove common separators
    clean = re.sub(r'[\s\-\(\)]', '', number)
    
    # Must have at least 8 digits
    if len(clean) < 8:
        return None
    
    # Add + prefix if missing
    if not clean.startswith('+'):
        # If starts with 46, assume Swedish international format
        if clean.startswith('46') and len(clean) >= 11:
            clean = '+' + clean
        # If starts with 0, convert to Swedish international format
        elif clean.startswith('0') and len(clean) >= 10:
            clean = '+46' + clean[1:]
        # If starts with 7, assume Swedish mobile without country code
        elif clean.startswith('7') and len(clean) == 9:
            clean = '+46' + clean
    
    # Validate format
    if not re.match(r'^\+[0-9]{10,15}$', clean):
        return None
    
    return clean


def import_from_file(filepath, output_file='config/trusted_numbers.json'):
    """Import phone numbers from Excel or CSV file"""
    
    filepath = Path(filepath)
    
    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        return False
    
    print(f"📂 Reading file: {filepath}")
    
    try:
        # Read file based on extension
        if filepath.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(filepath)
        elif filepath.suffix.lower() == '.csv':
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    print(f"✓ Read CSV with {encoding} encoding")
                    break
                except:
                    continue
        else:
            print(f"❌ Unsupported file format: {filepath.suffix}")
            print("Supported formats: .xlsx, .xls, .csv")
            return False
        
        print(f"✓ Found {len(df)} rows")
        print(f"✓ Columns: {', '.join(df.columns)}")
        
        # Find phone number column
        phone_numbers = []
        
        for col in df.columns:
            # Check if column name suggests phone numbers
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['nummer', 'number', 'phone', 'tel', 'mobil', 'mobile']):
                print(f"\n📱 Processing column: {col}")
                
                for value in df[col]:
                    clean = clean_phone_number(value)
                    if clean:
                        phone_numbers.append(clean)
        
        # If no phone column found, try all columns
        if not phone_numbers:
            print("\n📱 No phone column found, scanning all columns...")
            for col in df.columns:
                for value in df[col]:
                    clean = clean_phone_number(value)
                    if clean:
                        phone_numbers.append(clean)
        
        # Remove duplicates and sort
        phone_numbers = sorted(list(set(phone_numbers)))
        
        if not phone_numbers:
            print("❌ No valid phone numbers found in file")
            return False
        
        print(f"\n✅ Found {len(phone_numbers)} unique valid phone numbers:")
        for i, num in enumerate(phone_numbers[:10], 1):
            print(f"   {i}. {num}")
        
        if len(phone_numbers) > 10:
            print(f"   ... and {len(phone_numbers) - 10} more")
        
        # Load existing numbers
        output_path = Path(output_file)
        existing_numbers = []
        
        if output_path.exists():
            try:
                with open(output_path, 'r') as f:
                    data = json.load(f)
                    existing_numbers = data.get('numbers', [])
                print(f"\n📋 Found {len(existing_numbers)} existing numbers")
            except:
                pass
        
        # Merge with existing
        all_numbers = sorted(list(set(existing_numbers + phone_numbers)))
        new_count = len(all_numbers) - len(existing_numbers)
        
        # Save to file
        output_data = {
            "numbers": all_numbers,
            "description": f"Imported from {filepath.name}"
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\n💾 Saved to: {output_path}")
        print(f"   Total numbers: {len(all_numbers)}")
        print(f"   New numbers: {new_count}")
        print(f"   Duplicates skipped: {len(phone_numbers) - new_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 import_numbers.py <file.xlsx|file.csv>")
        print("\nExample:")
        print("  python3 import_numbers.py accessList.xlsx")
        print("  python3 import_numbers.py numbers.csv")
        sys.exit(1)
    
    filepath = sys.argv[1]
    success = import_from_file(filepath)
    
    sys.exit(0 if success else 1)
