import os

from waitress import serve

from server.app import create_app


def main():
    app = create_app({"ENV": "production"})
    serve(app, host="127.0.0.1", port=int(os.environ.get("PORT", "5001")), threads=6)


if __name__ == "__main__":
    main()
