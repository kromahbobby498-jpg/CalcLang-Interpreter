import sys
import re

# Token types
tokens = [
    'NUMBER', 'ID', 'PLUS', 'MINUS', 'MUL', 'DIV',
    'GT', 'LT', 'EQ', 'GE', 'LE', 'NE',
    'LPAREN', 'RPAREN', 'COMMA', 'ASSIGN',
    'IF', 'THEN', 'ELSE', 'END', 'DEF', 'PRINT'
]

# Regex for tokens
token_regex = {
    'NUMBER': r'\d+(\.\d+)?',
    'ID': r'[a-zA-Z_]\w*',
    'PLUS': r'\+', 'MINUS': r'-', 'MUL': r'\*', 'DIV': r'/',
    'EQ': r'==', 'NE': r'!=', 'GE': r'>=', 'LE': r'<=', 'GT': r'>', 'LT': r'<',
    'LPAREN': r'\(', 'RPAREN': r'\)', 'COMMA': r',', 'ASSIGN': r'='
}

keywords = {'if': 'IF', 'then': 'THEN', 'else': 'ELSE', 'end': 'END', 'def': 'DEF', 'print': 'PRINT'}

class Lexer:
    def __init__(self, code):
        self.code = code
        self.pos = 0
        self.tokens = []

    def tokenize(self):
        while self.pos < len(self.code):
            match = None
            if self.code[self.pos].isspace():
                self.pos += 1
                continue
            for token_type, pattern in token_regex.items():
                regex = re.compile(pattern)
                match = regex.match(self.code, self.pos)
                if match:
                    value = match.group(0)
                    if token_type == 'ID' and value in keywords:
                        self.tokens.append((keywords[value], value))
                    else:
                        if token_type == 'NUMBER':
                            value = float(value)
                        self.tokens.append((token_type, value))
                    self.pos = match.end()
                    break
            if not match:
                raise SyntaxError(f"Unexpected character: {self.code[self.pos]}")
        return self.tokens

# AST Nodes
class ASTNode: pass

class BinOpNode(ASTNode):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

class NumberNode(ASTNode):
    def __init__(self, value):
        self.value = value

class VarNode(ASTNode):
    def __init__(self, name):
        self.name = name

class AssignNode(ASTNode):
    def __init__(self, var, expr):
        self.var = var
        self.expr = expr

class IfNode(ASTNode):
    def __init__(self, cond, then_body, else_body):
        self.cond = cond
        self.then_body = then_body
        self.else_body = else_body

class FuncDefNode(ASTNode):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class FuncCallNode(ASTNode):
    def __init__(self, name, args):
        self.name = name
        self.args = args

class PrintNode(ASTNode):
    def __init__(self, expr):
        self.expr = expr

# Parser
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current_token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def eat(self, expected_type):
        token = self.current_token()
        if token and token[0] == expected_type:
            self.pos += 1
            return token[1]
        raise SyntaxError(f"Expected {expected_type}, got {token}")

    def parse_program(self):
        statements = []
        while self.current_token():
            statements.append(self.parse_statement())
        return statements

    def parse_statement(self):
        token = self.current_token()
        if token[0] == 'ID':
            if self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1][0] == 'ASSIGN':
                var_name = self.eat('ID')
                self.eat('ASSIGN')
                expr = self.parse_expression()
                return AssignNode(var_name, expr)
            else:
                expr = self.parse_expression()
                return expr
        elif token[0] == 'IF':
            return self.parse_if()
        elif token[0] == 'DEF':
            return self.parse_func_def()
        elif token[0] == 'PRINT':
            self.eat('PRINT')
            expr = self.parse_expression()
            return PrintNode(expr)
        else:
            return self.parse_expression()

    def parse_if(self):
        self.eat('IF')
        cond = self.parse_expression()
        self.eat('THEN')
        then_body = []
        while self.current_token() and self.current_token()[0] not in ('ELSE', 'END'):
            then_body.append(self.parse_statement())
        else_body = []
        if self.current_token() and self.current_token()[0] == 'ELSE':
            self.eat('ELSE')
            while self.current_token() and self.current_token()[0] != 'END':
                else_body.append(self.parse_statement())
        self.eat('END')
        return IfNode(cond, then_body, else_body)

    def parse_func_def(self):
        self.eat('DEF')
        name = self.eat('ID')
        self.eat('LPAREN')
        params = []
        if self.current_token() and self.current_token()[0] == 'ID':
            params.append(self.eat('ID'))
            while self.current_token() and self.current_token()[0] == 'COMMA':
                self.eat('COMMA')
                params.append(self.eat('ID'))
        self.eat('RPAREN')
        body = []
        while self.current_token() and self.current_token()[0] != 'END':
            body.append(self.parse_statement())
        self.eat('END')
        return FuncDefNode(name, params, body)

    def parse_expression(self):
        node = self.parse_term()
        while self.current_token() and self.current_token()[0] in ('PLUS', 'MINUS', 'GT', 'LT', 'EQ', 'GE', 'LE', 'NE'):
            op = self.eat(self.current_token()[0])
            right = self.parse_term()
            node = BinOpNode(op, node, right)
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.current_token() and self.current_token()[0] in ('MUL', 'DIV'):
            op = self.eat(self.current_token()[0])
            right = self.parse_factor()
            node = BinOpNode(op, node, right)
        return node

    def parse_factor(self):
        token = self.current_token()
        if token[0] == 'NUMBER':
            val = self.eat('NUMBER')
            return NumberNode(val)
        elif token[0] == 'ID':
            name = self.eat('ID')
            if self.current_token() and self.current_token()[0] == 'LPAREN':
                self.eat('LPAREN')
                args = []
                if self.current_token() and self.current_token()[0] != 'RPAREN':
                    args.append(self.parse_expression())
                    while self.current_token() and self.current_token()[0] == 'COMMA':
                        self.eat('COMMA')
                        args.append(self.parse_expression())
                self.eat('RPAREN')
                return FuncCallNode(name, args)
            return VarNode(name)
        elif token[0] == 'LPAREN':
            self.eat('LPAREN')
            expr = self.parse_expression()
            self.eat('RPAREN')
            return expr
        raise SyntaxError(f"Unexpected factor token: {token}")

