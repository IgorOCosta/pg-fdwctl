def execute(self, target, database, schemas, action):
    if target["fdw_type"] == "oracle":
        from engine.oracle_fdw import OracleFDW

        fdw = OracleFDW(self.pg, self.config, target)

        if action == "install":
            fdw.install(database, schemas)
        elif action == "update":
            fdw.update(database, schemas)
        elif action == "remove":
            fdw.remove(database, schemas)
 