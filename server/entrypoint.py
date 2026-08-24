import os

from waitress import serve

from server.app import create_app


def server_host():
    return os.environ.get("HOST", "127.0.0.1")


def main():
    app = create_app({"ENV": "production"})
    serve(app, host=server_host(), port=int(os.environ.get("PORT", "5001")), threads=6)


if __name__ == "__main__":
    main()
