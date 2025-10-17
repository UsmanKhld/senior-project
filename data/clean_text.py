import json
import re
from pathlib import Path

def clean_bill_text(text):
    """
    Clean up bill text by removing boilerplate and normalizing formatting
    """
    if not text:
        return ""
    
    # Remove header boilerplate
    text = re.sub(r'\[Congressional Bills.*?\]', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'\[From the U\.S\. Government Publishing Office\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[H\.R\.\s*\d+.*?\]', '', text, flags=re.IGNORECASE)
    
    # Remove "One Hundred Nineteenth Congress" and similar
    text = re.sub(r'One Hundred.*?Congress', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'United States of America', '', text, flags=re.IGNORECASE)
    text = re.sub(r'AT THE FIRST SESSION.*?two thousand.*?twenty-five', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove "An Act" and similar markers
    text = re.sub(r'\bAn Act\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Be it enacted by.*?in Congress assembled,?', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove signature lines (Speaker, Vice President, etc.)
    text = re.sub(r'Speaker of the House.*', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'Vice President.*President of the Senate.*', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove Congressional Record headers/footers
    text = re.sub(r'\[Congressional Record.*?\]', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'\[Page\s*\w?\d+\s*of\s*\d+\]', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'\[Page\s*\w?\d+\]', ' ', text, flags=re.IGNORECASE)
    
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'www\.\S+', '', text, flags=re.IGNORECASE)
    
    # Remove asterisk dividers
    text = re.sub(r'\*{2,}', '', text)
    
    # Remove U.S. Code citations like 15 U.S.C. 1681b
    text = re.sub(r'\(\s*\d+\s+U\.S\.C\.\s+\d+[a-zA-Z]?\s*\)', '', text)
    text = re.sub(r'\d+\s+U\.S\.C\.\s+\d+[a-zA-Z]?', '', text)
    
    # Remove section/subsection markers but keep content
    # Remove things like "SEC. 1.", "(a)", "(i)" etc at start of lines
    text = re.sub(r'^SEC\.\s*\d+\.?\s*', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'^\s*\(\s*[a-z0-9]+\s*\)\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*``\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r"''\s*\.\s*$", '', text, flags=re.MULTILINE)
    
    # Normalize whitespace
    text = text.replace('\f', ' ')
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove multiple newlines
    text = re.sub(r'\n{2,}', '\n', text)
    
    # Remove spaces at start/end of lines
    lines = [ln.strip() for ln in text.splitlines()]
    
    # Remove empty lines
    lines = [ln for ln in lines if ln.strip()]
    
    text = "\n".join(lines).strip()
    
    # Remove any remaining control characters except newline and tab
    text = ''.join(ch for ch in text if ord(ch) >= 32 or ch in '\n\t')
    
    return text

def main():
    # Load bills.json
    input_file = Path("bills.json")
    if not input_file.exists():
        print(f"Error: {input_file} not found")
        return
    
    print(f"Loading {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        bills = json.load(f)
    
    print(f"Cleaning text for {len(bills)} bills...")
    
    for i, bill in enumerate(bills, 1):
        original_length = len(bill.get("text", ""))
        bill["text"] = clean_bill_text(bill.get("text", ""))
        cleaned_length = len(bill["text"])
        
        reduction = original_length - cleaned_length
        reduction_pct = (reduction / original_length * 100) if original_length > 0 else 0
        
        print(f"[{i}/{len(bills)}] {bill['bill_type']}-{bill['bill_number']}: "
              f"{original_length} → {cleaned_length} chars ({reduction_pct:.1f}% reduction)")
    
    # Save cleaned bills
    output_file = Path("bills_cleaned.json")
    print(f"\nSaving cleaned bills to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(bills, f, indent=2, ensure_ascii=False)
    
    print(f"Done! Cleaned bills saved to {output_file}")

if __name__ == "__main__":
    main()