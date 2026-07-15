#!/usr/bin/env python3
"""
MinIO Orphan File Cleanup Script for RAGFlow.

Scans MinIO for files not referenced by any database record, backs them up
to a separate bucket, then deletes the originals. Supports backup list and
restore operations.

Usage:
    # Dry-run scan only (safe, no modifications)
    python cleanup_minio_orphans.py

    # Scan and clean (back up orphans, then delete originals)
    python cleanup_minio_orphans.py --cleanup

    # List backed-up files
    python cleanup_minio_orphans.py --list-backups

    # Restore backed-up files (with optional time range)
    python cleanup_minio_orphans.py --restore --after 2026-06-01T00:00:00 --before 2026-06-30T23:59:59

    # Clean up backups older than retention period
    python cleanup_minio_orphans.py --cleanup-backups
"""

import argparse
import logging
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Iterator

# ---------------------------------------------------------------------------
# Constants (modifiable)
# ---------------------------------------------------------------------------
BACKUP_BUCKET = "ragflow-orphan-backup"
DEFAULT_RETENTION_DAYS = 30
RETENTION_DAYS = DEFAULT_RETENTION_DAYS
BATCH_SIZE = 1000

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logger = logging.getLogger("minio-cleanup")


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(fmt)
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(level)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class OrphanStats:
    bucket: str
    kb_name: str = ""
    total_objects: int = 0
    total_bytes: int = 0
    referenced_objects: int = 0
    referenced_bytes: int = 0
    orphan_objects: int = 0
    orphan_bytes: int = 0


@dataclass
class BackupEntry:
    backup_key: str
    backup_time: datetime
    source_bucket: str
    source_key: str
    size: int = 0


@dataclass
class CleanupResult:
    stats: list[OrphanStats] = field(default_factory=list)
    backed_up: int = 0
    backed_up_bytes: int = 0
    backup_failed: int = 0
    deleted: int = 0


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------
def get_project_base():
    """Return the project root directory (where 'common' package lives)."""
    current = os.path.abspath(os.path.dirname(__file__))
    while True:
        if os.path.isdir(os.path.join(current, "common")) and os.path.isdir(os.path.join(current, "conf")):
            return current

        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def load_config(config_path: str | None = None) -> dict:
    """Load service_conf.yaml and return merged config dict."""
    project_base = get_project_base()
    sys.path.insert(0, project_base)

    from common.config_utils import load_yaml_conf, decrypt_database_config

    if config_path is None:
        conf_dir = os.path.join(project_base, "conf")
        config_path = os.path.join(conf_dir, "service_conf.yaml")
        if not os.path.exists(config_path):
            config_path = os.path.join(conf_dir, "service_conf.yaml.template")

    if not os.path.isabs(config_path):
        config_path = os.path.join(project_base, config_path)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    cfg = load_yaml_conf(config_path)
    if not isinstance(cfg, dict):
        raise ValueError(f"Invalid config file: {config_path}")

    return cfg


def get_minio_config(config: dict) -> dict:
    """Extract and decrypt MinIO configuration."""
    from common.config_utils import decrypt_database_config

    minio_cfg = decrypt_database_config(name="minio")
    # decrypt_database_config reads from global CONFIGS; ensure it matches our loaded config
    if not minio_cfg or "host" not in minio_cfg:
        raw = config.get("minio", {})
        minio_cfg = {
            "user": raw.get("user", os.environ.get("MINIO_USER", "rag_flow")),
            "password": raw.get("password", os.environ.get("MINIO_PASSWORD", "infini_rag_flow")),
            "host": raw.get("host", f"{os.environ.get('MINIO_HOST', 'minio')}:{os.environ.get('MINIO_PORT', '9000')}"),
            "bucket": raw.get("bucket") or os.environ.get("MINIO_BUCKET") or None,
            "prefix_path": raw.get("prefix_path") or os.environ.get("MINIO_PREFIX_PATH") or None,
            "secure": raw.get("secure", os.environ.get("MINIO_SECURE", False)),
            "verify": raw.get("verify", True),
        }
    return minio_cfg


def get_db_config(config: dict) -> dict:
    """Extract database configuration."""
    db_type = os.environ.get("DB_TYPE", "mysql")
    from common.config_utils import decrypt_database_config

    if db_type == "postgres":
        return decrypt_database_config(name="postgres")
    return decrypt_database_config(name="mysql")


def is_single_bucket_mode(minio_cfg: dict) -> bool:
    return bool(minio_cfg.get("bucket") and minio_cfg["bucket"] != "")


# ---------------------------------------------------------------------------
# MinIO helpers
# ---------------------------------------------------------------------------
def connect_minio(minio_cfg: dict):
    """Create a MinIO client from config."""
    from minio import Minio

    host = minio_cfg["host"]
    secure = minio_cfg.get("secure", False)
    if isinstance(secure, str):
        secure = secure.lower() in ("true", "1", "yes")

    client = Minio(
        host,
        access_key=minio_cfg["user"],
        secret_key=minio_cfg["password"],
        secure=secure,
    )
    # Quick connectivity check
    client.list_buckets()
    return client


def resolve_key_prefix(minio_cfg: dict, bucket: str) -> str:
    """
    Return the key prefix for objects in the given logical bucket,
    accounting for prefix_path and single-bucket mode.
    """
    prefix = ""
    if minio_cfg.get("prefix_path"):
        prefix += f"{minio_cfg['prefix_path']}/"
    if is_single_bucket_mode(minio_cfg):
        prefix += f"{bucket}/"
    return prefix


def logical_bucket_key(minio_cfg: dict, key: str) -> tuple[str | None, str]:
    """
    Given a physical key from a single-bucket-mode listing,
    extract (logical_bucket, inner_key).

    In multi-bucket mode, returns (None, key) — caller already knows the bucket.
    """
    if not is_single_bucket_mode(minio_cfg):
        return (None, key)

    pfx = minio_cfg.get("prefix_path")
    rest = key
    if pfx:
        pfx_slash = f"{pfx}/"
        if rest.startswith(pfx_slash):
            rest = rest[len(pfx_slash) :]

    parts = rest.split("/", 1)
    if len(parts) == 2:
        return (parts[0], parts[1])
    return (parts[0], "")


