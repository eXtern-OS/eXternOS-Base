from typing import *

from apt.progress.base import (
    AcquireProgress,
    CdromProgress,
    InstallProgress,
    OpProgress,
)

class Cdrom:
    def add(self, progress: CdromProgress) -> bool: ...
    def ident(self, progress: CdromProgress) -> str: ...

def gettext(msg: str) -> str: ...

class Configuration(dict):
    def find_file(self, key: str, default: str="") -> str: ...
    def find_dir(self, key: str, default: str="") -> str: ...
    def dump(self) -> str: ...
    def find(self, key: str, default: object=None) -> str: ...
    def find_b(self, key: str, default: bool=False) -> bool: ...
    def set(self, key: str, value: str) -> None: ...
    def value_list(self, key: str) -> List[str]: ...
    def clear(self, root: object=None) -> None: ...

config = Configuration()

def init() -> None: ...
def init_config() -> None: ...
def init_system() -> None: ...

# FIXME: this is really a file-like object
def md5sum(o: Any) -> str: ...

class Dependency():
    comp_type: str
    comp_type_deb: str
    target_pkg: Package
    target_ver: str
    dep_type_untranslated: str
    def all_targets(self) -> List[Version]: ...

# This is really a SystemError, but we don't want to expose that
class Error(Exception):
    pass

class Package():
    name: str
    version_list: List[Version]
    architecture: str
    id: int
    current_ver: Version
    essential: bool
    section: str
    current_state: int
    inst_state: int
    def get_fullname(self, pretty: bool=False) -> str: ...

class ProblemResolver:
    def __init__(self, cache: DepCache) -> None: ...
    def clear(self, pkg: Package) -> None: ...
    def protect(self, pkg: Package) -> None: ...
    def remove(self, pkg: Package) -> None: ...
    def install_protect(self) -> None: ...
    def resolve(self, fix_broken: bool=True) -> bool: ...
    def resolve_by_keep(self) -> bool: ...

CURSTATE_CONFIG_FILES: int
INSTSTATE_REINSTREQ: int
INSTSTATE_HOLD_REINSTREQ: int
    
class Version():
    ver_str: str
    hash: int
    file_list: List[PackageFile]
    translated_description: Description
    installed_size: int
    size: int
    arch: str
    downloadable: bool
    id: int
    section: str
    priority: int
    priority_str: str
    provides_list: List[Tuple[str,str,str]]
    def parent_pkg(self) -> Package: ...
    multi_arch: int
    MULTI_ARCH_ALL: int
    MULTI_ARCH_ALLOWED: int
    MULTI_ARCH_ALL_ALLOWED: int
    MULTI_ARCH_ALL_FOREIGN: int
    MULTI_ARCH_FOREIGN: int
    MULTI_ARCH_NO: int
    MULTI_ARCH_NONE: int
    MULTI_ARCH_SAME: int

class Description():
    file_list: List[PackageFile]

class PackageRecords():
    homepage: str
    short_desc: str
    long_desc: str
    source_pkg: str
    source_ver: str
    record: str
    filename: str
    md5_hash: str
    sha1_hash: str
    sha256_hash: str
    hashes: HashStringList
    def __init__(self, cache: Cache) -> None: ...
    def lookup(self, packagefile: PackageFile, index: int=0) -> bool: ...

class PackageFile(Iterable):
    architecture: str
    archive: str
    codename: str
    component: str
    filename: str
    id: int
    index_type: str
    label: str
    not_automatic: bool
    not_source: bool
    origin: str
    site: str
    size: int
    version: str

class TagFile(Iterable):
    def __init__(self, file: object, bytes: bool=False) -> None: ...
    def __iter__(self) -> Iterator[TagSection]: ...

class TagSection(Mapping):
    def __init__(self, str) -> None: ...
    def __getitem__(self, key: object) -> str: ...
    def __contains__(self, key: object) -> bool: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[str]: ...

def version_compare(a: str, b: str) -> int: ...

def get_lock(file: str, errors: bool=False) -> int: ...
def pkgsystem_lock() -> None: ...
def pkgsystem_unlock() -> None: ...
def read_config_file(configuration: Configuration, path: str) -> None: ...
def read_config_dir(configuration: Configuration, path: str) -> None: ...

def pkgsystem_lock_inner() -> None: ...
def pkgsystem_unlock_inner() -> None: ...
def pkgsystem_is_locked() -> bool: ...

SELSTATE_HOLD: int

class Acquire:
    fetch_needed: int
    items: List[AcquireItem]
    partial_present: int
    total_needed: int
    workers: List[AcquireWorker]
    RESULT_CANCELLED: int
    RESULT_FAILED: int
    RESULT_CONTINUE: int
    def __init__(self, progress: AcquireProgress=None) -> None: ...
    def run(self) -> int: ...
    def shutdown(self) -> None: ...
    def get_lock(self, path: str) -> None: ...

