class DBModel:
    def __init__(self, server_address=None, info=None, historical_server_address=None,
                 historical_info=None, pms_server_address=None, pms_db=None, pms_info=None):
        self.server_address = server_address
        self.info = info
        self.historical_server_address = historical_server_address
        self.historical_info = historical_info
        self.pms_server_address = pms_server_address
        self.pms_db = pms_db
        self.pms_info = pms_info
        

class DbConnectionString:
    def __init__(self, server_address=None, db_name=None, username=None, password=None):
        self.server_address = server_address
        self.db_name = db_name
        self.username = username
        self.password = password

    @property
    def connection_string(self):
        """Generate the connection string."""
        return f"Server={self.server_address};Initial Catalog={self.db_name};User ID={self.username};Password={self.password};"