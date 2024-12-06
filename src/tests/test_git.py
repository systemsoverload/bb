import os
from subprocess import CalledProcessError
from unittest.mock import patch, MagicMock

import pytest

from bb.git import (
    BB_CLIENT_ID,
    _prepare_git_env,
    _run_git_command,
    get_current_repo_slug,
    get_current_branch,
    get_current_diff_to_main,
    push_branch,
    get_branch,
    get_default_branch,
    edit_tmp_file,
)
from bb.exceptions import GitPushRejectedException, IPWhitelistException


@pytest.fixture
def mock_env():
    with patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=True):
        yield


def test_prepare_git_env(mock_env):
    """Test environment preparation for git commands"""
    env = _prepare_git_env()

    assert env['GIT_SSH_COMMAND'] == 'ssh -o SendEnv=BB_CLIENT_ID'
    assert env['BB_CLIENT_ID'] == BB_CLIENT_ID
    assert 'PATH' in env  # Should preserve existing env vars


@patch('bb.git.check_output')
def test_prepare_git_env_config_failure(mock_check_output, mock_env):
    """Test environment preparation handles git config failures gracefully"""
    mock_check_output.side_effect = CalledProcessError(1, 'cmd')

    env = _prepare_git_env()

    assert env['GIT_SSH_COMMAND'] == 'ssh -o SendEnv=BB_CLIENT_ID'
    assert env['BB_CLIENT_ID'] == BB_CLIENT_ID


@patch('bb.git.check_output')
def test_run_git_command_success(mock_check_output):
    """Test successful git command execution"""
    # Configure mock to return different values for different calls
    mock_check_output.side_effect = [
        None,  # First call (git config)
        "command output"  # Second call (actual command)
    ]

    result = _run_git_command("git status")

    assert result.unwrap() == "command output"
    assert mock_check_output.call_count == 2
    # Verify the actual command call
    actual_command_call = mock_check_output.call_args_list[1]
    assert actual_command_call.args[0] == ['git', 'status']


@patch('bb.git.check_output')
def test_run_git_command_failure(mock_check_output):
    """Test failed git command execution"""
    mock_check_output.side_effect = CalledProcessError(1, 'cmd')

    result = _run_git_command("git status")

    with pytest.raises(CalledProcessError):
        result.unwrap()


@patch('bb.git._run_git_command')
def test_get_current_repo_slug_success(mock_run):
    """Test extracting repository slug from remote URL"""
    mock_run.return_value.unwrap.return_value = (
        "origin\tgit@bitbucket.org:workspace/repo.git (fetch)\n"
        "origin\tgit@bitbucket.org:workspace/repo.git (push)"
    )

    result = get_current_repo_slug()

    assert result.unwrap() == "workspace/repo"


@patch('bb.git._run_git_command')
def test_get_current_repo_slug_no_bitbucket(mock_run):
    """Test handling of non-BitBucket repository"""
    mock_run.return_value.unwrap.return_value = (
        "origin\tgit@github.com:user/repo.git (fetch)\n"
        "origin\tgit@github.com:user/repo.git (push)"
    )

    result = get_current_repo_slug()

    with pytest.raises(RuntimeError, match="No repository detected"):
        result.unwrap()


@patch('bb.git._run_git_command')
def test_get_current_branch(mock_run):
    """Test getting current branch name"""
    mock_run.return_value.unwrap.return_value = "main\n"

    result = get_current_branch()

    assert result.unwrap() == "main\n"


@patch('bb.git.get_default_branch')
@patch('bb.git.get_current_branch')
@patch('bb.git._run_git_command')
def test_get_current_diff_to_main(mock_run, mock_current, mock_default):
    """Test getting diff between current and main branch"""
    mock_default.return_value.unwrap.return_value = "main"
    mock_current.return_value.unwrap.return_value = "feature"
    mock_run.return_value.unwrap.return_value = "diff content"

    result = get_current_diff_to_main()

    assert result.unwrap() == "diff content"
    mock_run.assert_called_with("git --no-pager diff main...feature", universal_newlines=False)


@patch('bb.git._run_git_command')
def test_push_branch_success(mock_run):
    """Test successful branch push"""
    mock_run.return_value.unwrap.return_value = "Branch pushed successfully"

    result = push_branch("feature")

    assert result.unwrap() == "Branch pushed successfully"


@patch('bb.git._run_git_command')
def test_push_branch_rejected(mock_run):
    """Test handling of rejected push"""
    error = CalledProcessError(1, 'cmd')
    error.output = "error: failed to push some refs [rejected]"
    mock_run.return_value.unwrap.side_effect = error

    result = push_branch("feature")

    with pytest.raises(GitPushRejectedException):
        result.unwrap()


@patch('bb.git._run_git_command')
def test_push_branch_whitelist(mock_run):
    """Test handling of IP whitelist error"""
    error = CalledProcessError(1, 'cmd')
    error.output = "whitelist your IP"
    mock_run.return_value.unwrap.side_effect = error

    result = push_branch("feature")

    with pytest.raises(IPWhitelistException):
        result.unwrap()


@patch('bb.git._run_git_command')
def test_get_branch(mock_run):
    """Test getting specific branch reference"""
    mock_run.return_value.unwrap.return_value = "feature"

    result = get_branch("feature")

    assert result.unwrap() == "feature"


@patch('bb.git._run_git_command')
def test_get_default_branch(mock_run):
    """Test getting default branch name"""
    mock_run.return_value.unwrap.return_value = "origin/main"

    result = get_default_branch()

    assert result.unwrap() == "origin/main"


class TestEditTmpFile:
    @pytest.fixture
    def mock_tempfile(self):
        with patch('tempfile.NamedTemporaryFile') as mock:
            tmpfile = MagicMock()
            tmpfile.name = '/tmp/test'
            mock.return_value.__enter__.return_value = tmpfile
            yield mock

    @pytest.fixture
    def mock_open(self):
        with patch('builtins.open', create=True) as mock:
            file_mock = MagicMock()
            file_mock.__enter__.return_value.read.return_value = "title\n------\ndescription"
            mock.return_value = file_mock
            yield mock

    @patch('bb.git._run_git_command')
    def test_edit_tmp_file_success(self, mock_run, mock_tempfile, mock_open):
        """Test successful temporary file editing"""
        mock_run.return_value.unwrap.return_value = "vim"

        result = edit_tmp_file("initial content")
        title, description = result.unwrap()

        assert title == "title\n"
        assert description == "\ndescription"

    @patch('bb.git._run_git_command')
    def test_edit_tmp_file_empty(self, mock_run, mock_tempfile, mock_open):
        """Test handling of empty file after editing"""
        mock_run.return_value.unwrap.return_value = "vim"
        mock_open.return_value.__enter__.return_value.read.return_value = ""

        result = edit_tmp_file()

        with pytest.raises(ValueError, match="Aborting due to empty description"):
            result.unwrap()
