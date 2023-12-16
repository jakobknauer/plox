# pylint: disable=function-redefined
# mypy: disable-error-code="no-redef"

from plox import expressions as expr
from plox.visitor import visitor


class AstPrinter:
    @visitor(expr.Binary)
    def print(self, binary: expr.Binary) -> str:
        return f"{binary.operator.lexeme} {self.print(binary.left)} {self.print(binary.right)}"

    @visitor(expr.Grouping)
    def print(self, grouping: expr.Grouping) -> str:
        return f"({self.print(grouping.expression)})"

    @visitor(expr.Literal)
    def print(self, literal: expr.Literal) -> str:
        return f"{literal.value}"

    @visitor(expr.Unary)
    def print(self, unary: expr.Unary) -> str:
        return f"{unary.operator.lexeme} {self.print(unary.right)}"
