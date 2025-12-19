# fdwctl

`fdwctl` is an interactive, JSON-driven CLI tool to manage **Foreign Data Wrappers (FDW)** in PostgreSQL.

The current implementation focuses on **Oracle FDW**, with a clean and extensible architecture prepared for **future MSSQL FDW support**.

This tool is designed for **production environments**: explicit configuration, deterministic behavior, and human-safe execution.

---

## What fdwctl does

- Installs Oracle FDW schemas into PostgreSQL
- Updates (recreates) existing Oracle FDW schemas
- Removes Oracle FDW schemas and foreign servers
- Guides the user through an interactive CLI
- Uses JSON as the single source of truth

---

## What fdwctl does NOT do

- It does not auto-discover Oracle databases
- It does not guess schema names
- It does not execute batch or mass operations
- It does not silently change infrastructure

Every action is explicitly selected by the user.

---

## Requirements

### General
- Python **3.9+**
- PostgreSQL **17**
- PostgreSQL superuser credentials
- Network connectivity between PostgreSQL and Oracle

---

## PostgreSQL Requirements for Oracle FDW

For `fdwctl` to work with Oracle, the PostgreSQL instance **must be prepared correctly**.

### 1. Oracle Instant Client (MANDATORY)

PostgreSQL **must have access to the Oracle Instant Client libraries at runtime**.
This is a hard requirement of `oracle_fdw`.

The Instant Client must be installed inside the PostgreSQL environment
(host, VM, or container) and visible to the PostgreSQL server process.

#### Required libraries

- `libclntsh.so`
- `libnnz*.so`
- `libocci*.so`

If PostgreSQL cannot load `libclntsh.so`, **oracle_fdw will not work**.

---

### 2. Environment Variables (MANDATORY)

The following environment variables **must be set for the PostgreSQL server process**:

```bash
ORACLE_HOME=/opt/oracle/instantclient_23_7
LD_LIBRARY_PATH=$ORACLE_HOME:${LD_LIBRARY_PATH}
PATH=$ORACLE_HOME:${PATH}
```

These variables must be visible **at PostgreSQL startup time**, not only in the shell.

---

### 3. System Dependencies (Build Time)

To compile and install `oracle_fdw`, the following packages are required:

- `build-essential`
- `libaio1`
- `git`
- `postgresql-server-dev-17`
- `ca-certificates`

These dependencies are required only for building `oracle_fdw`.
Oracle Instant Client libraries are required at runtime.

---

### 4. oracle_fdw Extension (MANDATORY)

The `oracle_fdw` extension must be compiled and installed manually.

Official repository:
https://github.com/laurenz/oracle_fdw

Recommended and tested versions:

- PostgreSQL: **17**
- Oracle Instant Client: **23.x**
- oracle_fdw tag: **ORACLE_FDW_2_7_0**

Typical build process:

```bash
git clone --depth 1 --branch ORACLE_FDW_2_7_0 https://github.com/laurenz/oracle_fdw.git
cd oracle_fdw
make
make install
```

After installation, enable the extension:

```sql
CREATE EXTENSION oracle_fdw;
```

---

### 5. PostgreSQL Configuration Notes

- `oracle_fdw` is loaded dynamically  
  (no `shared_preload_libraries` required)
- PostgreSQL must be restarted if:
  - Oracle Instant Client libraries change
  - Environment variables change
  - `oracle_fdw` is newly installed

---

### 6. Verification

Verify the extension:

```sql
SELECT * FROM pg_extension WHERE extname = 'oracle_fdw';
```

Verify library linkage:

```bash
ldd $(pg_config --pkglibdir)/oracle_fdw.so
```

All Oracle libraries must be resolved.

---

## Oracle Requirements

Each Oracle target must meet the following requirements.

### Oracle Database
- Oracle **12c or newer** (19c recommended)
- Listener reachable from PostgreSQL
- Service name (PDB) accessible

---

### Oracle Users (Schemas)

Each schema imported via FDW must:

- Exist in Oracle
- Have the correct password
- Have permission to connect and read its own objects

Minimum required privilege:

```sql
GRANT CREATE SESSION TO STR_DBMON;
```

`SYS` and `SYSTEM` users are not supported.

Each schema can (and usually does) have its own password.
Passwords are defined per role in the configuration file.

---

## Installation

```bash
pip install -r requirements.txt
```

Copy the example configuration file:

```bash
cp examples/fdwctl.config.example.json config/fdwctl.config.json
```

Edit the file and set:
- PostgreSQL connection details
- Oracle connection details
- Oracle schema passwords

---

## Configuration Overview

### Structure

```json
{
  "postgres": { ... },
  "defaults": { ... },
  "roles": [ ... ],
  "targets": [ ... ]
}
```

---

### Roles (Oracle Schemas)

Each role represents one Oracle schema.

```json
{
  "name": "STR_DBMON",
  "enabled": true,
  "oracle_password": "SecretPassword"
}
```

- `enabled = false` → schema is ignored by the CLI
- `oracle_password` is mandatory

---

### Targets (Oracle Servers)

Each target represents one Oracle environment.

```json
{
  "id": "acme-oracle-prod",
  "client": "ACME",
  "fdw_type": "oracle",
  "connection": {
    "jdbc": "jdbc:oracle:thin:@tcp://10.10.10.5:1521/ORCLPDB1"
  },
  "databases": [
    {
      "name": "ORCL",
      "schemas": ["STR_DBMON", "STR_DBDASH"]
    }
  ]
}
```

---

## Usage (Interactive CLI)

```bash
python main.py
```

### CLI Flow

1. Select target
2. Select database
3. Select schemas
4. Choose action:
   - Install
   - Update (recreate)
   - Remove

All selections are validated before any database operation.

---

## MSSQL FDW (Roadmap)

Support for MSSQL FDW is planned.

Planned scope:
- SQL Server FDW support
- ODBC / FreeTDS based connections
- Per-schema mapping
- Same interactive CLI
- Same JSON-driven configuration

Status: planned.

---

## Safety Model

- No batch execution
- No implicit actions
- No environment assumptions
- Explicit user confirmation for every operation

If a validation fails, execution stops immediately.

---

## Project Philosophy

- Explicit over implicit
- Configuration over convention
- Safe-by-design CLI
- Infrastructure treated as infrastructure

FDW is powerful and dangerous if misused.
This tool exists to make it predictable and safe.