class AcquireWorker:
    current_size: int
    total_size: int
    status: str
    
class AcquireItem:
    active_subprocess: str
    complete: bool
    desc_uri: str
    destfile: str
    error_text: str
    filesize: int
    id: int
    is_trusted: bool
    local: bool
    mode: str
    partialsize: int
    status: int
    
    STAT_IDLE: int
    STAT_FETCHING: int
    STAT_DONE: int
    STAT_ERROR: int
    STAT_AUTH_ERROR: int
    STAT_TRANSIENT_NETWORK_ERROR: int

class AcquireItemDesc:
    description: str
    owner: AcquireItem
    shortdesc: str
    uri: str

class Hashes:
    def __init__(self, object: Union[bytes, object, int]) -> None: ...
    hashes: HashStringList

class HashString:
    def __init__(self, type: str, hash: Optional[str] = None) -> None: ...
    def verify_file(self, filename: str) -> bool: ...

    hashtype: str
    hashvalue: str
    usable: bool

class HashStringList:
    def append(self, object: HashString) -> None: ...
    def find(self, type: str = "") -> HashString: ...
    def verify_file(self, filename: str) -> bool: ...

    file_size: int
    usable: bool

class AcquireFile(AcquireItem):
    def __init__(self, owner: Acquire, uri: str, hash: Optional[Union[HashStringList, str]], size: int=0, descr: str="", short_descr: str="", destdir: str="", destfile: str="") -> None: ...

class IndexFile:
    def archive_uri(self, path: str) -> str: ...
    describe: str
    exists: bool
    has_packages: bool
    is_trusted: bool
    label: str
    size: int
    
class SourceRecordFiles:

    hashes: HashStringList
    path: str
    size: int
    type: str

class SourceRecords:
    def lookup(self, name: str) -> bool: ...
    def restart(self) -> None: ...
    def step(self) -> bool: ...
    binaries: List[str]
    version: str
    files: List[SourceRecordFiles]
    index: IndexFile
    package: str
    section: str

class ActionGroup:
    def __init__(self, depcache: DepCache) -> None: ...

class SourceList():
    def read_main_list(self) -> None: ...
    def find_index(self, PackageFile) -> IndexFile: ...

class PackageManager():
    RESULT_FAILED: int
    RESULT_COMPLETED: int
    RESULT_INCOMPLETE: int
    def __init__(self, depcache: DepCache) -> None: ...
    def get_archives(self, fetcher: Acquire, list: SourceList, recs: PackageRecords) -> bool: ...

class Cache(dict):
    packages: List[Package]
    def __init__(self, progress: OpProgress=None) -> None: ...
    
class DepCache():
    broken_count: int
    inst_count: int
    del_count: int
    keep_count: int
    usr_size: int
    policy: Policy
    def __init__(self, cache: Cache) -> None: ...
    def init(self, progress: OpProgress=None) -> None: ...
    def get_candidate_ver(self, pkg: Package) -> Version: ...
    def set_candidate_ver(self, pkg: Package, ver: Version) -> bool: ...
    def marked_install(self, pkg: Package) -> bool: ...
    def marked_upgrade(self, pkg: Package) -> bool: ...
    def marked_keep(self, pkg: Package) -> bool: ...
    def marked_downgrade(self, pkg: Package) -> bool: ...
    def marked_delete(self, pkg: Package) -> bool: ...
    def marked_reinstall(self, pkg: Package) -> bool: ...

    def is_upgradable(self, pkg: Package) -> bool: ...
    def is_garbage(self, pkg: Package) -> bool: ...
    def is_auto_installed(self, pkg: Package) -> bool: ...
    def is_inst_broken(self, pkg: Package) -> bool: ...
    def is_now_broken(self, pkg: Package) -> bool: ...

    def mark_keep(self, pkg: Package) -> None: ...
    def mark_install(self, pkg: Package, auto_inst: bool=True, from_user: bool=True) -> None: ...
    def mark_delete(self, pkg: Package, purge: bool=False) -> None: ...
    def mark_auto(self, pkg: Package, auto: bool) -> None: ...
    def commit(self, acquire_progress: AcquireProgress, install_progress: InstallProgress) -> None: ...

    def upgrade(self, dist_upgrade: bool=True) -> bool: ...

class Policy():
    def get_priority(self, pkg: Union[Package, PackageFile]) -> int: ...

class SystemLock():
    def __enter__(self) -> None: ...
    def __exit__(self, typ: object, value: object, traceback: object) -> None: ...
    
class FileLock():
    def __init__(self, path: str) -> None: ...
    def __enter__(self) -> None: ...
    def __exit__(self, typ: object, value: object, traceback: object) -> None: ...

def upstream_version(ver: str) -> str: ...
def get_architectures() -> List[str]: ...    