def list_bucket_objects(client, bucket: str, prefix: str = "") -> Iterator[tuple[str, int]]:
    """Yield (key, size) for all objects in a bucket, optionally filtered by prefix."""
    try:
        objects = client.list_objects(bucket, prefix=prefix, recursive=True)
        for obj in objects:
            yield (obj.object_name, obj.size)
    except Exception:
        logger.exception("Failed to list objects in bucket=%s prefix=%s", bucket, prefix)


def list_bucket_prefixes(client, bucket: str, prefix: str = "") -> list[str]:
    """List top-level 'directory' prefixes in a bucket."""
    prefixes = []
    try:
        objects = client.list_objects(bucket, prefix=prefix, delimiter="/")
        for obj in objects:
            if obj.is_dir and obj.object_name:
                prefixes.append(obj.object_name.rstrip("/"))
    except Exception:
        logger.exception("Failed to list prefixes in bucket=%s prefix=%s", bucket, prefix)
    return prefixes


def ensure_bucket(client, bucket: str) -> None:
    """Create bucket if it doesn't exist."""
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            logger.info("Created bucket: %s", bucket)
    except Exception:
        logger.exception("Failed to ensure bucket: %s", bucket)
        raise


def copy_object(client, src_bucket: str, src_key: str, dst_bucket: str, dst_key: str) -> bool:
    """Server-side copy. Returns True on success."""
    from minio.commonconfig import CopySource

    try:
        client.copy_object(dst_bucket, dst_key, CopySource(src_bucket, src_key))
        return True
    except Exception:
        logger.exception("Copy failed: %s/%s -> %s/%s", src_bucket, src_key, dst_bucket, dst_key)
        return False


def remove_objects_batch(client, bucket: str, keys: list[str], audit_log) -> int:
    """Batch delete objects. Returns count of successfully deleted objects."""
    from minio.deleteobjects import DeleteObject

    if not keys:
        return 0

    deleted = 0
    # Process in batches
    for i in range(0, len(keys), BATCH_SIZE):
        batch = keys[i : i + BATCH_SIZE]
        try:
            errors = list(client.remove_objects(bucket, [DeleteObject(k) for k in batch]))
            failed_keys = set()
            for err in errors:
                logger.error("Delete error: %s/%s: %s", bucket, err.name, err.message)
                if err.name:
                    failed_keys.add(err.name)
            batch_deleted = len(batch) - len(errors)
            deleted += batch_deleted
            if len(failed_keys) == len(errors):
                for k in batch:
                    if k not in failed_keys:
                        audit_log.write(f"{datetime.now().isoformat()} | DELETE | {bucket}/{k}\n")
            else:
                logger.warning("Skipped per-object delete audit for bucket=%s due to unnamed delete errors", bucket)
        except Exception:
            logger.exception("Batch delete failed for bucket=%s, batch_size=%d", bucket, len(batch))
    return deleted


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
class DatabaseReader:
    """Read-only database access for referenced file discovery."""

    def __init__(self, db_config: dict):
        db_type = os.environ.get("DB_TYPE", "mysql")
        db_name = db_config["name"]
        db_user = db_config["user"]
        db_password = db_config["password"]
        db_host = db_config["host"]
        db_port = int(db_config.get("port", 3306))

        if db_type == "postgres":
            from playhouse.pool import PooledPostgresqlDatabase

            self.db = PooledPostgresqlDatabase(
                db_name,
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port,
                max_connections=5,
            )
        else:
            from playhouse.pool import PooledMySQLDatabase

            self.db = PooledMySQLDatabase(
                db_name,
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port,
                max_connections=5,
            )

    def connect(self):
        if self.db.is_closed():
            self.db.connect()

    def close(self):
        if not self.db.is_closed():
            self.db.close()

    def get_valid_kb_ids(self) -> list[tuple[str, str, str]]:
        """Return [(kb_id, tenant_id, kb_name), ...] for active knowledgebases."""
        self.connect()
        try:
            cursor = self.db.execute_sql(
                "SELECT id, tenant_id, name FROM knowledgebase WHERE status = '1'"
            )
            return [(row[0], row[1], row[2]) for row in cursor.fetchall()]
        finally:
            self.close()

    def get_document_keys(self, kb_id: str) -> tuple[set[str], set[str]]:
        """
        Return (locations, thumbnails) for active documents in a knowledgebase.
        location and thumbnail are the MinIO keys.
        """
        self.connect()
        try:
            cursor = self.db.execute_sql(
                "SELECT location, thumbnail FROM document WHERE kb_id = %s AND status = '1'",
                (kb_id,),
            )
            rows = cursor.fetchall()
            locations = set()
            thumbnails = set()
            for row in rows:
                if row[0]:
                    locations.add(row[0])
                if row[1] and not row[1].startswith("data:"):
                    thumbnails.add(row[1])
            return locations, thumbnails
        finally:
            self.close()

    def get_kb_id_for_bucket(self, bucket: str) -> tuple[str | None, str | None]:
        """Check if a bucket name maps to a valid kb_id. Returns (kb_id, kb_name) or (None, None)."""
        self.connect()
        try:
            cursor = self.db.execute_sql(
                "SELECT id, name FROM knowledgebase WHERE id = %s AND status = '1'",
                (bucket,),
            )
            row = cursor.fetchone()
            return (row[0], row[1]) if row else (None, None)
        finally:
            self.close()

    def get_all_tenant_ids(self) -> list[str]:
        """Return all tenant IDs."""
        self.connect()
        try:
            cursor = self.db.execute_sql("SELECT id FROM tenant WHERE status = '1'")
            return [row[0] for row in cursor.fetchall()]
        finally:
            self.close()

    def get_download_files(self, tenant_id: str) -> set[str]:
        """Return MinIO keys for download files belonging to a user."""
        self.connect()
        try:
            cursor = self.db.execute_sql(
                "SELECT location FROM file WHERE tenant_id = %s AND location IS NOT NULL AND location != ''",
                (tenant_id,),
            )
            return {row[0] for row in cursor.fetchall()}
        finally:
            self.close()


