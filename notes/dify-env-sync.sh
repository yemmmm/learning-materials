#!/usr/bin/env bash

# Synchronize a Dify 3.11 Docker Compose environment without Python.
#
# Besides rebuilding .env from .env.example, this version migrates custom
# values that moved to envs/**/*.env(.example). A value with exactly one
# structured destination is written there. Values with several destinations
# remain in a marked compatibility section at the end of .env so they are not
# silently lost.

set -euo pipefail

readonly SEP=$'\x1f'
WORK_DIR='.'
CREATE_BACKUP=true
MIGRATE_ENVS=true
TEMP_DIR=''
declare -A ENV_VALUES=()
declare -A EXAMPLE_VALUES=()
declare -A TEMPLATE_SOURCE=()
MIGRATED_COUNT=0
LEGACY_COUNT=0

log_info()    { printf '[INFO] %s\n' "$1"; }
log_success() { printf '[SUCCESS] %s\n' "$1"; }
log_warning() { printf '[WARNING] %s\n' "$1" >&2; }
log_error()   { printf '[ERROR] %s\n' "$1" >&2; }
die()         { log_error "$1"; exit 1; }

cleanup() {
    [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]] && rm -rf "$TEMP_DIR"
    return 0
}
trap cleanup EXIT

usage() {
    cat <<'EOF'
Usage: dify-env-sync.sh [--dir DIRECTORY] [--no-backup] [--no-envs-migration]

Synchronize .env with .env.example. By default, also migrate custom values
that moved to envs/**/*.env files in Dify 3.11.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dir) [[ $# -ge 2 ]] || die '--dir requires a directory'; WORK_DIR=$2; shift 2 ;;
        --no-backup) CREATE_BACKUP=false; shift ;;
        --no-envs-migration) MIGRATE_ENVS=false; shift ;;
        -h|--help) usage; exit 0 ;;
        *) die "Unknown argument: $1" ;;
    esac
done

WORK_DIR=$(cd "$WORK_DIR" && pwd)
ENV_FILE="$WORK_DIR/.env"
EXAMPLE_FILE="$WORK_DIR/.env.example"

# Emit KEY<US>VALUE records. Values retain embedded '=' characters.
parse_env() {
    awk -v sep="$SEP" '
        !/^[[:space:]]*#/ && /^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*[[:space:]]*=/ {
            line = $0
            sub(/^[[:space:]]*/, "", line)
            key = line
            sub(/[[:space:]]*=.*/, "", key)
            value = line
            sub(/^[^=]*=/, "", value)
            sub(/^[[:space:]]+|[[:space:]]+$/, "", value)
            print key sep value
        }
    ' "$1"
}

load_env_values() {
    local key value
    ENV_VALUES=()
    while IFS="$SEP" read -r key value; do
        [[ -n "$key" ]] && ENV_VALUES["$key"]=$value
    done < <(parse_env "$ENV_FILE")
}

load_example_values() {
    local key value
    EXAMPLE_VALUES=()
    while IFS="$SEP" read -r key value; do
        [[ -n "$key" ]] && EXAMPLE_VALUES["$key"]=$value
    done < <(parse_env "$EXAMPLE_FILE")
}

check_files() {
    [[ -f "$EXAMPLE_FILE" ]] || die ".env.example file not found in $WORK_DIR"
    if [[ ! -f "$ENV_FILE" ]]; then
        log_warning '.env does not exist. Creating it from .env.example.'
        cp "$EXAMPLE_FILE" "$ENV_FILE"
    fi
}

backup_env() {
    [[ "$CREATE_BACKUP" == true ]] || return 0
    local backup_dir="$WORK_DIR/env-backup" timestamp backup_file
    timestamp=$(date +'%Y%m%d_%H%M%S')
    mkdir -p "$backup_dir"
    backup_file="$backup_dir/.env.backup_$timestamp"
    cp "$ENV_FILE" "$backup_file"
    log_success "Backed up .env to ${backup_file#$WORK_DIR/}"
}

rewrite_from_template() {
    local template_file=$1 target_file=$2 overrides_file=$3 new_file
    new_file="$target_file.new"
    awk -v sep="$SEP" -v overrides_file="$overrides_file" '
        BEGIN {
            while ((getline record < overrides_file) > 0) {
                split(record, fields, sep)
                overrides[fields[1]] = substr(record, length(fields[1]) + length(sep) + 1)
            }
            close(overrides_file)
        }
        /^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*[[:space:]]*=/ {
            line = $0
            sub(/^[[:space:]]*/, "", line)
            key = line
            sub(/[[:space:]]*=.*/, "", key)
            if (key in overrides) { print key "=" overrides[key]; next }
        }
        { print }
    ' "$template_file" > "$new_file"
    mv "$new_file" "$target_file"
}