# Interpreter
class Interpreter:
    def __init__(self):
        self.globals = {}
        self.functions = {}
        self.call_stack = []

    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        return getattr(self, method_name, self.no_visit)(node)

    def no_visit(self, node):
        raise RuntimeError(f"No visit method for {type(node).__name__}")

    def visit_NumberNode(self, node):
        return node.value

    def visit_VarNode(self, node):
        # Look up in local scope first (top of call stack), then globals
        if self.call_stack:
            local_vars = self.call_stack[-1][1]
            if node.name in local_vars:
                return local_vars[node.name]
        if node.name in self.globals:
            return self.globals[node.name]
        raise NameError(f"Undefined variable: {node.name}")

    def visit_AssignNode(self, node):
        val = self.visit(node.expr)
        if self.call_stack:
            self.call_stack[-1][1][node.var] = val
        else:
            self.globals[node.var] = val
        return val

    def visit_BinOpNode(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        ops = {
            '+': lambda: left + right, '-': lambda: left - right,
            '*': lambda: left * right, '/': lambda: left / right if right != 0 else (_ for _ in ()).throw(ZeroDivisionError("division by zero")),
            '>': lambda: float(left > right), '<': lambda: float(left < right),
            '==': lambda: float(left == right), '>=': lambda: float(left >= right),
            '<=': lambda: float(left <= right), '!=': lambda: float(left != right)
        }
        if node.op in ops:
            try:
                return ops[node.op]()
            except ZeroDivisionError as e:
                self.print_call_stack_trace()
                raise e
        raise ValueError(f"Unknown operator: {node.op}")

    def visit_IfNode(self, node):
        print("Evaluating if condition")
        cond_val = self.visit(node.cond)
        last_val = None
        if cond_val != 0:
            print("Entering if block")
            for stmt in node.then_body:
                last_val = self.visit(stmt)
        else:
            print("Entering else block")
            for stmt in node.else_body:
                last_val = self.visit(stmt)
        return last_val

    def visit_FuncDefNode(self, node):
        self.functions[node.name] = (node.params, node.body)
        return f"Function {node.name} defined"

    def visit_FuncCallNode(self, node):
        if node.name not in self.functions:
            raise NameError(f"Undefined function: {node.name}")
        params, body = self.functions[node.name]
        if len(node.args) != len(params):
            raise TypeError(f"{node.name}() takes {len(params)} arguments but {len(node.args)} were given")
        
        # Evaluate arguments in current scope
        arg_vals = [self.visit(arg) for arg in node.args]
        new_locals = dict(zip(params, arg_vals))
        
        # Track on call stack
        self.call_stack.append((node.name, new_locals))
        print(f"Call stack push: {node.name} with locals {new_locals}")
        
        last_val = None
        try:
            for stmt in body:
                last_val = self.visit(stmt)
        finally:
            print(f"Call stack pop: {node.name}")
            self.call_stack.pop()
            
        return last_val

    def visit_PrintNode(self, node):
        val = self.visit(node.expr)
        print(val)
        return val

    def interpret(self, ast):
        last_val = None
        for stmt in ast:
            last_val = self.visit(stmt)
        return last_val

    def print_call_stack_trace(self):
        print("--- Call Stack Trace on Error ---")
        for i, (func_name, locals_dict) in enumerate(reversed(self.call_stack)):
            print(f"  Frame {len(self.call_stack) - i}: In function '{func_name}' with local variables: {locals_dict}")
        print("---------------------------------")

def repl():
    interpreter = Interpreter()
    print("CalcLang Interactive REPL. Type 'exit' to quit.")
    while True:
        try:
            code = input("CalcLang> ")
            if code.strip() == "exit":
                break
            if not code.strip():
                continue
            
            # Handle multi-line block accumulation
            open_blocks = code.count("def ") + code.count("if ")
            close_blocks = code.count("end")
            while open_blocks > close_blocks:
                extra_line = input("... ")
                code += "\n" + extra_line
                open_blocks = code.count("def ") + code.count("if ")
                close_blocks = code.count("end")
                
            lexer = Lexer(code)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse_program()
            res = interpreter.interpret(ast)
            if res is not None:
                print(f"Result: {res}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    repl()