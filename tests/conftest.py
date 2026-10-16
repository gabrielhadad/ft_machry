import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app({"TESTING": True, "DATABASE_PATH": str(tmp_path / "test.db")})


@pytest.fixture
def client(app):
    # test_cli_runner não empurra app context como o comando `flask` faz.
    with app.app_context():
        result = app.test_cli_runner().invoke(args=["init-db"])
    assert result.exit_code == 0, result.output
    return app.test_client()
