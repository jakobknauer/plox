# pylint: disable=function-redefined
# mypy: disable-error-code="no-redef"

from plox import expression
from plox.visitor import visitor


class AstPrinter:
    @visitor(expression.Binary)
    def print(self, binary: expression.Binary) -> str:
        return f"{binary.operator.lexeme} {self.print(binary.left)} {self.print(binary.right)}"

    @visitor(expression.Grouping)
    def print(self, grouping: expression.Grouping) -> str:
        return f"({self.print(grouping.expression)})"

    @visitor(expression.Literal)
    def print(self, literal: expression.Literal) -> str:
        return f"{literal.value}"

    @visitor(expression.Unary)
    def print(self, unary: expression.Unary) -> str:
        return f"{unary.operator.lexeme} {self.print(unary.right)}"
