"""Batch processing for multiple transcripts"""

import json
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Callable
from .pipeline import ProposalPipeline

class BatchProcessor:
    """Process multiple transcripts in batch"""
    
    def __init__(self, max_workers: int = 3):
        self.pipeline = ProposalPipeline()
        self.max_workers = max_workers
        self.results = []
    
    def process_folder(self, folder_path: str, file_pattern: str = "*.txt",
                      progress_callback: Callable = None) -> List[Dict]:
        """Process all transcript files in a folder"""
        
        folder = Path(folder_path)
        files = list(folder.glob(file_pattern))
        
        if not files:
            print(f"No files found in {folder_path}")
            return []
        
        print(f"Found {len(files)} files to process")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            for file in files:
                future = executor.submit(self._process_single, file)
                futures[future] = file
            
            for i, future in enumerate(as_completed(futures)):
                file = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if progress_callback:
                        progress_callback(i + 1, len(files), file.name)
                    
                    print(f"[{i+1}/{len(files)}] ✅ {file.name}")
                    
                except Exception as e:
                    print(f"[{i+1}/{len(files)}] ❌ {file.name}: {e}")
                    results.append({"file": str(file), "error": str(e)})
        
        # Save batch summary
        self._save_batch_summary(results)
        
        return results
    
    def _process_single(self, file_path: Path) -> Dict:
        """Process a single file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            transcript = f.read()
        
        result = self.pipeline.process(
            transcript,
            transcript_name=file_path.name,
            export_to_google=False,
            export_to_pdf=False
        )
        
        return {
            "file": str(file_path),
            "proposal_id": result['proposal_id'],
            "docx_path": result['docx_path'],
            "status": "success"
        }
    
    def process_list(self, transcripts: List[str], names: List[str] = None) -> List[Dict]:
        """Process a list of transcript strings"""
        
        if not names:
            names = [f"transcript_{i+1}" for i in range(len(transcripts))]
        
        results = []
        
        for i, (transcript, name) in enumerate(zip(transcripts, names)):
            print(f"Processing {i+1}/{len(transcripts)}: {name}")
            
            result = self.pipeline.process(
                transcript,
                transcript_name=name,
                export_to_google=False,
                export_to_pdf=False
            )
            
            results.append({
                "name": name,
                "proposal_id": result['proposal_id'],
                "docx_path": result['docx_path']
            })
        
        return results
    
    def _save_batch_summary(self, results: List[Dict]):
        """Save batch processing summary"""
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_processed": len([r for r in results if 'error' not in r]),
            "total_errors": len([r for r in results if 'error' in r]),
            "results": results
        }
        
        output_path = f"outputs/batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Path("outputs").mkdir(exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📊 Batch summary saved: {output_path}")