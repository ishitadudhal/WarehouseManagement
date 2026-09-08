from app import create_app
import app.models  # make sure all models are imported before db.create_all()

flask_app = create_app()

if __name__ == '__main__':
    flask_app.run(debug=True, port=5000)
