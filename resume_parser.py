#!/usr/bin/env python3
from unstructured.partition.auto import partition


def parse_document(file_path):
    """
    Parse document using unstructured library
    Returns extracted text
    """
    # Partition automatically detects file type and extracts content
    elements = partition(file_path)
    
    # Convert elements to text
    text = "\n".join([str(el) for el in elements])
    
    return text


def parse_and_save(file_path: str, output_path: str = "resume_text.md") -> str:
    text = parse_document(file_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    return text


def main():
    import sys
    input_file = sys.argv[1] if len(sys.argv) > 1 else "document.pdf"
    output_file = "resume_text.md"
    try:
        doc_text = parse_and_save(input_file, output_file)
        
        # Display summary
        print(f"Saved to {output_file}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure unstructured is installed:")
        print("  pip install unstructured")
        print("  pip install unstructured[pdf]  # for PDF support")


if __name__ == "__main__":
    main()