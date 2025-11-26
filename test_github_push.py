import os
import subprocess
import pytest
from pathlib import Path
import github_push as gp


@pytest.fixture
def temp_git_repo(tmp_path):
    """Crée un dépôt Git temporaire pour les tests."""
    cwd = tmp_path
    subprocess.run(["git", "init"], cwd=cwd, check=True)
    (cwd / "README.md").write_text("# Test Repo\n")
    subprocess.run(["git", "add", "README.md"], cwd=cwd, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=cwd, check=True)
    return cwd


def test_ensure_git_repo(temp_git_repo, tmp_path):
    # Le repo temporaire est bien reconnu
    assert gp.ensure_git_repo(temp_git_repo) is True

    # Crée un dossier complètement séparé (hors du repo)
    non_repo = tmp_path.parent / "outside_non_repo"
    non_repo.mkdir(exist_ok=True)
    assert gp.ensure_git_repo(non_repo) is False


def test_has_changes(temp_git_repo):
    assert gp.has_changes(temp_git_repo) is False
    (temp_git_repo / "file.txt").write_text("hello")
    subprocess.run(["git", "add", "file.txt"], cwd=temp_git_repo, check=True)
    assert gp.has_changes(temp_git_repo) is True


def test_push_project_no_repo(tmp_path, monkeypatch):
    monkeypatch.setattr(gp, "GIT_CWD", tmp_path)
    result = gp.push_project("Test commit", branch="testbranch", dry_run=True)
    assert result is False


def test_push_project_with_repo(temp_git_repo, monkeypatch):
    monkeypatch.setattr(gp, "GIT_CWD", temp_git_repo)
    (temp_git_repo / "newfile.txt").write_text("data")
    subprocess.run(["git", "add", "newfile.txt"], cwd=temp_git_repo, check=True)
    result = gp.push_project("Commit test", branch="testbranch", dry_run=True)
    assert result is True


def test_push_agent_output_missing_dir(temp_git_repo, monkeypatch):
    monkeypatch.setattr(gp, "GIT_CWD", temp_git_repo)
    result = gp.push_agent_output("fake_agent", branch="testbranch", dry_run=True)
    assert result is False


def test_push_agent_output_with_dir(temp_git_repo, monkeypatch):
    monkeypatch.setattr(gp, "GIT_CWD", temp_git_repo)
    agent_dir = temp_git_repo / "agents_output" / "fake_agent"
    agent_dir.mkdir(parents=True)
    (agent_dir / "README.md").write_text("agent readme")
    subprocess.run(["git", "add", str(agent_dir / "README.md")], cwd=temp_git_repo, check=True)
    result = gp.push_agent_output("fake_agent", branch="testbranch", dry_run=True)
    assert result is True