from types import Typ, Instance, Any, TupleType
from nodes import TypeInfo, FuncBase, Var, FuncDef, AccessorNode


# Analyse member access. This is a general operation that supports various
# different variations:
#
#   1. lvalue or non-lvalue access (i.e. setter or getter access)
#   2. supertype access (when using the super keyword; isSuper == True and
#      overrideInfo should refer to the supertype)
#
# Note that this function may return a RangeCallable type.
Typ analyse_member_access(str name, Typ typ, Context node, bool is_lvalue, bool is_super, Typ tuple_type, MessageBuilder msg, TypeInfo override_info=None):
    if isinstance(typ, Instance):
        # The base object has an instance type.
        itype = (Instance)typ
        
        info = itype.typ
        if override_info is not None:
            info = override_info
        
        # Look up the member. First look up the method dictionary.
        FuncBase method = None
        if not is_lvalue:
            method = info.get_method(name)
        
        if method is not None:
            # Found a method. The call below has a unique result for all valid
            # programs.
            itype = map_instance_to_supertype(itype, method.info)
            return expand_type_by_instance(method_type(method), itype)
        else:
            # Not a method.
            return analyse_member_var_access(name, itype, info, node, is_lvalue, is_super, msg)
    elif isinstance(typ, Any):
        # The base object has dynamic type.
        return Any()
    elif isinstance(typ, TupleType):
        # Actually look up from the tuple type.
        return analyse_member_access(name, tuple_type, node, is_lvalue, is_super, tuple_type, msg)
    else:
        # The base object has an unsupported type.
        return msg.has_no_member(typ, name, node)

# Analyse member access that does not target a method. This is logically
# part of AnalyseMemberAccess and the arguments are similar.
Typ analyse_member_var_access(str name, Instance itype, TypeInfo info, Context node, bool is_lvalue, bool is_super, MessageBuilder msg):
    # It was not a method. Try looking up a variable.
    v = lookup_member_var_or_accessor(info, name, is_lvalue)
    
    if isinstance(v, Var):
        # Found a member variable.
        
        itype = map_instance_to_supertype(itype, v.info)
        # FIX what if more than one?
        if v.typ is not None:
            return expand_type_by_instance(v.typ.typ, itype)
        else:
            # Implicit dynamic type.
            return Any()
    elif isinstance(v, FuncDef):
        # Found a getter or a setter.
        itype = map_instance_to_supertype(itype, v.info)
        return expand_type_by_instance(accessor_type(v), itype)
    
    # Could not find the member.
    if is_super:
        msg.undefined_in_superclass(name, node)
        return Any()
    else:
        return msg.has_no_member(itype, name, node)


# Find the member variable or accessor node that refers to the given member
# of a type.
AccessorNode lookup_member_var_or_accessor(TypeInfo info, str name, bool is_lvalue):
    if is_lvalue:
        return info.get_var_or_setter(name)
    else:
        return info.get_var_or_getter(name)