# ---------------------------------------------------------------------------
# Doc Store (ES/Infinity) helpers - for chunk img_id
# ---------------------------------------------------------------------------
class DocStoreReader:
    """Best-effort reader for chunk img_ids from the document store."""

    def __init__(self, config: dict):
        self.config = config
        self.doc_engine = os.environ.get("DOC_ENGINE", "elasticsearch").lower()
        self.client = None

    def connect(self) -> bool:
        try:
            if self.doc_engine == "elasticsearch":
                es_cfg = self.config.get("es", {})
                hosts = es_cfg.get("hosts", "http://localhost:9200")
                self.client = Elasticsearch(
                    hosts.split(","),
                    basic_auth=(es_cfg.get("username", ""), es_cfg.get("password", "")),
                    verify_certs=False,
                    request_timeout=60,
                )
            elif self.doc_engine == "infinity":
                from infinity import infinity

                infinity_cfg = self.config.get("infinity", {})
                uri = infinity_cfg.get("uri", "infinity:23817")
                self.client = infinity.connect(uri)
            return True
        except Exception:
            logger.warning("Doc store (%s) not reachable — skipping chunk image scan", self.doc_engine)
            return False

    def get_chunk_img_keys(self, kb_id: str, tenant_id: str) -> set[str]:
        """
        Query doc store for chunk img_ids belonging to a knowledgebase.

        img_id format stored in doc store: "{kb_id}-{chunk_object_key}"
        The chunk_object_key is the MinIO key of the chunk image.
        """
        if self.client is None:
            return set()

        try:
            if self.doc_engine == "elasticsearch":
                return self._es_get_img_keys(kb_id, tenant_id)
            # Infinity path not implemented in this version; skip gracefully
            return set()
        except Exception:
            logger.debug("Failed to query chunk images for kb_id=%s", kb_id)
            return set()

    def can_scan_chunk_images(self) -> bool:
        """Return whether chunk image references can be read reliably."""
        return self.client is not None and self.doc_engine == "elasticsearch"

    def _es_get_img_keys(self, kb_id: str, tenant_id: str) -> set[str]:
        index_name = f"ragflow_{tenant_id}"
        if not self.client.indices.exists(index=index_name):
            return set()

        img_keys = set()
        try:
            # Use scroll API for potentially large result sets
            result = self.client.search(
                index=index_name,
                body={
                    "query": {"term": {"kb_id": kb_id}},
                    "_source": ["img_id"],
                    "size": 1000,
                },
                scroll="2m",
            )

            scroll_id = result.get("_scroll_id")
            hits = result.get("hits", {}).get("hits", [])

            while hits:
                for hit in hits:
                    img_id = hit.get("_source", {}).get("img_id", "")
                    if img_id:
                        # img_id format: "{kb_id}-{objname}"
                        # Strip the "{kb_id}-" prefix to get the actual MinIO key
                        prefix = f"{kb_id}-"
                        if img_id.startswith(prefix):
                            objname = img_id[len(prefix) :]
                            if objname:
                                img_keys.add(objname)

                if scroll_id:
                    result = self.client.scroll(scroll_id=scroll_id, scroll="2m")
                    hits = result.get("hits", {}).get("hits", [])
                else:
                    break

            if scroll_id:
                try:
                    self.client.clear_scroll(scroll_id=scroll_id)
                except Exception:
                    pass
        except Exception:
            logger.debug("ES query failed for index=%s kb_id=%s", index_name, kb_id)

        return img_keys


# ---------------------------------------------------------------------------
# Bucket classification
# ---------------------------------------------------------------------------
SYSTEM_BUCKETS = {".minio.sys", "sandbox-artifacts"}


def _looks_like_kb_id(name: str) -> bool:
    """Check if a name looks like a RAGFlow kb_id (32 hex chars)."""
    if len(name) != 32:
        return False
    return all(c in "0123456789abcdef" for c in name.lower())


def classify_buckets(
    client,
    minio_cfg: dict,
    db: DatabaseReader,
    buckets_filter: list[str] | None,
    skip_buckets: list[str] | None,
) -> list[tuple[str, str, bool]]:
    """
    Discover RAGFlow-related buckets.
    Returns [(bucket_name, kb_name_or_label, is_download_bucket), ...].
    kb_name_or_label is the KB name (for KB buckets) or a label like "user-downloads".
    """
    skip_set = set(skip_buckets or []) | SYSTEM_BUCKETS
    skip_set.add(BACKUP_BUCKET)

    if is_single_bucket_mode(minio_cfg):
        physical_bucket = minio_cfg["bucket"]
        if physical_bucket in skip_set:
            return []

        prefix = minio_cfg.get("prefix_path", "")
        if prefix:
            prefix = f"{prefix}/"

        kb_map = {row[0]: row[2] for row in db.get_valid_kb_ids()}
        tenant_ids = set(db.get_all_tenant_ids())

        # In single-bucket mode, list top-level prefixes as logical buckets.
        # Only process prefixes that map to live RAGFlow records; arbitrary
        # top-level directories in the physical bucket are not safe to scan.
        prefixes = list_bucket_prefixes(client, physical_bucket, prefix)
        result = []
        for pfx in prefixes:
            logical = pfx
            if prefix and logical.startswith(prefix):
                logical = logical[len(prefix) :]
            if logical in skip_set:
                continue
            if buckets_filter and logical not in buckets_filter:
                continue

            if logical in kb_map:
                result.append((logical, kb_map[logical], False))
                continue

            if logical.endswith("-downloads"):
                tenant_id = logical[: -len("-downloads")]
                if tenant_id in tenant_ids:
                    result.append((logical, logical, True))
                    continue

            logger.debug("Skipping non-RAGFlow logical bucket prefix: %s", logical)
        return result

    # Multi-bucket mode
    try:
        all_buckets = [b.name for b in client.list_buckets()]
    except Exception:
        logger.exception("Failed to list buckets")
        return []

    kb_map = {row[0]: row[2] for row in db.get_valid_kb_ids()}

    result = []
    for bname in all_buckets:
        if bname in skip_set:
            continue
        if buckets_filter and bname not in buckets_filter:
            continue

        is_download = bname.endswith("-downloads")
        if _looks_like_kb_id(bname):
            label = kb_map.get(bname, bname)
            result.append((bname, label, False))
        elif is_download:
            result.append((bname, bname, True))

    return result


