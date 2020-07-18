from functools import wraps
from flask_jwt import _jwt, JWTError
import jwt
import app.models.User as User


def authorize(realm=None, user_type='user'):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            token = _jwt.request_callback()

            if token is None:
                raise JWTError('Authorization Required', 'Request does not contain an access token',
                               headers={'WWW-Authenticate': 'JWT realm="%s"' % realm})

            try:
                payload = _jwt.jwt_decode_callback(token)
            except jwt.InvalidTokenError as e:
                raise JWTError('Invalid token', str(e))

            identity = _jwt.identity_callback(payload)
            if user_type == 'student' and isinstance(identity, Student):
                return fn(*args, **kwargs)
            elif user_type == 'teacher' and isinstance(identity, Teacher):
                return fn(*args, **kwargs)
            # NOTE - By default JWTError throws 401. We needed 404. Hence status_code=404
            raise JWTError('Unauthorized',
                           'You are unauthorized to request the api or access the resource',
                           status_code=404)
        return decorator
    return wrapper
