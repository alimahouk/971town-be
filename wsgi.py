from app import app


if __name__ == "__main__":
    app.run(app,
            port=8000,
            threaded=True)