# ---------------------------------------------------------------------------
# Orphan discovery
# ---------------------------------------------------------------------------
def get_referenced_keys(
    minio_cfg: dict,
    bucket: str,
    is_download: bool,
    db: DatabaseReader,
    doc_store: DocStoreReader | None,
) -> set[str]:
    """
    Build the complete set of MinIO keys that SHOULD exist for a given bucket
    according to database and document store records.
    """
    referenced: set[str] = set()

    if is_download:
        # {user_id}-downloads bucket: files belong to that tenant
        user_id = bucket.replace("-downloads", "")
        keys = db.get_download_files(user_id)
        referenced.update(keys)
        logger.debug("  Bucket %s: %d download file references from DB", bucket, len(keys))
        return referenced

    # KB bucket: documents + thumbnails + chunk images
    locations, thumbnails = db.get_document_keys(bucket)
    referenced.update(locations)
    referenced.update(t for t in thumbnails if t)

    logger.debug(
        "  Bucket %s: %d locations + %d thumbnails from DB",
        bucket,
        len(locations),
        len(thumbnails),
    )

    # Chunk images from doc store
    if doc_store and doc_store.client:
        kb_list = db.get_valid_kb_ids()
        tenant_id = None
        for kid, tid, _ in kb_list:
            if kid == bucket:
                tenant_id = tid
                break
        if tenant_id:
            img_keys = doc_store.get_chunk_img_keys(bucket, tenant_id)
            referenced.update(img_keys)
            logger.debug(
                "  Bucket %s: %d chunk images from doc store",
                bucket,
                len(img_keys),
            )

    return referenced


def scan_bucket(
    client,
    minio_cfg: dict,
    bucket: str,
    is_download: bool,
    db: DatabaseReader,
    doc_store: DocStoreReader | None,
) -> OrphanStats:
    """Compare MinIO objects against DB references for one bucket."""
    # Get referenced keys
    referenced = get_referenced_keys(minio_cfg, bucket, is_download, db, doc_store)
    referenced_sizes: dict[str, int] = {}

    # Get actual keys from MinIO
    prefix = resolve_key_prefix(minio_cfg, bucket)
    actual: dict[str, int] = {}  # key -> size

    physical_bucket = minio_cfg.get("bucket") if is_single_bucket_mode(minio_cfg) else bucket
    if not physical_bucket:
        physical_bucket = bucket

    for key, size in list_bucket_objects(client, physical_bucket, prefix):
        if is_single_bucket_mode(minio_cfg):
            lb, inner = logical_bucket_key(minio_cfg, key)
            if lb != bucket:
                continue
            actual[inner] = size
        else:
            actual[key] = size

    # Compute stats
    total_objects = len(actual)
    total_bytes = sum(actual.values())

    # Match referenced keys against actual
    referenced_objects = 0
    referenced_bytes = 0
    orphans: dict[str, int] = {}
    for key, size in actual.items():
        if key in referenced:
            referenced_objects += 1
            referenced_bytes += size
        else:
            orphans[key] = size

    orphan_objects = len(orphans)
    orphan_bytes = sum(orphans.values())

    # Get KB name for display
    kb_name = ""
    if not is_download:
        _, kb_name = db.get_kb_id_for_bucket(bucket)

    return OrphanStats(
        bucket=bucket,
        kb_name=kb_name or "",
        total_objects=total_objects,
        total_bytes=total_bytes,
        referenced_objects=referenced_objects,
        referenced_bytes=referenced_bytes,
        orphan_objects=orphan_objects,
        orphan_bytes=orphan_bytes,
    )


# ---------------------------------------------------------------------------
# Backup operations
# ---------------------------------------------------------------------------
def backup_orphans(
    client,
    minio_cfg: dict,
    bucket: str,
    orphans: dict[str, int],
    audit_log,
) -> tuple[int, int, int]:
    """
    Copy orphan files to the backup bucket.
    Returns (backed_up, failed, total_bytes).
    """
    ensure_bucket(client, BACKUP_BUCKET)
    timestamp = datetime.now().isoformat(timespec="seconds")
    backed_up = 0
    failed = 0
    total_bytes = 0

    physical_bucket = minio_cfg.get("bucket") if is_single_bucket_mode(minio_cfg) else bucket
    if not physical_bucket:
        physical_bucket = bucket

    for key, size in orphans.items():
        # Resolve the physical key for the source
        if is_single_bucket_mode(minio_cfg):
            source_key = resolve_key_prefix(minio_cfg, bucket) + key
        else:
            source_key = key

        backup_key = f"{timestamp}/{bucket}/{key}"

        if copy_object(client, physical_bucket, source_key, BACKUP_BUCKET, backup_key):
            backed_up += 1
            total_bytes += size
            audit_log.write(
                f"{datetime.now().isoformat()} | BACKUP | {BACKUP_BUCKET}/{backup_key} "
                f"(source: {physical_bucket}/{source_key}, size: {size})\n"
            )
        else:
            failed += 1
            logger.error("Backup failed for %s/%s", bucket, key)

    return backed_up, failed, total_bytes


