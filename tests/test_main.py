"""CLIエントリーポイントのテスト"""

from click.testing import CliRunner

from src.main import main


def test_runs_with_default_config_path() -> None:
    """デフォルトの設定ファイルパスで実行されること

    Arrange
    - CliRunnerを準備
    Act
    - オプションなしでmainを実行
    Assert
    - 終了コードが0であること
    """
    # Arrange
    runner = CliRunner()

    # Act
    result = runner.invoke(main)

    # Assert
    assert result.exit_code == 0


def test_custom_config_path_loaded() -> None:
    """カスタム設定ファイルパスが指定された場合に読み込まれること

    Arrange
    - CliRunnerとオプション引数を準備
    Act
    - -cオプションで設定ファイルを指定してmainを実行
    Assert
    - 終了コードが0であること
    """
    # Arrange
    runner = CliRunner()

    # Act
    result = runner.invoke(main, ["-c", "./config/config.json"])

    # Assert
    assert result.exit_code == 0


def test_nonexistent_config_file_raises_error() -> None:
    """存在しない設定ファイルを指定した場合にエラーになること

    Arrange
    - CliRunnerと存在しないファイルパスを準備
    Act
    - 存在しないファイルを指定してmainを実行
    Assert
    - 終了コードが0以外であること
    """
    # Arrange
    runner = CliRunner()

    # Act
    result = runner.invoke(main, ["-c", "./config/not_exist.json"])

    # Assert
    assert result.exit_code != 0
