"""Main pipeline with Google Docs support"""

import json
from datetime import datetime
from pathlib import Path
from .extractor import TranscriptExtractor
from .template_engine import ProposalGenerator
from .models import ExtractedData
from .google_docs import GoogleDocsExporter  # NEW

class ProposalPipeline:
    def __init__(self):
        """Initialize the pipeline"""
        self.extractor = TranscriptExtractor()
        self.generator = ProposalGenerator()
        self.google_docs = GoogleDocsExporter()  # NEW
    
    def process(self, transcript: str, transcript_name: str = "unknown", 
                export_to_google: bool = False) -> dict:  # NEW parameter
        """Process a transcript from start to finish"""
        
        print("\n" + "="*50)
        print("🚀 Starting Proposal Generation")
        print("="*50)
        
        # Step 1: Extract data
        print("\n📝 Step 1: Extracting data from transcript...")
        extracted_data = self.extractor.extract(transcript)
        
        # Step 2: Generate proposal ID
        proposal_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Step 3: Generate DOCX
        print("\n📄 Step 2: Generating proposal document...")
        output_path = f"outputs/proposals/proposal_{proposal_id}.docx"
        self.generator.generate(extracted_data, output_path)
        
        # Step 4: Save extracted data as JSON
        print("\n💾 Step 3: Saving extracted data...")
        json_path = f"outputs/json/extracted_{proposal_id}.json"
        result_data = extracted_data.to_dict()
        result_data['proposal_id'] = proposal_id
        result_data['docx_path'] = output_path
        
        with open(json_path, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        # Step 5: Export to Google Docs (NEW)
        google_result = None
        if export_to_google:
            print("\n🌐 Step 4: Exporting to Google Docs...")
            google_result = self.google_docs.upload_proposal(output_path)
            if google_result['success']:
                print(f"✅ Google Docs: {google_result['url']}")
                result_data['google_docs_url'] = google_result['url']
        
        print("\n" + "="*50)
        print("✅ Proposal Generation Complete!")
        print("="*50)
        print(f"📄 Document: {output_path}")
        if google_result and google_result['success']:
            print(f"🌐 Google Docs: {google_result['url']}")
        
        return {
            "proposal_id": proposal_id,
            "docx_path": output_path,
            "json_path": json_path,
            "extracted_data": result_data,
            "google_docs_url": google_result['url'] if google_result and google_result['success'] else None
        }