def delete_originals_after_backup(
    client,
    minio_cfg: dict,
    bucket: str,
    orphans: dict[str, int],
    audit_log,
) -> int:
    """Delete original orphan files from their source bucket."""
    physical_bucket = minio_cfg.get("bucket") if is_single_bucket_mode(minio_cfg) else bucket
    if not physical_bucket:
        physical_bucket = bucket

    keys = []
    for key in orphans:
        if is_single_bucket_mode(minio_cfg):
            keys.append(resolve_key_prefix(minio_cfg, bucket) + key)
        else:
            keys.append(key)

    return remove_objects_batch(client, physical_bucket, keys, audit_log)


# ---------------------------------------------------------------------------
# Backup listing and parsing
# ---------------------------------------------------------------------------
def parse_backup_key(backup_key: str, size: int = 0) -> BackupEntry | None:
    """
    Parse a backup key in format: {timestamp}/{source_bucket}/{source_key}
    """
    parts = backup_key.split("/", 2)
    if len(parts) < 3:
        return None
    try:
        backup_time = datetime.fromisoformat(parts[0])
    except ValueError:
        return None
    return BackupEntry(
        backup_key=backup_key,
        backup_time=backup_time,
        source_bucket=parts[1],
        source_key=parts[2],
        size=size,
    )


def list_backup_entries(
    client,
    after: datetime | None = None,
    before: datetime | None = None,
) -> list[BackupEntry]:
    """List all backup entries in the backup bucket, optionally filtered by time."""
    entries: list[BackupEntry] = []
    try:
        if not client.bucket_exists(BACKUP_BUCKET):
            return entries
    except Exception:
        return entries

    for key, size in list_bucket_objects(client, BACKUP_BUCKET):
        entry = parse_backup_key(key, size)
        if entry is None:
            continue
        if after and entry.backup_time < after:
            continue
        if before and entry.backup_time > before:
            continue
        entries.append(entry)

    entries.sort(key=lambda e: e.backup_time)
    return entries


def find_old_backups(client) -> tuple[list[BackupEntry], int, int]:
    """Find backups older than RETENTION_DAYS. Returns (entries, count, total_size)."""
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    old = []
    for entry in list_backup_entries(client):
        if entry.backup_time < cutoff:
            old.append(entry)
    total_size = sum(e.size for e in old)
    return old, len(old), total_size


def delete_backup_entries(client, entries: list[BackupEntry], audit_log) -> int:
    """Delete specific backup entries from the backup bucket."""
    if not entries:
        return 0
    logger.info("Deleting %d backup entries...", len(entries))
    # Group entries to avoid giant batches
    keys = [e.backup_key for e in entries]
    return remove_objects_batch(client, BACKUP_BUCKET, keys, audit_log)


# ---------------------------------------------------------------------------
# Restore operations
# ---------------------------------------------------------------------------
def resolve_restore_target(minio_cfg: dict, entry: BackupEntry) -> tuple[str, str]:
    """Return the physical bucket/key where a backup entry should be restored."""
    if is_single_bucket_mode(minio_cfg):
        return minio_cfg["bucket"], resolve_key_prefix(minio_cfg, entry.source_bucket) + entry.source_key
    return entry.source_bucket, entry.source_key


def restore_backup_entries(
    client,
    minio_cfg: dict,
    entries: list[BackupEntry],
    delete_after: bool = False,
    audit_log=None,
) -> tuple[int, int]:
    """
    Restore backed-up files to their original locations.
    Returns (restored, failed).
    """
    restored = 0
    failed = 0

    for entry in entries:
        try:
            restore_bucket, restore_key = resolve_restore_target(minio_cfg, entry)

            # Ensure source bucket exists
            if not client.bucket_exists(restore_bucket):
                client.make_bucket(restore_bucket)
                logger.info("Created bucket: %s", restore_bucket)

            if copy_object(client, BACKUP_BUCKET, entry.backup_key, restore_bucket, restore_key):
                restored += 1
                if audit_log:
                    audit_log.write(
                        f"{datetime.now().isoformat()} | RESTORE | "
                        f"{restore_bucket}/{restore_key} (from: {BACKUP_BUCKET}/{entry.backup_key})\n"
                    )
                if delete_after:
                    try:
                        client.remove_object(BACKUP_BUCKET, entry.backup_key)
                        if audit_log:
                            audit_log.write(
                                f"{datetime.now().isoformat()} | DELETE-BACKUP | "
                                f"{BACKUP_BUCKET}/{entry.backup_key}\n"
                            )
                    except Exception:
                        logger.warning("Failed to delete backup after restore: %s", entry.backup_key)
            else:
                failed += 1
        except Exception:
            logger.exception("Restore failed for %s -> %s/%s", entry.backup_key, entry.source_bucket, entry.source_key)
            failed += 1

    return restored, failed


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
def format_size(num_bytes: int) -> str:
    if num_bytes >= 1024 * 1024 * 1024:
        return f"{num_bytes / (1024**3):.1f} GB"
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes / (1024**2):.1f} MB"
    if num_bytes >= 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes} B"


def format_pct(part: int, total: int) -> str:
    if total == 0:
        return "0.0%"
    return f"{part / total * 100:.1f}%"


