from subprocess import CalledProcessError
from unittest import mock

import pytest

from bb.core.git import (
    GitCommand,
    amend_commit,
    clean,
    commit,
    create_branch,
    create_tag,
    delete_branch,
    delete_tag,
    diff,
    get_config,
    get_current_branch,
    get_current_repo_slug,
    is_git_repo,
    list_tags,
    push,
    rename_branch,
    set_config,
    stash_list,
    stash_pop,
    stash_save,
    status,
)
from bb.exceptions import GitPushRejectedException, IPWhitelistException
from bb.typeshed import Err, Ok


class TestGitCommand:
    @mock.patch("bb.core.git.check_output")
    def test_run_success(self, mock_check_output):
        mock_check_output.return_value = "command output"
        cmd = GitCommand("status")
        result = cmd.run()
        assert isinstance(result, Ok)
        assert result.unwrap() == "command output"

    @mock.patch("bb.core.git.check_output")
    def test_run_failure(self, mock_check_output):
        mock_check_output.side_effect = CalledProcessError(
            1, "git status", output="error output"
        )
        cmd = GitCommand("status")
        result = cmd.run()
        assert isinstance(result, Err)

    @mock.patch("bb.core.git.is_git_repo")
    def test_not_git_repo(self, mock_is_git_repo):
        mock_is_git_repo.return_value = False
        cmd = GitCommand("status")
        result = cmd.run()
        assert isinstance(result, Err)
        with pytest.raises(RuntimeError):
            result.unwrap()


class TestGitOperations:
    @mock.patch("bb.core.git.check_output")
    def test_get_current_repo_slug(self, mock_check_output):
        mock_check_output.return_value = (
            "origin\tgit@bitbucket.org:org/repo.git (fetch)\n"
        )
        result = get_current_repo_slug()
        assert isinstance(result, Ok)
        assert result.unwrap() == "org/repo"

    @mock.patch("bb.core.git.check_output")
    def test_get_current_branch(self, mock_check_output):
        mock_check_output.return_value = "main"
        result = get_current_branch()
        assert isinstance(result, Ok)
        assert result.unwrap() == "main"

    @mock.patch("bb.core.git.GitCommand.run")
    def test_create_branch(self, mock_run):
        mock_run.return_value = Ok("Created branch 'feature'\n")
        result = create_branch("feature")
        assert isinstance(result, Ok)
        mock_run.assert_called_once()

    @mock.patch("bb.core.git.GitCommand.run")
    def test_delete_branch(self, mock_run):
        mock_run.return_value = Ok("Deleted branch 'feature'\n")
        result = delete_branch("feature")
        assert isinstance(result, Ok)
        mock_run.assert_called_once()

    @mock.patch("bb.core.git.GitCommand.run")
    def test_rename_branch(self, mock_run):
        mock_run.return_value = Ok("Renamed branch 'old' to 'new'\n")
        result = rename_branch("old", "new")
        assert isinstance(result, Ok)
        mock_run.assert_called_once()

    @mock.patch("bb.core.git.GitCommand.run")
    def test_commit(self, mock_run):
        mock_run.return_value = Ok("Changes committed\n")
        result = commit("test commit")
        assert isinstance(result, Ok)
        mock_run.assert_called_once()

    @mock.patch("bb.core.git.GitCommand.run")
    def test_amend_commit(self, mock_run):
        mock_run.return_value = Ok("Commit amended\n")
        result = amend_commit("amended message")
        assert isinstance(result, Ok)
        mock_run.assert_called_once()

    @mock.patch("bb.core.git.GitCommand.run")
    def test_status(self, mock_run):
        mock_run.return_value = Ok("On branch main\n")
        result = status()
        assert isinstance(result, Ok)
        mock_run.assert_called_once()

    @mock.patch("bb.core.git.GitCommand.run")
    def test_diff(self, mock_run):
        mock_run.return_value = Ok("diff output\n")
        result = diff()
        assert isinstance(result, Ok)
        mock_run.assert_called_once()

    @mock.patch("bb.core.git.GitCommand.run")
    def test_push_success(self, mock_run):
        mock_run.return_value = Ok("Push successful\n")

        result = push("origin", "main")
        assert result.unwrap() == "Push successful\n"
        mock_run.assert_called_once()

    @mock.patch("bb.core.git.GitCommand.run")
    def test_push_rejected(self, mock_run):
        error = CalledProcessError(1, "git push", output="[rejected] main -> main")
        mock_run.return_value = Err(error)
        result = push("origin", "main")
        with pytest.raises(GitPushRejectedException):
            result.unwrap()

    @mock.patch("bb.core.git.GitCommand.run")
    def test_push_ip_whitelist(self, mock_run):
        error = CalledProcessError(1, "git push", output="whitelist your IP")
        mock_run.return_value = Err(error)
        result = push("origin", "main")
        with pytest.raises(IPWhitelistException):
            result.unwrap()

    @mock.patch("bb.core.git.GitCommand.run")
    def test_stash_operations(self, mock_run):
        mock_run.return_value = Ok("Stash operation successful\n")

        result = stash_save("test stash")
        assert isinstance(result, Ok)

        result = stash_pop()
        assert isinstance(result, Ok)

        result = stash_list()
        assert isinstance(result, Ok)

    @mock.patch("bb.core.git.GitCommand.run")
    def test_config_operations(self, mock_run):
        mock_run.return_value = Ok("Config operation successful\n")

        result = get_config("user.name")
        assert isinstance(result, Ok)

        result = set_config("user.name", "Test User")
        assert isinstance(result, Ok)

    @mock.patch("bb.core.git.GitCommand.run")
    def test_tag_operations(self, mock_run):
        mock_run.return_value = Ok("Tag operation successful\n")

        result = create_tag("v1.0.0", "Version 1.0.0")
        assert isinstance(result, Ok)

        result = delete_tag("v1.0.0")
        assert isinstance(result, Ok)

        result = list_tags()
        assert isinstance(result, Ok)

    @mock.patch("bb.core.git.GitCommand.run")
    def test_clean(self, mock_run):
        mock_run.return_value = Ok("Clean successful\n")
        result = clean(force=True)
        assert isinstance(result, Ok)
        mock_run.assert_called_once()

    @mock.patch("bb.core.git.check_output")
    def test_is_git_repo(self, mock_check_output):
        mock_check_output.return_value = ""
        assert is_git_repo() is True

        mock_check_output.side_effect = CalledProcessError(128, "git rev-parse")
        assert is_git_repo() is False
