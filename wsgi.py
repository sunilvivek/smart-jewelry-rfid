import os
from app import create_app, init_db

config_name = os.environ.get("FLASK_CONFIG", "production")
app = create_app(config_name)
init_db(app)

if __name__ == "__main__":
    app.run()
