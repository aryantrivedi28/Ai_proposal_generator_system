"""Main CLI entry point for the proposal generator"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import ProposalPipeline

def main():
    print("""
    ╔═══════════════════════════════════════╗
    ║   AI Proposal Generator               ║
    ║   Convert transcripts to proposals    ║
    ╚═══════════════════════════════════════╝
    """)
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python main.py <transcript_file>")
        print("  python main.py --text \"your transcript text here\"")
        print("\nExamples:")
        print("  python main.py transcript.txt")
        print("  python main.py --text \"Client wants a wedding for 150 people\"")
        return
    
    # Initialize pipeline
    pipeline = ProposalPipeline()
    
    # Process based on input type
    if sys.argv[1] == "--text":
        # Direct text input
        transcript = " ".join(sys.argv[2:])
        result = pipeline.process(transcript)
    else:
        # File input
        file_path = sys.argv[1]
        if not Path(file_path).exists():
            print(f"❌ File not found: {file_path}")
            return
        result = pipeline.process_file(file_path)
    
    print("\n📋 Extracted Information:")
    print("-" * 30)
    for key, value in result["extracted_data"].items():
        if value:
            print(f"  {key}: {value}")

if __name__ == "__main__":
    main()