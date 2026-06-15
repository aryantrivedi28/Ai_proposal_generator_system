"""Main pipeline that connects everything together"""

import json
from datetime import datetime
from pathlib import Path
from .extractor import TranscriptExtractor
from .template_engine import ProposalGenerator
from .models import ExtractedData

# Optional imports (won't break if not installed)
try:
    from .google_docs import GoogleDocsExporter
    GOOGLE_DOCS_AVAILABLE = True
except ImportError:
    GOOGLE_DOCS_AVAILABLE = False
    print("⚠️ Google Docs not available. Install google-api-python-client")

try:
    from .pdf_exporter import PDFExporter
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ PDF export not available. Install reportlab")

try:
    from .database import ProposalDatabase
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("⚠️ Database not available")

try:
    from .cost_tracker import CostTracker
    COST_TRACKING_AVAILABLE = True
except ImportError:
    COST_TRACKING_AVAILABLE = False
    print("⚠️ Cost tracking not available")

class ProposalPipeline:
    def __init__(self):
        """Initialize the pipeline with all available components"""
        self.extractor = TranscriptExtractor()
        self.generator = ProposalGenerator()
        
        # Initialize optional components
        self.google_docs = GoogleDocsExporter() if GOOGLE_DOCS_AVAILABLE else None
        self.pdf_exporter = PDFExporter() if PDF_AVAILABLE else None
        self.db = ProposalDatabase() if DATABASE_AVAILABLE else None
        self.cost_tracker = CostTracker() if COST_TRACKING_AVAILABLE else None
    
    def process(self, transcript: str, transcript_name: str = "unknown", 
                export_to_google: bool = False, export_to_pdf: bool = False) -> dict:
        """
        Process a transcript from start to finish
        
        Args:
            transcript: The transcript text to process
            transcript_name: Name of the transcript file
            export_to_google: Whether to upload to Google Docs
            export_to_pdf: Whether to generate PDF version
        
        Returns:
            Dictionary with proposal details
        """
        
        print("\n" + "="*50)
        print("🚀 Starting Proposal Generation")
        print("="*50)
        
        # Step 1: Extract data
        print("\n📝 Step 1: Extracting data from transcript...")
        extracted_data = self.extractor.extract(transcript)
        
        # Generate proposal ID
        proposal_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Set proposal ID in extractor for cost tracking
        if hasattr(self.extractor, 'set_proposal_id'):
            self.extractor.set_proposal_id(proposal_id)
        
        # Step 2: Generate DOCX
        print("\n📄 Step 2: Generating proposal document...")
        output_path = f"outputs/proposals/proposal_{proposal_id}.docx"
        self.generator.generate(extracted_data, output_path)
        
        # Step 3: Save extracted data as JSON
        print("\n💾 Step 3: Saving extracted data...")
        result_data = extracted_data.to_dict()
        result_data['proposal_id'] = proposal_id
        result_data['docx_path'] = output_path
        result_data['created_at'] = datetime.now().isoformat()
        
        json_path = f"outputs/json/extracted_{proposal_id}.json"
        Path("outputs/json").mkdir(parents=True, exist_ok=True)
        with open(json_path, 'w') as f:
            json.dump(result_data, f, indent=2, default=str)
        
        # Step 4: Export to Google Docs (if requested and available)
        google_result = None
        if export_to_google and self.google_docs:
            print("\n🌐 Step 4: Exporting to Google Docs...")
            try:
                google_result = self.google_docs.upload_proposal(output_path)
                if google_result and google_result.get('success'):
                    print(f"✅ Google Docs: {google_result['url']}")
                    result_data['google_docs_url'] = google_result['url']
                else:
                    print(f"⚠️ Google Docs export failed: {google_result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"⚠️ Google Docs error: {e}")
        elif export_to_google and not self.google_docs:
            print("⚠️ Google Docs not available. Install required packages.")
        
        # Step 5: Export to PDF (if requested and available)
        pdf_path = None
        if export_to_pdf and self.pdf_exporter:
            print("\n📑 Step 5: Exporting to PDF...")
            try:
                pdf_path = self.pdf_exporter.convert_docx_to_pdf(output_path)
                if pdf_path:
                    print(f"✅ PDF: {pdf_path}")
                    result_data['pdf_path'] = pdf_path
            except Exception as e:
                print(f"⚠️ PDF export error: {e}")
        elif export_to_pdf and not self.pdf_exporter:
            print("⚠️ PDF export not available. Install reportlab.")
        
        # Step 6: Save to database (if available)
        if self.db:
            print("\n💾 Step 6: Saving to database...")
            try:
                # Get cost if available
                if self.cost_tracker:
                    total_cost = self.cost_tracker.get_proposal_cost(proposal_id)
                    result_data['cost_usd'] = total_cost
                
                self.db.save_proposal(result_data)
                print("✅ Saved to database")
            except Exception as e:
                print(f"⚠️ Database save error: {e}")
        
        # Step 7: Track cost (if available)
        if self.cost_tracker:
            print("\n💰 Step 7: Tracking costs...")
            summary = self.cost_tracker.get_summary()
            print(f"   Today's cost: ${summary['today']:.4f}")
            print(f"   This month: ${summary['this_month']:.2f}")
        
        print("\n" + "="*50)
        print("✅ Proposal Generation Complete!")
        print("="*50)
        print(f"📄 Document: {output_path}")
        print(f"📊 Data: {json_path}")
        if google_result and google_result.get('success'):
            print(f"🌐 Google Docs: {google_result['url']}")
        if pdf_path:
            print(f"📑 PDF: {pdf_path}")
        
        return {
            "proposal_id": proposal_id,
            "docx_path": output_path,
            "json_path": json_path,
            "pdf_path": pdf_path,
            "google_docs_url": google_result['url'] if google_result and google_result.get('success') else None,
            "extracted_data": result_data
        }
    
    def process_file(self, file_path: str, export_to_google: bool = False, export_to_pdf: bool = False) -> dict:
        """Process a transcript from a file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            transcript = f.read()
        return self.process(transcript, Path(file_path).name, export_to_google, export_to_pdf)
    
    def export_to_google_docs(self, proposal_id: str, docx_path: str) -> dict:
        """Export existing proposal to Google Docs"""
        if not self.google_docs:
            return {"success": False, "error": "Google Docs not available"}
        
        return self.google_docs.upload_proposal(docx_path, f"Proposal_{proposal_id}")
    
    def export_to_pdf(self, docx_path: str) -> str:
        """Convert proposal to PDF"""
        if not self.pdf_exporter:
            return None
        
        return self.pdf_exporter.convert_docx_to_pdf(docx_path)