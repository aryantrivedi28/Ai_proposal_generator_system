"""Track OpenAI API costs and usage"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

class CostTracker:
    """Track and monitor API costs"""
    
    # Pricing per 1K tokens (as of 2024)
    PRICING = {
        'gpt-4o-mini': {
            'input': 0.00015,   # $0.00015 per 1K tokens
            'output': 0.00060   # $0.00060 per 1K tokens
        },
        'gpt-3.5-turbo': {
            'input': 0.00050,
            'output': 0.00150
        }
    }
    
    def __init__(self, monthly_budget: float = 50.0):
        self.monthly_budget = monthly_budget
        self.log_file = Path("logs/api_costs.jsonl")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.daily_usage = defaultdict(float)
        self._load_history()
    
    def _load_history(self):
        """Load historical usage"""
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        date = entry['timestamp'][:10]
                        self.daily_usage[date] += entry['cost']
                    except:
                        pass
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for API call"""
        pricing = self.PRICING.get(model, self.PRICING['gpt-4o-mini'])
        
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        
        return input_cost + output_cost
    
    def record_usage(self, model: str, input_tokens: int, output_tokens: int, 
                     proposal_id: str = None, endpoint: str = "extraction"):
        """Record API usage"""
        
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": cost,
            "proposal_id": proposal_id,
            "endpoint": endpoint
        }
        
        # Write to log
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        
        # Update daily usage
        today = datetime.now().strftime("%Y-%m-%d")
        self.daily_usage[today] += cost
        
        return cost
    
    def get_daily_cost(self) -> float:
        """Get today's total cost"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.daily_usage.get(today, 0.0)
    
    def get_weekly_cost(self) -> float:
        """Get last 7 days cost"""
        week_ago = datetime.now() - timedelta(days=7)
        total = 0.0
        for date, cost in self.daily_usage.items():
            if datetime.strptime(date, "%Y-%m-%d") >= week_ago:
                total += cost
        return total
    
    def get_monthly_cost(self) -> float:
        """Get current month cost"""
        current_month = datetime.now().strftime("%Y-%m")
        total = 0.0
        for date, cost in self.daily_usage.items():
            if date.startswith(current_month):
                total += cost
        return total
    
    def get_remaining_budget(self) -> float:
        """Get remaining monthly budget"""
        return max(0, self.monthly_budget - self.get_monthly_cost())
    
    def check_alerts(self) -> list:
        """Check for budget alerts"""
        alerts = []
        monthly = self.get_monthly_cost()
        
        if monthly > self.monthly_budget:
            alerts.append(f"⚠️ Monthly budget exceeded: ${monthly:.2f} > ${self.monthly_budget}")
        elif monthly > self.monthly_budget * 0.8:
            alerts.append(f"⚠️ 80% of monthly budget used: ${monthly:.2f} / ${self.monthly_budget}")
        
        return alerts
    
    def get_proposal_cost(self, proposal_id: str) -> float:
        """Get total cost for a specific proposal"""
        total = 0.0
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                for line in f:
                    entry = json.loads(line)
                    if entry.get('proposal_id') == proposal_id:
                        total += entry['cost']
        return total
    
    def get_summary(self) -> dict:
        """Get complete cost summary"""
        return {
            "today": round(self.get_daily_cost(), 4),
            "this_week": round(self.get_weekly_cost(), 4),
            "this_month": round(self.get_monthly_cost(), 4),
            "remaining_budget": round(self.get_remaining_budget(), 2),
            "budget_total": self.monthly_budget,
            "alerts": self.check_alerts(),
            "average_per_proposal": self._get_average_cost()
        }
    
    def _get_average_cost(self) -> float:
        """Calculate average cost per proposal"""
        proposals = set()
        total_cost = 0.0
        
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                for line in f:
                    entry = json.loads(line)
                    if entry.get('proposal_id'):
                        proposals.add(entry['proposal_id'])
                        total_cost += entry['cost']
        
        if proposals:
            return round(total_cost / len(proposals), 4)
        return 0.0