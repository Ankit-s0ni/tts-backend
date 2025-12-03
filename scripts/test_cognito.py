from dotenv import load_dotenv
import os, traceback

base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
env_path = os.path.join(base, '.env')
print('Loading .env from', env_path)
load_dotenv(env_path)
print('COGNITO_USER_POOL_ID=', os.getenv('COGNITO_USER_POOL_ID'))
print('COGNITO_APP_CLIENT_ID=', os.getenv('COGNITO_APP_CLIENT_ID'))
print('AWS_REGION=', os.getenv('AWS_REGION'))

try:
    import app.auth as auth
    print('Imported app.auth OK')
    token = os.getenv('TEST_COGNITO_TOKEN')
    print('TEST_COGNITO_TOKEN present:', bool(token))
    if token:
        try:
            u = auth.get_current_user(token=token)
            print('get_current_user returned id/email:', getattr(u, 'id', None), getattr(u, 'email', None))
        except Exception:
            print('get_current_user raised:')
            traceback.print_exc()
except Exception:
    print('Importing app.auth failed:')
    traceback.print_exc()
