"""
AST Debug visualization - provides pretty-print and tree view of AST nodes.
"""

def ast_to_tree(node, indent=0, is_last=True, prefix="", visited_nodes=None):
    """
    Convert AST node to a tree string representation.
    
    Args:
        node: AST node to visualize
        indent: Current indentation level
        is_last: Whether this is the last child of its parent
        prefix: Current line prefix
        visited_nodes: Set of nodes that were visited during execution (for highlighting)
    
    Returns:
        Formatted tree string
    """
    if node is None:
        return ""
    
    # Build the tree characters
    connector = "└── " if is_last else "├── "
    new_prefix = prefix + ("    " if is_last else "│   ")
    
    # Get node type and details
    node_type = type(node).__name__
    node_info = _get_node_info(node)
    
    # Build the line
    line = f"{prefix}{connector}{node_type}"
    if node_info:
        line += f" {node_info}"
    
    # Mark visited nodes
    if visited_nodes and id(node) in visited_nodes:
        line += " ✓"
    
    result = line + "\n"
    
    # Get and process children
    children = _get_node_children(node)
    for i, child in enumerate(children):
        is_last_child = (i == len(children) - 1)
        result += ast_to_tree(child, indent + 1, is_last_child, new_prefix, visited_nodes)
    
    return result


def _get_node_info(node):
    """Get a brief info string for a node."""
    node_type = type(node).__name__
    
    if node_type == "NumberNode":
        return f"value={node.tok.value}"
    elif node_type == "BooleanNode":
        return f"value={node.tok.value}"
    elif node_type == "StringNode":
        return f"value={node.tok.value!r}"
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
    elif node_type == "FuncDefNode":
        return f"name={node.var_name_tok.value}"
    elif node_type == "CallNode":
        return f"name={node.var_name_tok.value}"
    
    return ""


def _get_node_children(node):
    """Get child nodes for an AST node."""
    node_type = type(node).__name__
    children = []
    
    if node_type == "ProgramNode":
        children = node.statements
    elif node_type == "BlockNode":
        children = node.statements
    elif node_type == "VarDeclarationNode":
        children = [node.value_node]
    elif node_type == "AssignmentNode":
        children = [node.value_node]
    elif node_type == "PrintNode":
        children = [node.expr_node]
    elif node_type == "IfNode":
        children = [node.condition_node, node.then_block]
        if node.else_block:
            children.append(node.else_block)
    elif node_type == "WhileNode":
        children = [node.condition_node, node.body_node]
    elif node_type == "ForNode":
        children = [node.init_node, node.condition_node, 
                   node.increment_node, node.body_node]
    elif node_type == "FuncDefNode":
        children = [node.body_node]
    elif node_type == "ReturnNode":
        children = [node.expr_node]
    elif node_type == "BinOpNode":
        children = [node.left_node, node.right_node]
    elif node_type == "UnaryOpNode":
        children = [node.node]
    elif node_type == "CallNode":
        children = node.arg_nodes
    
    return children


def ast_inspect(node, show_positions=False):
    """
    Print a detailed inspection of an AST node and its children.
    
    Args:
        node: AST node to inspect
        show_positions: Whether to show position information
    """
    lines = []
    _inspect_node(node, 0, lines, show_positions)
    return "\n".join(lines)


