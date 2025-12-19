import re
import time


class OracleFDW:
    def __init__(self, pg, config, target):
        self.pg = pg
        self.config = config
        self.target = target
        self.defaults = config["defaults"]

        self.ip, self.port, self.service = self._parse_connection(
            target["connection"]
        )

    def _oracle_password(self, role):
        for r in self.config["roles"]:
            if r["name"] == role:
                return r.get("oracle_password")
        raise ValueError(f"Oracle password not defined for role {role}")

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def install(self, database, schemas):
        self._apply(database, schemas, mode="install")

    def update(self, database, schemas):
        self._apply(database, schemas, mode="update")

    def remove(self, database, schemas):
        self._apply(database, schemas, mode="remove")

    # ---------------------------------------------------------
    # Core logic
    # ---------------------------------------------------------

    def _apply(self, database, schemas, mode):
        roles = [r["name"] for r in self.config["roles"] if r["enabled"]]

        if self.defaults.get("grant_superuser_temporarily", False):
            self._grant_superuser(roles)

        try:
            for role in roles:
                if role not in schemas:
                    continue

                schema_name = self._schema_name(database, role)
                server_name = self._server_name(database, role)

                if mode in ("update", "remove"):
                    self._drop_schema(schema_name)
                    self._drop_server(server_name)

                if mode in ("install", "update"):
                    self._create_schema(schema_name, role)
                    self._create_server(server_name)
                    self._create_user_mappings(server_name, role)
                    self._import_schema(server_name, schema_name, role)

        finally:
            if self.defaults.get("grant_superuser_temporarily", False):
                self._revoke_superuser(roles)

    # ---------------------------------------------------------
    # PostgreSQL operations
    # ---------------------------------------------------------

    def _create_schema(self, schema, owner):
        print(f"📦 Creating schema {schema}")
        self.pg.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.schemata
                    WHERE schema_name = '{schema}'
                ) THEN
                    CREATE SCHEMA {schema} AUTHORIZATION {owner.lower()};
                END IF;
            END $$;
        """)

    def _drop_schema(self, schema):
        print(f"🧹 Dropping schema {schema}")
        self.pg.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")

    def _create_server(self, server):
        print(f"🔧 Creating FDW server {server}")

        self.pg.execute(
            "SELECT 1 FROM pg_foreign_server WHERE srvname = %s;",
            (server.lower(),)
        )

        if self.pg.fetchone():
            print(f"🔹 FDW server {server} already exists, skipping creation")
            return

        dbserver = f"//{self.ip}:{self.port}/{self.service}"

        self.pg.execute(f"""
            CREATE SERVER {server}
            FOREIGN DATA WRAPPER oracle_fdw
            OPTIONS (dbserver '{dbserver}');
        """)


    def _drop_server(self, server):
        print(f"🧹 Dropping FDW server {server}")
        self.pg.execute(f'DROP SERVER IF EXISTS "{server}" CASCADE;')

    def _create_user_mappings(self, server, role):
        password = self._oracle_password(role)

        for pg_user in ("postgres", role.lower()):
            print(f"🔐 Ensuring user mapping for {pg_user}")

            self.pg.execute(
                """
                SELECT 1
                FROM pg_user_mappings um
                JOIN pg_foreign_server fs ON fs.oid = um.srvid
                JOIN pg_roles r ON r.oid = um.umuser
                WHERE fs.srvname = %s
                AND r.rolname = %s
                """,
                (server.lower(), pg_user)
            )

            if self.pg.fetchone():
                print(f"🔹 User mapping for {pg_user} already exists, skipping")
                continue

            self.pg.execute(f"""
                CREATE USER MAPPING FOR {pg_user}
                SERVER {server}
                OPTIONS (user '{role}', password '{password}');
            """)


    def _import_schema(self, server, schema, role):
        print(f"📥 Importing Oracle schema {role} into {schema}")
        start = time.time()

        self.pg.execute(f"SET ROLE {role.lower()};")
        self.pg.execute(f"""
            IMPORT FOREIGN SCHEMA "{role}"
            FROM SERVER {server}
            INTO {schema}
            OPTIONS (case 'lower');
        """)
        self.pg.execute("RESET ROLE;")

        elapsed = time.time() - start
        print(f"✅ Import completed in {elapsed:.2f}s")
        self.pg.notice_flush()

    # ---------------------------------------------------------
    # Superuser handling
    # ---------------------------------------------------------

    def _grant_superuser(self, roles):
        for r in roles:
            print(f"🔺 Granting SUPERUSER to {r}")
            self.pg.execute(f"ALTER ROLE {r.lower()} WITH SUPERUSER;")

    def _revoke_superuser(self, roles):
        for r in roles:
            print(f"🔻 Revoking SUPERUSER from {r}")
            self.pg.execute(f"ALTER ROLE {r.lower()} WITH NOSUPERUSER;")

    # ---------------------------------------------------------
    # Naming helpers
    # ---------------------------------------------------------

    def _schema_name(self, database, role):
        return self.defaults["schema_name_pattern"].format(
            db_type="oracle",
            database=database.lower(),
            user=role.lower(),
            ip=self.ip.replace(".", "_"),
            client=self.target["client"].lower()
        )

    def _server_name(self, database, role):
        return self.defaults["server_name_pattern"].format(
            user=role,
            database=database,
            client=self.target["client"],
            ip=self.ip.replace(".", "_")
        )

    # ---------------------------------------------------------
    # Connection parsing
    # ---------------------------------------------------------

    def _parse_connection(self, conn):
        if "jdbc" in conn:
            return self._parse_jdbc(conn["jdbc"])

        return conn["ip"], conn["port"], conn["service_name"]

    def _parse_jdbc(self, jdbc):
        match = re.search(r'@tcp://([\d\.]+):(\d+)/(.*)', jdbc)
        if not match:
            raise ValueError(f"Invalid JDBC string: {jdbc}")

        ip, port, service = match.group(1), match.group(2), match.group(3)
        print(f"🔍 JDBC parsed: {ip}:{port}/{service}")
        return ip, port, service
