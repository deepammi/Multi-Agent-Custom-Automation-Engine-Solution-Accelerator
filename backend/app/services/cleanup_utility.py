"""
Cleanup utility for removing deprecated code and optimizing performance.

This utility helps identify and clean up deprecated patterns from the
LangGraph Orchestrator Simplification project.
"""
import logging
import os
import re
from typing import List, Dict, Any, Set
from pathlib import Path

logger = logging.getLogger(__name__)


class DeprecatedPatternDetector:
    """Detects deprecated patterns in the codebase."""
    
    DEPRECATED_PATTERNS = {
        "next_agent": {
            "pattern": r"next_agent",
            "description": "Old routing field, replaced by linear execution",
            "replacement": "Use agent_sequence and current_step instead"
        },
        "workflow_type": {
            "pattern": r"workflow_type",
            "description": "Old workflow classification, replaced by AI Planner",
            "replacement": "Use AI Planner for dynamic workflow generation"
        },
        "supervisor_router": {
            "pattern": r"supervisor_router",
            "description": "Old routing function, eliminated per requirements",
            "replacement": "Use LinearGraphFactory.create_graph_from_sequence()"
        },
        "add_conditional_edges": {
            "pattern": r"add_conditional_edges",
            "description": "Conditional routing, replaced by linear edges",
            "replacement": "Use add_edge() for linear connections"
        },
        "get_agent_graph": {
            "pattern": r"get_agent_graph\(\)",
            "description": "Old graph creation function",
            "replacement": "Use LinearGraphFactory.get_default_graph()"
        }
    }
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.findings: List[Dict[str, Any]] = []
    
    def scan_directory(self, directory: str, exclude_patterns: List[str] = None) -> List[Dict[str, Any]]:
        """
        Scan directory for deprecated patterns.
        
        Args:
            directory: Directory to scan
            exclude_patterns: Patterns to exclude from scanning
            
        Returns:
            List of findings with deprecated patterns
        """
        exclude_patterns = exclude_patterns or [
            "test_*",  # Test files may legitimately test deprecated patterns
            "*.md",    # Documentation files
            "*.log",   # Log files
            "__pycache__",
            ".git"
        ]
        
        findings = []
        scan_path = self.project_root / directory
        
        if not scan_path.exists():
            logger.warning(f"Directory {scan_path} does not exist")
            return findings
        
        for file_path in scan_path.rglob("*.py"):
            # Skip excluded patterns
            if any(file_path.match(pattern) for pattern in exclude_patterns):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_findings = self._scan_file_content(str(file_path), content)
                findings.extend(file_findings)
                
            except Exception as e:
                logger.error(f"Error scanning {file_path}: {e}")
        
        return findings
    
    def _scan_file_content(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Scan file content for deprecated patterns."""
        findings = []
        lines = content.split('\n')
        
        for pattern_name, pattern_info in self.DEPRECATED_PATTERNS.items():
            pattern = re.compile(pattern_info["pattern"])
            
            for line_num, line in enumerate(lines, 1):
                if pattern.search(line):
                    # Skip comments that mention deprecation
                    if "DEPRECATED" in line or "deprecated" in line:
                        continue
                    
                    findings.append({
                        "file": file_path,
                        "line": line_num,
                        "pattern": pattern_name,
                        "content": line.strip(),
                        "description": pattern_info["description"],
                        "replacement": pattern_info["replacement"]
                    })
        
        return findings
    
    def generate_cleanup_report(self, findings: List[Dict[str, Any]]) -> str:
        """Generate a cleanup report from findings."""
        if not findings:
            return "✅ No deprecated patterns found!"
        
        report = ["🧹 Deprecated Pattern Cleanup Report", "=" * 50, ""]
        
        # Group by pattern
        by_pattern = {}
        for finding in findings:
            pattern = finding["pattern"]
            if pattern not in by_pattern:
                by_pattern[pattern] = []
            by_pattern[pattern].append(finding)
        
        for pattern, pattern_findings in by_pattern.items():
            report.append(f"## {pattern.upper()}")
            report.append(f"Description: {pattern_findings[0]['description']}")
            report.append(f"Replacement: {pattern_findings[0]['replacement']}")
            report.append(f"Occurrences: {len(pattern_findings)}")
            report.append("")
            
            # Show first few occurrences
            for finding in pattern_findings[:5]:
                report.append(f"  📁 {finding['file']}:{finding['line']}")
                report.append(f"     {finding['content']}")
            
            if len(pattern_findings) > 5:
                report.append(f"  ... and {len(pattern_findings) - 5} more occurrences")
            
            report.append("")
        
        return "\n".join(report)


class PerformanceOptimizer:
    """Optimizes performance by cleaning up unused code and improving caching."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
    
    def find_unused_imports(self, file_path: str) -> List[str]:
        """Find potentially unused imports in a Python file."""
        unused_imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple heuristic: find imports that aren't used in the file
            import_lines = []
            for line_num, line in enumerate(content.split('\n'), 1):
                if line.strip().startswith(('import ', 'from ')):
                    import_lines.append((line_num, line.strip()))
            
            for line_num, import_line in import_lines:
                # Extract imported names
                if import_line.startswith('from '):
                    # from module import name1, name2
                    parts = import_line.split(' import ')
                    if len(parts) == 2:
                        names = [name.strip() for name in parts[1].split(',')]
                        for name in names:
                            if name not in content.replace(import_line, ''):
                                unused_imports.append(f"Line {line_num}: {name} from {import_line}")
                elif import_line.startswith('import '):
                    # import module
                    module = import_line.replace('import ', '').strip()
                    if module not in content.replace(import_line, ''):
                        unused_imports.append(f"Line {line_num}: {import_line}")
        
        except Exception as e:
            logger.error(f"Error analyzing imports in {file_path}: {e}")
        
        return unused_imports
    
    def analyze_memory_usage(self) -> Dict[str, Any]:
        """Analyze memory usage patterns."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "percent": process.memory_percent(),
                "available_mb": psutil.virtual_memory().available / 1024 / 1024
            }
        except ImportError:
            return {"error": "psutil not available for memory analysis"}
    
    def suggest_optimizations(self) -> List[str]:
        """Suggest performance optimizations."""
        suggestions = []
        
        # Check for graph factory cache usage
        try:
            from app.agents.graph_factory import LinearGraphFactory
            cache_stats = LinearGraphFactory.get_cache_stats()
            
            if cache_stats["cached_graphs"] == 0:
                suggestions.append("Enable graph caching in LinearGraphFactory for better performance")
            elif cache_stats["cached_graphs"] > 50:
                suggestions.append("Consider implementing cache size limits to prevent memory bloat")
        except Exception:
            suggestions.append("Ensure LinearGraphFactory is properly configured for caching")
        
        # Check for performance monitoring
        try:
            from app.services.performance_monitor import get_performance_monitor
            monitor = get_performance_monitor()
            stats = monitor.get_overall_stats()
            
            if stats["workflows"]["total"] == 0:
                suggestions.append("Start using PerformanceMonitor to track workflow metrics")
            elif stats["cache"]["hit_rate"] < 0.5:
                suggestions.append("Low cache hit rate - consider optimizing caching strategy")
        except Exception:
            suggestions.append("Implement performance monitoring for better insights")
        
        return suggestions


def run_cleanup_analysis(project_root: str = ".") -> None:
    """Run complete cleanup analysis and generate report."""
    logger.info("🧹 Starting cleanup analysis...")
    
    # Detect deprecated patterns
    detector = DeprecatedPatternDetector(project_root)
    findings = detector.scan_directory("backend/app", exclude_patterns=[
        "test_*",
        "*.md",
        "__pycache__"
    ])
    
    # Generate report
    report = detector.generate_cleanup_report(findings)
    print(report)
    
    # Performance analysis
    optimizer = PerformanceOptimizer(project_root)
    suggestions = optimizer.suggest_optimizations()
    
    if suggestions:
        print("\n🚀 Performance Optimization Suggestions:")
        print("=" * 50)
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion}")
    
    # Memory analysis
    memory_info = optimizer.analyze_memory_usage()
    if "error" not in memory_info:
        print(f"\n💾 Memory Usage:")
        print(f"   RSS: {memory_info['rss_mb']:.1f} MB")
        print(f"   Percent: {memory_info['percent']:.1f}%")
        print(f"   Available: {memory_info['available_mb']:.1f} MB")
    
    logger.info("✅ Cleanup analysis complete")


if __name__ == "__main__":
    run_cleanup_analysis()