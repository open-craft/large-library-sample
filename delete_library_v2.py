from openedx.core.djangoapps.content_libraries.models import ContentLibrary
from openedx_learning.api.authoring_models import DraftSideEffect, EntityList, EntityListRow, LearningPackage


def delete_library(library_key: str):
    """
    Deletes the library with library_key.
    """
    print(f"Deleting library with id {library_key}")

    ContentLibrary.objects.filter(learning_package__key=library_key).delete()
    EntityListRow.objects.filter(entity__learning_package__key=library_key).delete()
    EntityList.objects.filter(entitylistrow__isnull=True, container_versions__isnull=True).delete()
    DraftSideEffect.objects.filter(cause__draft_change_log__learning_package__key=library_key).delete()
    LearningPackage.objects.filter(key=library_key).delete()


library_key = ""
if not library_key:
    raise ValueError("Set library key")
delete_library(library_key)
