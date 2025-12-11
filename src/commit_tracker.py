#!/usr/bin/env python3
"""
Git Commit Tracker CLI
Analyzes git commits to measure contributor value, quality, difficulty, and work style.
"""

import argparse
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List
import json


class CommitAnalyzer:
    """Analyzes git commits to extract metrics about contributors."""
    
    # Normalization factor for amount score: 10 lines = 1 point, 1000 lines = 100 points
    AMOUNT_NORMALIZATION_FACTOR = 10
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.commits_data = []
        self.contributors = defaultdict(lambda: {
            'commits': [],
            'total_commits': 0,
            'lines_added': 0,
            'lines_deleted': 0,
            'files_changed': 0,
            'complexity_score': 0,
            'quality_score': 0,
            'difficulty_score': 0,
            'value_score': 0
        })
    
    def get_commits_since(self, days: int = 30) -> List[Dict]:
        """Get all commits from the last N days."""
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Get commit hashes and basic info
        cmd = [
            'git', '-C', self.repo_path, 'log',
            f'--since={since_date}',
            '--pretty=format:%H|%an|%ae|%ad|%s',
            '--date=iso',
            '--all'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            commits = []
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('|', 4)
                if len(parts) == 5:
                    commit_hash, author, email, date, subject = parts
                    commits.append({
                        'hash': commit_hash,
                        'author': author,
                        'email': email,
                        'date': date,
                        'subject': subject
                    })
            
            return commits
        except subprocess.CalledProcessError as e:
            print(f"Error getting commits: {e}", file=sys.stderr)
            return []
    
    def get_commit_stats(self, commit_hash: str) -> Dict:
        """Get detailed statistics for a specific commit."""
        cmd = [
            'git', '-C', self.repo_path, 'show',
            '--numstat', '--format=', commit_hash
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            lines_added = 0
            lines_deleted = 0
            files_changed = 0
            file_types = set()
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('\t')
                if len(parts) >= 3:
                    added, deleted, filename = parts[0], parts[1], parts[2]
                    # Skip binary files
                    if added == '-' or deleted == '-':
                        continue
                    lines_added += int(added)
                    lines_deleted += int(deleted)
                    files_changed += 1
                    # Extract file extension
                    if '.' in filename:
                        ext = filename.split('.')[-1]
                        file_types.add(ext)
            
            return {
                'lines_added': lines_added,
                'lines_deleted': lines_deleted,
                'files_changed': files_changed,
                'file_types': list(file_types),
                'total_changes': lines_added + lines_deleted
            }
        except subprocess.CalledProcessError:
            return {
                'lines_added': 0,
                'lines_deleted': 0,
                'files_changed': 0,
                'file_types': [],
                'total_changes': 0
            }
    
    def calculate_complexity_score(self, stats: Dict) -> float:
        """Calculate complexity based on number of files and changes."""
        files = stats['files_changed']
        total_changes = stats['total_changes']
        
        # More files and more changes indicate higher complexity
        complexity = (files * 2) + (total_changes / 10)
        return min(complexity, 100)  # Cap at 100
    
    def calculate_quality_score(self, stats: Dict, subject: str) -> float:
        """Calculate quality score based on commit patterns."""
        quality = 50.0  # Base score
        
        # Good practices indicators
        if any(keyword in subject.lower() for keyword in ['test', 'fix', 'refactor', 'improve']):
            quality += 15
        
        if any(keyword in subject.lower() for keyword in ['bug', 'issue', 'error']):
            quality += 10
        
        # Code organization indicators
        if 'py' in stats['file_types'] and stats['files_changed'] <= 3:
            quality += 10  # Focused changes
        
        # Documentation indicators
        if any(ext in stats['file_types'] for ext in ['md', 'rst', 'txt']):
            quality += 10
        
        # Penalize very large unfocused commits
        if stats['files_changed'] > 10 and stats['total_changes'] > 1000:
            quality -= 20
        
        return max(0, min(quality, 100))  # Clamp between 0-100
    
    def calculate_difficulty_score(self, stats: Dict) -> float:
        """Calculate difficulty based on scope and size of changes."""
        # Difficulty increases with:
        # - More files changed
        # - More lines changed
        # - Diverse file types
        
        file_factor = min(stats['files_changed'] * 5, 40)
        change_factor = min(stats['total_changes'] / 20, 40)
        diversity_factor = len(stats['file_types']) * 5
        
        difficulty = file_factor + change_factor + diversity_factor
        return min(difficulty, 100)
    
    def calculate_value_score(self, quality: float, difficulty: float, amount: float) -> float:
        """Calculate overall value score combining quality, difficulty, and amount."""
        # Value = (Quality * 0.4) + (Difficulty * 0.3) + (Amount * 0.3)
        # This weights quality as most important, but considers effort and scope
        value = (quality * 0.4) + (difficulty * 0.3) + (amount * 0.3)
        return round(value, 2)
    
    def analyze_commits(self, days: int = 30):
        """Analyze all commits and calculate metrics for each contributor."""
        commits = self.get_commits_since(days)
        
        if not commits:
            print(f"No commits found in the last {days} days.")
            return
        
        print(f"Analyzing {len(commits)} commits from the last {days} days...\n")
        
        for commit in commits:
            author = commit['author']
            stats = self.get_commit_stats(commit['hash'])
            
            # Calculate metrics
            complexity = self.calculate_complexity_score(stats)
            quality = self.calculate_quality_score(stats, commit['subject'])
            difficulty = self.calculate_difficulty_score(stats)
            
            # Amount normalized to 0-100 scale using class constant
            amount = min((stats['total_changes'] / self.AMOUNT_NORMALIZATION_FACTOR), 100)
            
            value = self.calculate_value_score(quality, difficulty, amount)
            
            # Store commit data
            commit_data = {
                **commit,
                **stats,
                'complexity': complexity,
                'quality': quality,
                'difficulty': difficulty,
                'amount': amount,
                'value': value
            }
            
            # Aggregate contributor stats
            self.contributors[author]['commits'].append(commit_data)
            self.contributors[author]['total_commits'] += 1
            self.contributors[author]['lines_added'] += stats['lines_added']
            self.contributors[author]['lines_deleted'] += stats['lines_deleted']
            self.contributors[author]['files_changed'] += stats['files_changed']
            self.contributors[author]['complexity_score'] += complexity
            self.contributors[author]['quality_score'] += quality
            self.contributors[author]['difficulty_score'] += difficulty
            self.contributors[author]['value_score'] += value
    
    def get_work_style(self, contributor_data: Dict) -> str:
        """Determine work style based on commit patterns."""
        total_commits = contributor_data['total_commits']
        
        if total_commits == 0:
            return "No activity"
        
        avg_quality = contributor_data['quality_score'] / total_commits
        avg_difficulty = contributor_data['difficulty_score'] / total_commits
        avg_changes = (contributor_data['lines_added'] + contributor_data['lines_deleted']) / total_commits
        
        styles = []
        
        # Determine primary work style
        if avg_quality >= 70:
            styles.append("High-quality")
        elif avg_quality >= 50:
            styles.append("Balanced")
        else:
            styles.append("Rapid-iteration")
        
        if avg_difficulty >= 60:
            styles.append("complex work")
        elif avg_difficulty >= 30:
            styles.append("moderate complexity")
        else:
            styles.append("straightforward changes")
        
        if avg_changes > 200:
            styles.append("large scope")
        elif avg_changes > 50:
            styles.append("medium scope")
        else:
            styles.append("focused changes")
        
        if total_commits >= 10:
            styles.append("highly active")
        elif total_commits >= 5:
            styles.append("active")
        else:
            styles.append("occasional")
        
        return " | ".join(styles)
    
    def print_summary(self):
        """Print a formatted summary of all contributors."""
        if not self.contributors:
            print("No contributor data available.")
            return
        
        print("=" * 100)
        print(f"{'CONTRIBUTOR SUMMARY':^100}")
        print("=" * 100)
        print()
        
        # Sort by value score descending
        sorted_contributors = sorted(
            self.contributors.items(),
            key=lambda x: x[1]['value_score'],
            reverse=True
        )
        
        for author, data in sorted_contributors:
            total_commits = data['total_commits']
            
            # Skip contributors with no commits
            if total_commits == 0:
                continue
            
            # Calculate averages
            avg_quality = data['quality_score'] / total_commits
            avg_difficulty = data['difficulty_score'] / total_commits
            avg_value = data['value_score'] / total_commits
            
            work_style = self.get_work_style(data)
            
            print(f"👤 Contributor: {author}")
            print(f"   {'─' * 90}")
            print(f"   📊 Commits: {total_commits}")
            print(f"   ➕ Lines Added: {data['lines_added']}")
            print(f"   ➖ Lines Deleted: {data['lines_deleted']}")
            print(f"   📁 Files Changed: {data['files_changed']}")
            print()
            print(f"   🎯 Overall Value Score:  {avg_value:.2f}/100")
            print(f"   ✨ Quality Score:        {avg_quality:.2f}/100")
            print(f"   🔧 Difficulty Score:     {avg_difficulty:.2f}/100")
            print(f"   📦 Amount Score:         {(data['lines_added'] + data['lines_deleted']) / total_commits / self.AMOUNT_NORMALIZATION_FACTOR:.2f}/100")
            print()
            print(f"   💼 Work Style: {work_style}")
            print()
            print("   Recent Commits:")
            for i, commit in enumerate(data['commits'][:3], 1):
                print(f"      {i}. {commit['subject'][:70]}")
                print(f"         ({commit['files_changed']} files, +{commit['lines_added']}/-{commit['lines_deleted']}, "
                      f"value: {commit['value']:.1f})")
            if len(data['commits']) > 3:
                print(f"      ... and {len(data['commits']) - 3} more")
            print()
            print("=" * 100)
            print()
    
    def export_json(self, output_file: str):
        """Export contributor data to JSON file."""
        export_data = {}
        for author, data in self.contributors.items():
            total_commits = data['total_commits']
            
            # Skip contributors with no commits
            if total_commits == 0:
                continue
            
            export_data[author] = {
                'total_commits': total_commits,
                'lines_added': data['lines_added'],
                'lines_deleted': data['lines_deleted'],
                'files_changed': data['files_changed'],
                'avg_quality_score': round(data['quality_score'] / total_commits, 2),
                'avg_difficulty_score': round(data['difficulty_score'] / total_commits, 2),
                'avg_value_score': round(data['value_score'] / total_commits, 2),
                'work_style': self.get_work_style(data),
                'commits': [
                    {
                        'hash': c['hash'][:8],
                        'subject': c['subject'],
                        'date': c['date'],
                        'value': c['value']
                    }
                    for c in data['commits']
                ]
            }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        print(f"Data exported to {output_file}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Git Commit Tracker - Analyze contributor value and work style',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Analyze last 30 days
  %(prog)s --days 60                # Analyze last 60 days
  %(prog)s --export report.json     # Export to JSON
  %(prog)s --repo /path/to/repo     # Analyze different repo
        """
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to look back (default: 30)'
    )
    
    parser.add_argument(
        '--repo',
        type=str,
        default='.',
        help='Path to git repository (default: current directory)'
    )
    
    parser.add_argument(
        '--export',
        type=str,
        help='Export data to JSON file'
    )
    
    args = parser.parse_args()
    
    # Create analyzer and run analysis
    analyzer = CommitAnalyzer(args.repo)
    analyzer.analyze_commits(args.days)
    analyzer.print_summary()
    
    # Export if requested
    if args.export:
        analyzer.export_json(args.export)


if __name__ == '__main__':
    main()
