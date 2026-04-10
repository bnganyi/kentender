# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE

"""Row-level scope composition (PERM-003).

Re-exports :mod:`kentender.services.permission_query_service` and
:class:`kentender.services.entity_scope_service` helpers so domain code can depend
on ``kentender.permissions.scope`` as a single import path.
"""

from kentender.services.entity_scope_service import (
	get_record_entity_value,
	is_central_entity_scope_user,
	list_user_procuring_entity_permissions,
	record_belongs_to_entity,
	user_has_entity_access,
)
from kentender.services.permission_query_service import (
	NO_MATCHING_DOCNAMES,
	merge_entity_scope_filters,
	name_in_docnames,
	or_filters_entity_or_docnames,
	owner_is_user,
)

__all__ = [
	"NO_MATCHING_DOCNAMES",
	"get_record_entity_value",
	"is_central_entity_scope_user",
	"list_user_procuring_entity_permissions",
	"merge_entity_scope_filters",
	"name_in_docnames",
	"or_filters_entity_or_docnames",
	"owner_is_user",
	"record_belongs_to_entity",
	"user_has_entity_access",
]