build_structured_templates() {
    local source target
    while IFS= read -r -d '' source; do
        target=${source%.example}
        TEMPLATE_SOURCE["$target"]=$source
    done < <(find "$WORK_DIR/envs" -type f -name '*.env.example' -print0 2>/dev/null || true)
    while IFS= read -r -d '' source; do
        target=$source
        [[ -v "TEMPLATE_SOURCE[$target]" ]] || TEMPLATE_SOURCE["$target"]=$source
    done < <(find "$WORK_DIR/envs" -type f -name '*.env' -print0 2>/dev/null || true)

    : > "$TEMP_DIR/template-index"
    for target in "${!TEMPLATE_SOURCE[@]}"; do
        source=${TEMPLATE_SOURCE[$target]}
        while IFS="$SEP" read -r key value; do
            printf '%s%s%s%s%s\n' "$target" "$SEP" "$key" "$SEP" "$value" >> "$TEMP_DIR/template-index"
        done < <(parse_env "$source")
    done
}

migrate_structured_values() {
    local key value record target template_value candidate_count source current_file
    declare -A migration_values=() legacy_values=()
    build_structured_templates
    for key in "${!ENV_VALUES[@]}"; do
        [[ -v "EXAMPLE_VALUES[$key]" ]] && continue
        value=${ENV_VALUES[$key]}
        [[ -n "$value" ]] || continue
        mapfile -t candidates < <(awk -F "$SEP" -v wanted="$key" '$2 == wanted {print $1 SUBSEP $3}' "$TEMP_DIR/template-index")
        candidate_count=${#candidates[@]}
        if (( candidate_count == 1 )); then
            target=${candidates[0]%%$'\034'*}
            template_value=${candidates[0]#*$'\034'}
            [[ "$value" == "$template_value" ]] && continue
            migration_values["$target$SEP$key"]=$value
        elif (( candidate_count > 1 )); then
            legacy_values["$key"]=$value
        fi
    done

    for target in "${!TEMPLATE_SOURCE[@]}"; do
        source=${TEMPLATE_SOURCE[$target]}
        current_file="$TEMP_DIR/structured-overrides.$RANDOM"
        : > "$current_file"
        if [[ -f "$target" && "$target" != "$source" ]]; then
            awk -F "$SEP" '
                FNR == NR { defaults[$1] = substr($0, length($1) + length(FS) + 1); next }
                $1 in defaults && substr($0, length($1) + length(FS) + 1) != defaults[$1] { print }
            ' <(parse_env "$source") <(parse_env "$target") >> "$current_file"
        fi
        local target_has_migration=false
        for record in "${!migration_values[@]}"; do
            [[ ${record%%"$SEP"*} == "$target" ]] || continue
            key=${record#*"$SEP"}
            printf '%s%s%s\n' "$key" "$SEP" "${migration_values[$record]}" >> "$current_file"
            target_has_migration=true
            ((MIGRATED_COUNT += 1))
        done
        if [[ "$target_has_migration" == true ]]; then
            rewrite_from_template "$source" "$target" "$current_file"
            log_success "Migrated structured variables to ${target#$WORK_DIR/}"
        fi
        rm -f "$current_file"
    done

    : > "$TEMP_DIR/legacy-overrides"
    for key in "${!legacy_values[@]}"; do
        printf '%s%s%s\n' "$key" "$SEP" "${legacy_values[$key]}" >> "$TEMP_DIR/legacy-overrides"
    done
    LEGACY_COUNT=${#legacy_values[@]}
}

sync_top_level_env() {
    local key value
    : > "$TEMP_DIR/root-overrides"
    for key in "${!ENV_VALUES[@]}"; do
        [[ -v "EXAMPLE_VALUES[$key]" ]] || continue
        value=${ENV_VALUES[$key]}
        [[ "$value" == "${EXAMPLE_VALUES[$key]}" ]] && continue
        printf '%s%s%s\n' "$key" "$SEP" "$value" >> "$TEMP_DIR/root-overrides"
    done
    rewrite_from_template "$EXAMPLE_FILE" "$ENV_FILE" "$TEMP_DIR/root-overrides"
    if [[ -s "$TEMP_DIR/legacy-overrides" ]]; then
        {
            printf '\n# Legacy overrides retained because multiple envs templates declare them.\n'
            printf '# Move each value to the appropriate envs/*.env file after reviewing its service.\n'
            awk -F "$SEP" '{print $1 "=" substr($0, length($1) + length(FS) + 1)}' "$TEMP_DIR/legacy-overrides"
        } >> "$ENV_FILE"
    fi
}

main() {
    log_info "=== Dify Environment Variables Synchronization Script ==="
    log_info "Working directory: $WORK_DIR"
    check_files
    backup_env
    ENV_VALUES=(); EXAMPLE_VALUES=(); TEMPLATE_SOURCE=()
    MIGRATED_COUNT=0; LEGACY_COUNT=0
    TEMP_DIR=$(mktemp -d)
    load_env_values
    load_example_values
    if [[ "$MIGRATE_ENVS" == true ]]; then
        migrate_structured_values
    else
        : > "$TEMP_DIR/legacy-overrides"
    fi
    sync_top_level_env
    log_success 'Top-level .env synchronized'
    log_info "Migrated to structured envs: $MIGRATED_COUNT"
    log_info "Legacy compatibility overrides retained: $LEGACY_COUNT"
    log_success '=== Synchronization process completed successfully ==='
}

main
