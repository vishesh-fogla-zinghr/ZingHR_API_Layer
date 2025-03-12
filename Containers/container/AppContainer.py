# zinghr_backend/app/Containers/container.py
from dependency_injector import containers, providers
from DAL.dbconnection import DBConnection
from Common.AES.EncryptDecryptValue import EncryptDecryptValue
from DAL.dal import DAL
from Common.Redis.redis_service import RedisService
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.LoginCommand import LoginCommand
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.SendOTPCommand import SendOTPCommand
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Handlers.SendOTPHandler import SendOTPHandler
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Handlers.LoginHandler import LoginHandler
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.VerifyOTPCommand import VerifyOTPCommand
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Handlers.VerifyOTPHandler import VerifyOTPHandler



from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Commands.RefreshTokenCommand import RefreshTokenCommand
from MicroServices.ZingAuth.Application.AppLogics.AuthToken.Handlers.RefreshTokenCommandHandler import RefreshTokenHandler
from Containers.mediator import mediator

class AppContainer(containers.DeclarativeContainer):
    db_connection = providers.Singleton(DBConnection)
    encryptor = providers.Singleton(EncryptDecryptValue)
    dal = providers.Singleton(DAL, connection=db_connection)
    redis_service = providers.Singleton(RedisService)
    login_handler = providers.Factory(LoginHandler, _connection=dal, encryptor=encryptor, redis_service=redis_service)
    send_otp_handler = providers.Factory(SendOTPHandler, _connection=dal)
    verify_otp_handler = providers.Factory(VerifyOTPHandler, _connection=dal)
    refresh_token_handler = providers.Factory(RefreshTokenHandler, _connection=dal)
    

container = AppContainer()
mediator.register_handler(LoginCommand, container.login_handler)
mediator.register_handler(RefreshTokenCommand, container.refresh_token_handler)
mediator.register_handler(SendOTPCommand, container.send_otp_handler)
mediator.register_handler(VerifyOTPCommand, container.verify_otp_handler)