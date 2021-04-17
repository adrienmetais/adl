from . import db

data = db.DBData()

if not data.check_or_create_dir():
  logging.error("Error accessing data directory !")
  sys.exit(1)

data.load()