def _inspect_node(node, depth, lines, show_positions):
    """Recursively inspect a node."""
    if node is None:
        return
    
    indent = "  " * depth
    node_type = type(node).__name__
    lines.append(f"{indent}┌─ {node_type}")
    
    # Show node details
    node_type = type(node).__name__
    
    if node_type == "NumberNode":
        lines.append(f"{indent}│  value: {node.tok.value}")
        lines.append(f"{indent}│  type: {node.tok.type}")
    elif node_type == "BooleanNode":
        lines.append(f"{indent}│  value: {node.tok.value}")
    elif node_type == "StringNode":
        lines.append(f"{indent}│  value: {node.tok.value!r}")
    elif node_type == "VarAccessNode":
        lines.append(f"{indent}│  name: {node.var_name_tok.value}")
    elif node_type == "VarDeclarationNode":
        lines.append(f"{indent}│  name: {node.var_name_tok.value}")
        lines.append(f"{indent}│  value:")
        _inspect_node(node.value_node, depth + 2, lines, show_positions)
    elif node_type == "AssignmentNode":
        lines.append(f"{indent}│  name: {node.var_name_tok.value}")
        lines.append(f"{indent}│  value:")
        _inspect_node(node.value_node, depth + 2, lines, show_positions)
    elif node_type == "PrintNode":
        lines.append(f"{indent}│  expr:")
        _inspect_node(node.expr_node, depth + 2, lines, show_positions)
    elif node_type == "BinOpNode":
        lines.append(f"{indent}│  operator: {node.op_tok.type}")
        lines.append(f"{indent}│  left:")
        _inspect_node(node.left_node, depth + 2, lines, show_positions)
        lines.append(f"{indent}│  right:")
        _inspect_node(node.right_node, depth + 2, lines, show_positions)
    elif node_type == "UnaryOpNode":
        lines.append(f"{indent}│  operator: {node.op_tok.type}")
        lines.append(f"{indent}│  operand:")
        _inspect_node(node.node, depth + 2, lines, show_positions)
    elif node_type == "IfNode":
        lines.append(f"{indent}│  condition:")
        _inspect_node(node.condition_node, depth + 2, lines, show_positions)
        lines.append(f"{indent}│  then:")
        _inspect_node(node.then_block, depth + 2, lines, show_positions)
        if node.else_block:
            lines.append(f"{indent}│  else:")
            _inspect_node(node.else_block, depth + 2, lines, show_positions)
    elif node_type == "WhileNode":
        lines.append(f"{indent}│  condition:")
        _inspect_node(node.condition_node, depth + 2, lines, show_positions)
        lines.append(f"{indent}│  body:")
        _inspect_node(node.body_node, depth + 2, lines, show_positions)
    elif node_type == "ForNode":
        lines.append(f"{indent}│  init:")
        _inspect_node(node.init_node, depth + 2, lines, show_positions)
        lines.append(f"{indent}│  condition:")
        _inspect_node(node.condition_node, depth + 2, lines, show_positions)
        lines.append(f"{indent}│  increment:")
        _inspect_node(node.increment_node, depth + 2, lines, show_positions)
        lines.append(f"{indent}│  body:")
        _inspect_node(node.body_node, depth + 2, lines, show_positions)
    elif node_type == "FuncDefNode":
        lines.append(f"{indent}│  name: {node.var_name_tok.value}")
        params = [tok.value for tok in node.params_name_toks]
        lines.append(f"{indent}│  params: {params}")
        lines.append(f"{indent}│  body:")
        _inspect_node(node.body_node, depth + 2, lines, show_positions)
    elif node_type == "CallNode":
        lines.append(f"{indent}│  name: {node.var_name_tok.value}")
        lines.append(f"{indent}│  args:")
        for arg in node.arg_nodes:
            _inspect_node(arg, depth + 2, lines, show_positions)
    elif node_type == "ReturnNode":
        lines.append(f"{indent}│  expr:")
        _inspect_node(node.expr_node, depth + 2, lines, show_positions)
    elif node_type == "ProgramNode":
        lines.append(f"{indent}│  statements: {len(node.statements)}")
        for stmt in node.statements:
            _inspect_node(stmt, depth + 1, lines, show_positions)
    elif node_type == "BlockNode":
        lines.append(f"{indent}│  statements: {len(node.statements)}")
        for stmt in node.statements:
            _inspect_node(stmt, depth + 1, lines, show_positions)
    
    if show_positions:
        lines.append(f"{indent}│  pos: {node.pos_start} → {node.pos_end}")
