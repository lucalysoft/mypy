"""Subtype check for RTypes."""

from mypyc.rtypes import (
    RType, RInstance, RPrimitive, RTuple, RVoid, RTypeVisitor, RUnion,
    is_bool_rprimitive, is_int_rprimitive, is_tuple_rprimitive,
    is_short_int_rprimitive,
    is_object_rprimitive
)


def is_subtype(left: RType, right: RType) -> bool:
    if is_object_rprimitive(right):
        return True
    elif isinstance(right, RUnion):
        if isinstance(left, RUnion):
            for left_item in left.items:
                if not any(is_subtype(left_item, right_item)
                           for right_item in right.items):
                    return False
            return True
        else:
            return any(is_subtype(left, item)
                       for item in right.items)
    return left.accept(SubtypeVisitor(right))


class SubtypeVisitor(RTypeVisitor[bool]):
    """Is left a subtype of right?

    A few special cases such as right being 'object' are handled in
    is_subtype and don't need to be covered here.
    """

    def __init__(self, right: RType) -> None:
        self.right = right

    def visit_rinstance(self, left: RInstance) -> bool:
        return isinstance(self.right, RInstance) and self.right.class_ir in left.class_ir.mro

    def visit_runion(self, left: RUnion) -> bool:
        return all(is_subtype(item, self.right)
                   for item in left.items)

    def visit_rprimitive(self, left: RPrimitive) -> bool:
        if is_bool_rprimitive(left) and is_int_rprimitive(self.right):
            return True
        if is_short_int_rprimitive(left) and is_int_rprimitive(self.right):
            return True
        return left is self.right

    def visit_rtuple(self, left: RTuple) -> bool:
        if is_tuple_rprimitive(self.right):
            return True
        if isinstance(self.right, RTuple):
            return len(self.right.types) == len(left.types) and all(
                is_subtype(t1, t2) for t1, t2 in zip(left.types, self.right.types))
        return False

    def visit_rvoid(self, left: RVoid) -> bool:
        return isinstance(self.right, RVoid)
