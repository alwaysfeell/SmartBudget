import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'smartbudget-dev-key-change-in-prod')
DATABASE   = os.environ.get('DATABASE',   'smartbudget.db')
DEBUG      = os.environ.get('DEBUG', 'true').lower() == 'true'
