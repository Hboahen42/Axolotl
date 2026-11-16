"""
Node visitor tracking - tracks which AST nodes are visited during interpretation.
Useful for understanding execution flow and demonstrating how the interpreter traverses the AST.
"""

from typing import List, Dict, Any


class NodeVisit:
    """Represents a single node visit during execution."""
    
    def __init__(self, node_type: str, node_name: str, depth: int, order: int):
        self.node_type = node_type
        self.node_name = node_name
        self.depth = depth
        self.order = order
    
    def __repr__(self):
        return f"{self.node_type}:{self.node_name}"


class NodeTracker:
    """Tracks AST nodes visited during interpretation."""
    
    def __init__(self):
        self.visits: List[NodeVisit] = []
        self.visit_order = 0
        self.depth_stack = [0]
        self.enabled = False
    
    def enable(self):
        """Start tracking node visits."""
        self.enabled = True
        self.visits = []
        self.visit_order = 0
        self.depth_stack = [0]
    
    def disable(self):
        """Stop tracking node visits."""
        self.enabled = False
    
    def push_depth(self):
        """Enter a deeper scope."""
        if self.enabled:
            self.depth_stack.append(self.depth_stack[-1] + 1)
    
    def pop_depth(self):
        """Exit to shallower scope."""
        if self.enabled and len(self.depth_stack) > 1:
            self.depth_stack.pop()
    
    def track(self, node):
        """Record a node visit."""
        if not self.enabled:
            return
        
        node_type = type(node).__name__
        node_name = _get_node_display_name(node)
        depth = self.depth_stack[-1]
        
        visit = NodeVisit(node_type, node_name, depth, self.visit_order)
        self.visits.append(visit)
        self.visit_order += 1
    
    def clear(self):
        """Clear all tracked visits."""
        self.visits = []
        self.visit_order = 0
        self.depth_stack = [0]
    
    def get_execution_path(self) -> str:
        """Get a formatted execution path showing visited nodes."""
        if not self.visits:
            return "No nodes visited"
        
        lines = []
        for visit in self.visits:
            indent = "  " * visit.depth
            lines.append(f"{indent}→ {visit.node_type} ({visit.node_name})")
        
        return "\n".join(lines)
    
    def get_execution_tree(self) -> str:
        """Get a tree visualization of the execution path."""
        if not self.visits:
            return "No nodes visited"
        
        lines = []
        prev_depth = -1
        
        for i, visit in enumerate(self.visits):
            # Build tree characters
            if i == len(self.visits) - 1:
                # Last item
                connector = "└── "
                continuation = "    "
            else:
                # Check if next item has greater depth (has children)
                next_depth = self.visits[i + 1].depth if i + 1 < len(self.visits) else visit.depth - 1
                if next_depth > visit.depth:
                    connector = "├── "
                    continuation = "│   "
                else:
                    connector = "└── "
                    continuation = "    "
            
            # Build indentation
            if visit.depth == 0:
                indent = ""
            else:
                indent = "".join(
                    ("│   " if j < visit.depth - 1 else continuation)
                    for j in range(visit.depth - 1)
                )
            
            # Format node info
            node_info = f"{visit.node_type}"
            if visit.node_name:
                node_info += f" [{visit.node_name}]"
            
            line = f"{indent}{connector}{node_info}"
            lines.append(line)
        
        return "\n".join(lines)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the execution."""
        if not self.visits:
            return {"total_visits": 0, "node_types": {}, "max_depth": 0}
        
        node_counts = {}
        max_depth = 0
        
        for visit in self.visits:
            node_counts[visit.node_type] = node_counts.get(visit.node_type, 0) + 1
            max_depth = max(max_depth, visit.depth)
        
        return {
            "total_visits": len(self.visits),
            "unique_types": len(node_counts),
            "node_types": node_counts,
            "max_depth": max_depth,
        }
    
    def get_summary(self) -> str:
        """Get a summary of execution statistics."""
        stats = self.get_statistics()
        
        if stats["total_visits"] == 0:
            return "No nodes visited"
        
        lines = [
            f"Execution Summary:",
            f"  Total node visits: {stats['total_visits']}",
            f"  Unique node types: {stats['unique_types']}",
            f"  Maximum depth: {stats['max_depth']}",
            f"",
            f"Node visit breakdown:",
        ]
        
        # Sort by count descending
        for node_type, count in sorted(stats['node_types'].items(), key=lambda x: -x[1]):
            lines.append(f"  {node_type}: {count}")
        
        return "\n".join(lines)


def _get_node_display_name(node) -> str:
    """Extract a display name for a node."""
    node_type = type(node).__name__
    
    if node_type == "NumberNode":
        return f"value={node.tok.value}"
    elif node_type == "StringNode":
        return f"value={node.tok.value!r}"
    elif node_type == "BooleanNode":
        return f"value={node.tok.value}"
    elif node_type == "VarAccessNode":
        return f"name={node.var_name_tok.value}"
    elif node_type == "VarDeclarationNode":
        return f"name={node.var_name_tok.value}"
    elif node_type == "AssignmentNode":
        return f"name={node.var_name_tok.value}"
    elif node_type == "BinOpNode":
        return f"op={node.op_tok.type}"
    elif node_type == "UnaryOpNode":
        return f"op={node.op_tok.type}"
    elif node_type == "PrintNode":
        return "print"
    elif node_type == "IfNode":
        return "if"
    elif node_type == "WhileNode":
        return "while"
    elif node_type == "ForNode":
        return "for"
    elif node_type == "FuncDefNode":
        return f"name={node.var_name_tok.value}"
    elif node_type == "CallNode":
        return f"call={node.var_name_tok.value}"
    elif node_type == "ReturnNode":
        return "return"
    elif node_type == "BlockNode":
        return f"block({len(node.statements)} statements)"
    elif node_type == "ProgramNode":
        return f"program({len(node.statements)} statements)"
    
    return ""


# Global tracker instance
_global_tracker = NodeTracker()


def get_tracker() -> NodeTracker:
    """Get the global node tracker."""
    return _global_tracker


def enable_tracking():
    """Enable node tracking globally."""
    _global_tracker.enable()


def disable_tracking():
    """Disable node tracking globally."""
    _global_tracker.disable()


def clear_tracking():
    """Clear all tracked visits."""
    _global_tracker.clear()


def get_execution_path() -> str:
    """Get formatted execution path."""
    return _global_tracker.get_execution_path()


def get_execution_tree() -> str:
    """Get tree visualization of execution."""
    return _global_tracker.get_execution_tree()


def get_summary() -> str:
    """Get execution summary."""
    return _global_tracker.get_summary()
