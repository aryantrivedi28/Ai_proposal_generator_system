"""SQLite database for proposal storage"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

class ProposalDatabase:
    """Store and query proposal history"""
    
    def __init__(self, db_path: str = "data/proposals.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Proposals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS proposals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proposal_id TEXT UNIQUE NOT NULL,
                    client_name TEXT,
                    event_name TEXT,
                    event_date TEXT,
                    guest_count INTEGER,
                    proposal_type TEXT,
                    budget TEXT,
                    docx_path TEXT,
                    pdf_path TEXT,
                    google_docs_url TEXT,
                    created_at TIMESTAMP,
                    status TEXT DEFAULT 'draft',
                    extracted_data_json TEXT,
                    cost_usd REAL
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_client ON proposals(client_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON proposals(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_type ON proposals(proposal_type)')
            
            conn.commit()
    
    def save_proposal(self, proposal_data: dict) -> int:
        """Save proposal to database"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            extracted = proposal_data.get('extracted_data', {})
            
            cursor.execute('''
                INSERT OR REPLACE INTO proposals 
                (proposal_id, client_name, event_name, event_date, guest_count,
                 proposal_type, budget, docx_path, pdf_path, google_docs_url,
                 created_at, status, extracted_data_json, cost_usd)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                proposal_data.get('proposal_id'),
                extracted.get('client_name'),
                extracted.get('event_name'),
                extracted.get('event_date'),
                extracted.get('guest_count'),
                extracted.get('proposal_type'),
                extracted.get('budget'),
                proposal_data.get('docx_path'),
                proposal_data.get('pdf_path'),
                proposal_data.get('google_docs_url'),
                datetime.now().isoformat(),
                'draft',
                json.dumps(extracted),
                proposal_data.get('cost_usd', 0)
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_all_proposals(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all proposals with pagination"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM proposals 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def search_proposals(self, query: str) -> List[Dict]:
        """Search proposals by client or event name"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM proposals 
                WHERE client_name LIKE ? OR event_name LIKE ?
                ORDER BY created_at DESC
            ''', (f'%{query}%', f'%{query}%'))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_proposal(self, proposal_id: str) -> Optional[Dict]:
        """Get single proposal by ID"""
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM proposals WHERE proposal_id = ?', (proposal_id,))
            row = cursor.fetchone()
            
            return dict(row) if row else None
    
    def update_status(self, proposal_id: str, status: str):
        """Update proposal status"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE proposals SET status = ? WHERE proposal_id = ?
            ''', (status, proposal_id))
            conn.commit()
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM proposals')
            total = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT proposal_type, COUNT(*) FROM proposals 
                GROUP BY proposal_type
            ''')
            by_type = dict(cursor.fetchall())
            
            cursor.execute('SELECT SUM(cost_usd) FROM proposals')
            total_cost = cursor.fetchone()[0] or 0
            
            return {
                "total_proposals": total,
                "by_type": by_type,
                "total_cost_usd": round(total_cost, 4),
                "average_cost": round(total_cost / total, 4) if total > 0 else 0
            }