import config.settings as s
import os

print('DATABASE_URL=', s.DATABASE_URL)
print('ENV=', dict(os.environ))
