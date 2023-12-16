from plox import expression
from plox.visitor import visitor


class AstPrinter:
    @visitor(expression.Expr)
    def print(self, expr: expression.Expr) -> str:
        pass

    @visitor(expression.Binary)
    def print_binary(self, binary: expression.Binary) -> str:
        return f"{binary.operator.lexeme} {self.print(binary.left)} {self.print(binary.right)}"

    @visitor(expression.Grouping)
    def print_grouping(self, grouping: expression.Grouping) -> str:
        return f"({self.print(grouping.expression)})"

    @visitor(expression.Literal)
    def print_literal(self, literal: expression.Literal) -> str:
        return f"{literal.value}"

    @visitor(expression.Unary)
    def print_unary(self, unary: expression.Unary) -> str:
        return f"{unary.operator.lexeme} {self.print(unary.right)}"
