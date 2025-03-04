# zinghr_backend/app/Containers/container.py
from dependency_injector import containers, providers
from DAL.dbconnection import DBConnection
from Common.AES.EncryptDecryptValue import EncryptDecryptValue
from DAL.dal import DAL
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.LoginCommand import LoginCommand
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Handlers.LoginHandler import LoginHandler

class CustomMediator:
    def __init__(self, container):
        self.container = container
        self.handlers = {LoginCommand: LoginHandler}

    async def send(self, command):
        handler_class = self.handlers.get(type(command))
        if not handler_class:
            raise ValueError(f"No handler for command {type(command)}")
        handler = self.container.login_handler()
        return await handler.handle(command)

class AppContainer(containers.DeclarativeContainer):
    db_connection = providers.Singleton(DBConnection)
    encryptor = providers.Singleton(EncryptDecryptValue)
    dal = providers.Singleton(DAL, connection=db_connection)
    login_handler = providers.Factory(LoginHandler, _connection=dal, encryptor=encryptor)
    mediator = providers.Singleton(CustomMediator, container=providers.Self())

container = AppContainer()
mediator = CustomMediator(AppContainer)