def print_header(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_orphan_stats(stats: OrphanStats) -> None:
    kb_display = f' (KB: "{stats.kb_name}")' if stats.kb_name else ""
    print(f"\n--- {stats.bucket}{kb_display} ---")
    print(f"  Total objects:     {stats.total_objects:>8} ({format_size(stats.total_bytes)})")
    print(f"  Referenced:        {stats.referenced_objects:>8} ({format_size(stats.referenced_bytes)})")
    print(f"  Orphans:           {stats.orphan_objects:>8} ({format_size(stats.orphan_bytes)})")


def print_grand_total(stats_list: list[OrphanStats]) -> None:
    total_objs = sum(s.total_objects for s in stats_list)
    total_bytes = sum(s.total_bytes for s in stats_list)
    ref_objs = sum(s.referenced_objects for s in stats_list)
    ref_bytes = sum(s.referenced_bytes for s in stats_list)
    orphan_objs = sum(s.orphan_objects for s in stats_list)
    orphan_bytes = sum(s.orphan_bytes for s in stats_list)

    print_header("GRAND TOTAL")
    print(f"  Buckets scanned:   {len(stats_list)}")
    print(f"  Total objects:     {total_objs:>8} ({format_size(total_bytes)})")
    print(f"  Referenced:        {ref_objs:>8} ({format_size(ref_bytes)})")
    print(f"  Orphans:           {orphan_objs:>8} ({format_size(orphan_bytes)}, {format_pct(orphan_bytes, total_bytes)})")


def print_backup_table(entries: list[BackupEntry]) -> None:
    if not entries:
        print("  (no backups)")
        return

    total_size = 0
    print(f"  {'Backup Time':<20} {'Source Bucket':<34} {'Source Key':<40} {'Size':>10}")
    print(f"  {'-'*20} {'-'*34} {'-'*40} {'-'*10}")
    for e in entries:
        bucket_trunc = e.source_bucket if len(e.source_bucket) <= 34 else e.source_bucket[:31] + "..."
        key_trunc = e.source_key if len(e.source_key) <= 40 else e.source_key[:37] + "..."
        print(f"  {e.backup_time.isoformat(timespec='seconds'):<20} {bucket_trunc:<34} {key_trunc:<40} {format_size(e.size):>10}")
        total_size += e.size
    print(f"  {'─' * 20} {'─' * 34} {'─' * 40} {'─' * 10}")
    print(f"  Total: {len(entries)} objects ({format_size(total_size)})")


# ---------------------------------------------------------------------------
# Try import for Elasticsearch (may not be available in all deployments)
# ---------------------------------------------------------------------------
try:
    from elasticsearch import Elasticsearch
except ImportError:
    Elasticsearch = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------
def run_cleanup(
    client,
    minio_cfg: dict,
    db: DatabaseReader,
    doc_store: DocStoreReader | None,
    args: argparse.Namespace,
    audit_log,
    buckets: list[tuple[str, str, bool]],
) -> int:
    """Run the cleanup flow: scan -> backup -> delete -> check old backups."""
    # Phase 1: Scan all buckets
    print_header("Phase 1: Scanning for Orphans")
    all_stats: list[OrphanStats] = []
    all_orphans: dict[str, dict[str, int]] = {}  # bucket -> {key: size}

    for bucket, label, is_download in buckets:
        logger.info("Scanning bucket: %s", bucket)
        stats = scan_bucket(client, minio_cfg, bucket, is_download, db, doc_store)
        stats.kb_name = label
        all_stats.append(stats)
        print_orphan_stats(stats)

        if stats.orphan_objects > 0:
            # Re-scan to get the actual orphan keys with sizes
            prefix = resolve_key_prefix(minio_cfg, bucket)
            physical_bucket = minio_cfg.get("bucket") if is_single_bucket_mode(minio_cfg) else bucket
            if not physical_bucket:
                physical_bucket = bucket

            referenced = get_referenced_keys(minio_cfg, bucket, is_download, db, doc_store)
            orphans: dict[str, int] = {}
            for key, size in list_bucket_objects(client, physical_bucket, prefix):
                if is_single_bucket_mode(minio_cfg):
                    lb, inner = logical_bucket_key(minio_cfg, key)
                    if lb != bucket:
                        continue
                    lookup_key = inner
                else:
                    lookup_key = key
                if lookup_key not in referenced:
                    orphans[lookup_key] = size
            all_orphans[bucket] = orphans

    print_grand_total(all_stats)

    total_orphans = sum(s.orphan_objects for s in all_stats)
    if total_orphans == 0:
        print("\nNo orphan files found. Nothing to clean up.")
        return 0

    # Phase 2: Confirm and execute backup + delete
    print_header("Phase 2: Backup and Cleanup")
    total_orphan_bytes = sum(s.orphan_bytes for s in all_stats)
    print(f"  Total orphans to back up: {total_orphans} objects ({format_size(total_orphan_bytes)})")
    print(f"  Backup bucket: {BACKUP_BUCKET}")
    print()

    if not args.yes:
        try:
            confirm = input("Proceed with backup and cleanup? Type CLEANUP to confirm: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return 1
        if confirm != "CLEANUP":
            print("Aborted (confirmation did not match 'CLEANUP').")
            return 0

    result = CleanupResult(stats=all_stats)

    for bucket, orphans in all_orphans.items():
        if not orphans:
            continue
        logger.info("Backing up %d orphans from bucket %s...", len(orphans), bucket)
        bu, bf, bb = backup_orphans(client, minio_cfg, bucket, orphans, audit_log)
        result.backed_up += bu
        result.backup_failed += bf
        result.backed_up_bytes += bb
        print(f"  [Backup] {bucket}: {bu}/{len(orphans)} backed up ({format_size(bb)})")

        if bf > 0:
            logger.error("Some backups failed for bucket %s — skipping delete for this bucket", bucket)
            continue

        logger.info("Deleting %d original orphans from bucket %s...", len(orphans), bucket)
        deleted = delete_originals_after_backup(client, minio_cfg, bucket, orphans, audit_log)
        result.deleted += deleted
        print(f"  [Delete] {bucket}: {deleted}/{len(orphans)} originals deleted")

    print(f"\n  Summary: backed up {result.backed_up}, deleted {result.deleted}")

    # Phase 3: Check old backups
    print_header("Phase 3: Old Backup Check")
    old_entries, old_count, old_size = find_old_backups(client)
    if old_count > 0:
        print(f"  Found {old_count} backup entries older than {RETENTION_DAYS} days ({format_size(old_size)})")
        cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
        print(f"  (backups before {cutoff.isoformat(timespec='seconds')})")
        print()
        if not args.yes:
            try:
                confirm = input("Delete these old backups? Type DELETE-OLD to confirm (or press Enter to skip): ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nSkipped.")
                confirm = ""
            if confirm == "DELETE-OLD":
                deleted = delete_backup_entries(client, old_entries, audit_log)
                print(f"  Deleted {deleted} old backup entries")
            else:
                print("  Skipped (use --cleanup-backups to clean old backups later)")
        else:
            deleted = delete_backup_entries(client, old_entries, audit_log)
            print(f"  Deleted {deleted} old backup entries")
    else:
        print(f"  No backup entries older than {RETENTION_DAYS} days.")

    return 0


def run_list_backups(client, args: argparse.Namespace) -> int:
    """List backed-up files."""
    try:
        if not client.bucket_exists(BACKUP_BUCKET):
            print(f"Backup bucket '{BACKUP_BUCKET}' does not exist. No backups found.")
            return 0
    except Exception:
        print(f"Backup bucket '{BACKUP_BUCKET}' not accessible.")
        return 1

    after = None
    before = None
    if args.after:
        try:
            after = datetime.fromisoformat(args.after)
        except ValueError:
            print(f"Invalid --after timestamp: {args.after}")
            return 1
    if args.before:
        try:
            before = datetime.fromisoformat(args.before)
        except ValueError:
            print(f"Invalid --before timestamp: {args.before}")
            return 1

    entries = list_backup_entries(client, after=after, before=before)

    print_header("Backup Files")
    time_range = ""
    if after and before:
        time_range = f" ({after.isoformat()} to {before.isoformat()})"
    elif after:
        time_range = f" (after {after.isoformat()})"
    elif before:
        time_range = f" (before {before.isoformat()})"
    print(f"  Bucket: {BACKUP_BUCKET}{time_range}\n")
    print_backup_table(entries)
    return 0


def run_restore(client, minio_cfg: dict, args: argparse.Namespace, audit_log) -> int:
    """Restore backed-up files."""
    try:
        if not client.bucket_exists(BACKUP_BUCKET):
            print(f"Backup bucket '{BACKUP_BUCKET}' does not exist.")
            return 1
    except Exception:
        print(f"Cannot access backup bucket '{BACKUP_BUCKET}'.")
        return 1

    after = None
    before = None
    if args.after:
        try:
            after = datetime.fromisoformat(args.after)
        except ValueError:
            print(f"Invalid --after timestamp: {args.after}")
            return 1
    if args.before:
        try:
            before = datetime.fromisoformat(args.before)
        except ValueError:
            print(f"Invalid --before timestamp: {args.before}")
            return 1

    entries = list_backup_entries(client, after=after, before=before)

    if not entries:
        print("No backup entries found matching the specified time range.")
        return 0

    total_size = sum(e.size for e in entries)
    print_header("Restore from Backup")
    print(f"  Will restore {len(entries)} objects ({format_size(total_size)})")
    print(f"  Delete backup after restore: {'Yes' if args.delete_backup else 'No'}")
    print()
    print_backup_table(entries[:20])
    if len(entries) > 20:
        print(f"  ... and {len(entries) - 20} more entries")

    if not args.yes:
        try:
            confirm = input("\nProceed with restore? Type RESTORE to confirm: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return 1
        if confirm != "RESTORE":
            print("Aborted.")
            return 0

    restored, failed = restore_backup_entries(client, minio_cfg, entries, delete_after=args.delete_backup, audit_log=audit_log)
    print(f"\n  Restored: {restored}/{len(entries)}")
    if failed > 0:
        print(f"  Failed:   {failed}")
    return 0 if failed == 0 else 1


def run_cleanup_backups(client, args: argparse.Namespace, audit_log) -> int:
    """Delete backup entries older than retention period."""
    old_entries, old_count, old_size = find_old_backups(client)

    if old_count == 0:
        print(f"No backup entries older than {RETENTION_DAYS} days.")
        return 0

    print_header("Clean Old Backups")
    print(f"  Found {old_count} entries older than {RETENTION_DAYS} days ({format_size(old_size)})")
    print()

    if not args.yes:
        try:
            confirm = input("Delete these old backups? Type DELETE-OLD to confirm: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return 1
        if confirm != "DELETE-OLD":
            print("Aborted.")
            return 0

    deleted = delete_backup_entries(client, old_entries, audit_log)
    print(f"  Deleted {deleted} old backup entries")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="RAGFlow MinIO Orphan File Cleanup (with Backup & Restore)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run scan (safe, no changes)
  python cleanup_minio_orphans.py

  # Clean orphans: backup to separate bucket, then delete originals
  python cleanup_minio_orphans.py --cleanup

  # Clean specific buckets only
  python cleanup_minio_orphans.py --cleanup --buckets abc123,def456

  # List all backup entries
  python cleanup_minio_orphans.py --list-backups

  # Restore backups from a specific time range
  python cleanup_minio_orphans.py --restore --after 2026-06-01T00:00:00 --before 2026-06-30T23:59:59

  # Clean backups older than retention period
  python cleanup_minio_orphans.py --cleanup-backups


Configuration is read from conf/service_conf.yaml (same as RAGFlow).
All MinIO credentials and database settings come from the config file.
        """,
    )

    parser.add_argument(
        "--config",
        default=None,
        help="Path to service_conf.yaml (default: conf/service_conf.yaml)",
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--cleanup", action="store_true", help="Scan orphans, backup, then delete originals")
    mode.add_argument("--list-backups", action="store_true", help="List all backed-up files")
    mode.add_argument("--restore", action="store_true", help="Restore backed-up files to original locations")
    mode.add_argument("--cleanup-backups", action="store_true", help="Delete backup entries older than retention period")

    parser.add_argument("--dry-run", action="store_true", default=True, help="Scan only, no modifications (default)")
    parser.add_argument("--buckets", help="Only process specified buckets (comma-separated)")
    parser.add_argument("--skip-buckets", help="Skip specified buckets (comma-separated)")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip all confirmation prompts")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    # Restore options
    parser.add_argument("--after", help="Restore/list backups after this time (ISO format)")
    parser.add_argument("--before", help="Restore/list backups before this time (ISO format)")
    parser.add_argument("--delete-backup", action="store_true", help="Delete backup entries after successful restore")

    parser.add_argument("--retention-days", type=int, default=DEFAULT_RETENTION_DAYS, help=f"Backup retention days (default: {DEFAULT_RETENTION_DAYS})")
    parser.add_argument("--audit-log", default="/tmp/minio_cleanup_audit.log", help="Audit log file path")

    args = parser.parse_args()

    # Global retention override
    global RETENTION_DAYS
    RETENTION_DAYS = args.retention_days

    # Setup
    setup_logging(args.verbose)

    # Determine mode
    is_cleanup = args.cleanup
    is_restore = args.restore
    is_list_backups = args.list_backups
    is_cleanup_backups = args.cleanup_backups
    is_dry_run = not (is_cleanup or is_restore or is_list_backups or is_cleanup_backups)

    # -----------------------------------------------------------------------
    # Load config
    # -----------------------------------------------------------------------
    print_header("Initialization")
    try:
        raw_config = load_config(args.config)
        minio_cfg = get_minio_config(raw_config)
        db_config = get_db_config(raw_config)
        print(f"  Config: OK")
        print(f"  MinIO:  {minio_cfg['host']} (user={minio_cfg['user']})")
        single_bucket = is_single_bucket_mode(minio_cfg)
        print(f"  Mode:   {'single-bucket' if single_bucket else 'multi-bucket'}")
        if single_bucket:
            print(f"  Physical bucket: {minio_cfg['bucket']}")
    except Exception as e:
        logger.error("Failed to load config: %s", e)
        return 1

    # -----------------------------------------------------------------------
    # Connect to services
    # -----------------------------------------------------------------------
    try:
        client = connect_minio(minio_cfg)
        print(f"  MinIO connection: OK")
    except Exception as e:
        logger.error("Failed to connect to MinIO: %s", e)
        return 1

    try:
        db = DatabaseReader(db_config)
        # Quick connectivity test
        kb_count = len(db.get_valid_kb_ids())
        print(f"  Database: OK ({kb_count} active knowledgebases)")
    except Exception as e:
        logger.error("Failed to connect to database: %s", e)
        return 1

    doc_store = None
    try:
        doc_store = DocStoreReader(raw_config)
        if doc_store.connect():
            print(f"  Doc store: OK ({doc_store.doc_engine})")
        else:
            print(f"  Doc store: unavailable (chunk image scan will be skipped)")
    except Exception as e:
        logger.warning("Doc store connection failed: %s", e)
        print(f"  Doc store: unavailable")

    # Skip ES import error gracefully
    if doc_store is None or doc_store.client is None:
        if Elasticsearch is None and os.environ.get("DOC_ENGINE", "elasticsearch") == "elasticsearch":
            print("  Note: elasticsearch package not available, chunk image scan skipped")

    # -----------------------------------------------------------------------
    # Open audit log
    # -----------------------------------------------------------------------
    try:
        audit_log = open(args.audit_log, "a")
        audit_log.write(f"\n{'=' * 60}\n")
        audit_log.write(f"Session: {datetime.now().isoformat()}\n")
        audit_log.write(f"Mode: {'cleanup' if is_cleanup else 'restore' if is_restore else 'list' if is_list_backups else 'cleanup-backups' if is_cleanup_backups else 'dry-run'}\n")
        audit_log.write(f"{'=' * 60}\n")
    except Exception as e:
        logger.error("Cannot open audit log %s: %s", args.audit_log, e)
        return 1

    # -----------------------------------------------------------------------
    # Execute mode
    # -----------------------------------------------------------------------
    exit_code = 0

    try:
        # Parse bucket filters
        buckets_filter = [b.strip() for b in args.buckets.split(",") if b.strip()] if args.buckets else None
        skip_buckets = [b.strip() for b in args.skip_buckets.split(",") if b.strip()] if args.skip_buckets else None

        if is_dry_run:
            print_header("DRY RUN — no modifications will be made")
            buckets = classify_buckets(client, minio_cfg, db, buckets_filter, skip_buckets)
            if not buckets:
                print("No RAGFlow-related buckets found.")
                return 0

            print(f"  Skipped system buckets: {', '.join(sorted(SYSTEM_BUCKETS))}")
            if not is_single_bucket_mode(minio_cfg):
                print(f"  Skipped backup bucket: {BACKUP_BUCKET}")
            skipped_non_ragflow = []
            for b in [b.name for b in client.list_buckets()]:
                if b not in SYSTEM_BUCKETS and b != BACKUP_BUCKET:
                    if not _looks_like_kb_id(b) and not b.endswith("-downloads"):
                        skipped_non_ragflow.append(b)
            if skipped_non_ragflow:
                print(f"  Skipped non-RAGFlow buckets: {', '.join(skipped_non_ragflow)}")
            print()

            all_stats = []
            for bucket, label, is_download in buckets:
                logger.info("Scanning bucket: %s", bucket)
                stats = scan_bucket(client, minio_cfg, bucket, is_download, db, doc_store)
                stats.kb_name = label
                all_stats.append(stats)
                print_orphan_stats(stats)

            print_grand_total(all_stats)
            print("\n[DRY RUN] No files were modified. Use --cleanup to backup and delete orphans.")

        elif is_list_backups:
            exit_code = run_list_backups(client, args)

        elif is_restore:
            exit_code = run_restore(client, minio_cfg, args, audit_log)

        elif is_cleanup_backups:
            exit_code = run_cleanup_backups(client, args, audit_log)

        elif is_cleanup:
            if doc_store is None or not doc_store.can_scan_chunk_images():
                print(
                    "Refusing to run cleanup because chunk image references cannot be scanned reliably. "
                    "Make the Elasticsearch doc store reachable before deleting MinIO orphans."
                )
                return 1
            buckets = classify_buckets(client, minio_cfg, db, buckets_filter, skip_buckets)
            if not buckets:
                print("No RAGFlow-related buckets found.")
                return 0
            exit_code = run_cleanup(client, minio_cfg, db, doc_store, args, audit_log, buckets)

    finally:
        audit_log.close()
        db.close()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
