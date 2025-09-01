import logging
import random

from django.contrib.auth import get_user_model
from opaque_keys.edx.locator import LibraryContainerLocator, LibraryUsageLocatorV2
from openedx.core.djangoapps.content_libraries import api as lib_api
from organizations.models import Organization

# Configuring logger while running in the shell to make it less verbose
logger = logging.getLogger("large-library-sample")
logger.propagate = False
logger_handler = logging.StreamHandler()
logger.addHandler(logger_handler)
logger_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s - %(message)s'))

random.seed(43)

User = get_user_model()

USER_EMAIL = "edx@example.com"

user = User.objects.get(email=USER_EMAIL)

SAMPLE_ORG_NAME = "SampleLibraryOrg"
LIBRARY_NAME = "Sample Large library 1"
LIBRARY_SLUG = "sample_large_library_1"
SECTION_COUNT = 50
SUBSECTION_COUNT = 30
SUBSECTION_LINK_RATE = 0.5
UNIT_COUNT = 30
UNIT_LINK_RATE = 0.5
COMPONENT_COUNT = 30
COMPONENT_LINK_RATE = 0.5
COMPONENT_TYPES = ['html', 'video', 'problem']


def create_containers(container_type: lib_api.ContainerType, count: int):
    logger.info(f"Creating {count} {container_type.value}s...")
    keys = []
    children = {}
    for i in range(1, count + 1):
        container = lib_api.create_container(
            library_key=library_key,
            container_type=container_type,
            slug=None,
            title=f"{container_type.value} {i}".capitalize(),
            user_id=user.id,
        )
        keys.append(container.container_key)
        children[container.container_key] = []
    logger.info(f"Created {count} {container_type.value}s")
    return keys, children


def create_components():
    logger.info(f"Creating {COMPONENT_COUNT} components...")
    keys = []
    for i in range(1, COMPONENT_COUNT + 1):
        block_type = random.sample(COMPONENT_TYPES, 1)[0]
        component = lib_api.create_library_block(
            library_key=library_key,
            block_type=block_type,
            definition_id=f'{LIBRARY_SLUG}_component_{i}',
            user_id=user.id,
        )
        keys.append(component.usage_key)
    logger.info(f"Created {COMPONENT_COUNT} components")
    return keys


def link_in_containers(
    container_keys: list[LibraryContainerLocator],
    children_keys: list[LibraryUsageLocatorV2] | list[LibraryContainerLocator],
    result_dict: dict[LibraryContainerLocator, list[LibraryUsageLocatorV2] | list[LibraryContainerLocator]],
    count: int,
    link_rate: float,
):
    num_containers = int(count * link_rate)
    for child_key in children_keys:
        random_containers = random.choices(container_keys, k=num_containers)
        for container_key in random_containers:
            result_dict[container_key].append(child_key)
    for container_key, container_children_keys in result_dict.items():
        logger.info(f"Saving children of {container_key}...")
        lib_api.update_container_children(
            container_key=container_key,
            children_ids=container_children_keys,
            user_id=user.id,
        )
        logger.info(f"Saved children of {container_key}")


logger.info("Generating or retrieving sample Organization...")
org, created = Organization.objects.get_or_create(
    name=SAMPLE_ORG_NAME,
    short_name=SAMPLE_ORG_NAME,
)
logger.info(f"{'Created' if created else 'Retrieved'} {org}")

logger.info("Creating the sample large library...")
library = lib_api.create_library(org=org, slug=LIBRARY_SLUG, title=LIBRARY_NAME)
library_key = library.key
logger.info(f"Created {LIBRARY_NAME}")

# Creating the sections in the library
section_keys, section_children = create_containers(
    lib_api.ContainerType.Section,
    SECTION_COUNT,
)

# Creating the subsections in the library, without adding them to sections
subsection_keys, subsection_children = create_containers(
    lib_api.ContainerType.Subsection,
    SUBSECTION_COUNT,
)

# Adding the subsections to sections using the subsection link rate
logger.info("Linking subsections to sections...")
link_in_containers(
    container_keys=section_keys,
    children_keys=subsection_keys,
    result_dict=section_children,
    count=SUBSECTION_COUNT,
    link_rate=SUBSECTION_LINK_RATE,
)
logger.info("Linked subsections to sections")

# Creating units in the library, without adding them to subsections
unit_keys, unit_children = create_containers(
    lib_api.ContainerType.Unit,
    UNIT_COUNT,
)

# Adding the units to subsections usung the unit link rate
logger.info("Linking units to subsections...")
link_in_containers(
    container_keys=subsection_keys,
    children_keys=unit_keys,
    result_dict=subsection_children,
    count=UNIT_COUNT,
    link_rate=UNIT_LINK_RATE,
)
logger.info("Linked units to subsections")

# Creating components in the library, without adding them to subsections
component_keys = create_components()

# Adding components to units using the link rate
logger.info("Linking components to units...")
link_in_containers(
    container_keys=unit_keys,
    children_keys=component_keys,
    result_dict=unit_children,
    count=COMPONENT_COUNT,
    link_rate=COMPONENT_LINK_RATE,
)
logger.info("Linked units to components")
