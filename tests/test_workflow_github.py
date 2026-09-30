"""Exercise delivery with real disposable git repositories and mocked GitHub."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/workflow_github.py"
SPEC = importlib.util.spec_from_file_location("delivery", SCRIPT)
delivery = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(delivery)


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.old_cwd = Path.cwd()
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, self.old_cwd)
        self.real_run = delivery.run
        self.real_run("git", "init", "-q", "-b", "main")
        self.real_run("git", "config", "user.name", "Workflow test")
        self.real_run("git", "config", "user.email", "test@example.com")
        self.real_run("git", "config", "commit.gpgsign", "false")
        Path(".gitignore").write_text(".specify/feature.json\n")
        Path("src").mkdir()
        Path("src/app.cs").write_text("baseline\n")
        self.real_run("git", "add", ".")
        self.real_run("git", "commit", "-qm", "baseline")
        self.base = self.real_run("git", "rev-parse", "HEAD")
        self.real_run("git", "update-ref", "refs/remotes/origin/main", self.base)
        self.real_run("git", "remote", "add", "origin", f"https://github.com/{delivery.REPO}.git")
        Path(".specify/memory").mkdir(parents=True)
        Path(".specify/memory/constitution.md").write_text("# Agreed constitution\n")
        self.events = []
        self.remote_issues = []
        self.remote_prs = []
        self.login = delivery.ACCOUNT
        self.fail_tests = False
        self.fail_issue = None
        self.fail_push = False
        self.patcher = patch.object(delivery, "run", side_effect=self.fake_run)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.stdout = contextlib.redirect_stdout(io.StringIO())
        self.stdout.__enter__()
        self.addCleanup(self.stdout.__exit__, None, None, None)

    def fake_run(self, *args, input_text=None):
        self.events.append(args)
        if args[:2] == ("git", "fetch"):
            return ""
        if args[:2] == ("git", "push"):
            if self.fail_push:
                raise RuntimeError("push failed")
            return ""
        if args[0] == "dotnet":
            if self.fail_tests:
                raise RuntimeError("test failure")
            return "Passed"
        if args[0] != "gh":
            return self.real_run(*args, input_text=input_text)
        if args[1:3] == ("auth", "switch"):
            return ""
        if args[1:3] == ("api", "user"):
            return self.login
        if args[1] == "api":
            path = next(arg for arg in args if arg.startswith("repos/"))
            if "issues?state=all" in path:
                return json.dumps([self.remote_issues])
            if "labels?" in path:
                return json.dumps([[{"name": "demo"}]])
            if path.endswith("/issues") and input_text:
                data = json.loads(input_text)
                if self.fail_issue and data["title"].startswith(self.fail_issue):
                    raise RuntimeError("issue API failed")
                number = len(self.remote_issues) + 1
                data.update(number=number, html_url=f"https://github.com/{delivery.REPO}/issues/{number}")
                self.remote_issues.append(data)
                return json.dumps(data)
        if args[1:3] == ("pr", "list"):
            return json.dumps(self.remote_prs)
        if args[1:3] == ("pr", "create"):
            pr = {"number": 42, "url": f"https://github.com/{delivery.REPO}/pull/42", "state": "OPEN"}
            self.remote_prs.append(pr)
            return pr["url"]
        if args[1:3] == ("pr", "edit"):
            return ""
        raise AssertionError(f"Unexpected GitHub operation: {args}")

    def feature(self, name="001-health", checked=False):
        self.directory = Path("specs") / name
        self.directory.mkdir(parents=True)
        Path(".specify/feature.json").write_text(json.dumps({"feature_directory": str(self.directory)}))
        self.tasks(checked)

    def tasks(self, checked):
        check = "x" if checked else " "
        (self.directory / "tasks.md").write_text(
            f"- [{check}] T001 [P] Add regression test\n- [{check}] T1000 Implement health field\n")

    def ready(self):
        delivery.prepare()
        self.feature()
        delivery.issues(create=True)
        self.tasks(True)
        Path("src/app.cs").write_text("implementation\n")

    def test_branch_created_and_reused_without_touching_main(self):
        delivery.prepare()
        branch = delivery.state()["branch"]
        self.assertTrue(branch.startswith("demo/delivery-"))
        delivery.prepare()
        self.assertEqual(branch, delivery.state()["branch"])
        self.assertEqual(self.base, self.real_run("git", "rev-parse", "main"))

    def test_unrelated_dirty_file_rejected(self):
        Path("private.txt").write_text("unrelated")
        with self.assertRaisesRegex(RuntimeError, "unrelated changes"):
            delivery.prepare()
        self.assertEqual("main", self.real_run("git", "branch", "--show-current"))

    def test_old_checkpoint_rejected(self):
        self.real_run("git", "commit", "--allow-empty", "-qm", "different baseline")
        with self.assertRaisesRegex(RuntimeError, "origin/main"):
            delivery.prepare()

    def test_wrong_account_and_push_remote_rejected(self):
        self.login = "another-account"
        with self.assertRaisesRegex(RuntimeError, "account must"):
            delivery.prepare()
        self.login = delivery.ACCOUNT
        self.real_run("git", "remote", "set-url", "--push", "origin", "https://github.com/other/repo.git")
        with self.assertRaisesRegex(RuntimeError, "origin must"):
            delivery.prepare()
        self.assertFalse(self.remote_issues)

    def test_partial_issue_failure_retries_without_duplicates(self):
        delivery.prepare()
        self.feature()
        self.fail_issue = "T1000"
        with self.assertRaisesRegex(RuntimeError, "API failed"):
            delivery.issues(create=True)
        self.assertEqual(len(self.remote_issues), 1)
        self.fail_issue = None
        delivery.issues(create=True)
        delivery.issues(create=True)
        self.assertEqual(len(self.remote_issues), 2)
        self.assertTrue(all(i["labels"] == ["demo"] for i in self.remote_issues))
        self.assertEqual(set(delivery.issues(create=False)), {"T001", "T1000"})

    def test_generic_task_titles_do_not_collide(self):
        self.remote_issues.append({"title": "T001: Old task", "body": "Other feature", "number": 50})
        delivery.prepare()
        self.feature()
        delivery.issues(create=True)
        self.assertEqual(len(self.remote_issues), 3)

    def test_missing_issues_stop_before_implementation_verification(self):
        delivery.prepare()
        self.feature()
        with self.assertRaisesRegex(RuntimeError, "Missing GitHub issues"):
            delivery.issues(create=False)

    def test_changed_feature_and_branch_rejected(self):
        self.ready()
        self.feature("002-other")
        with self.assertRaisesRegex(RuntimeError, "feature changed"):
            delivery.review()
        self.real_run("git", "switch", "-c", "unexpected")
        with self.assertRaisesRegex(RuntimeError, "branch changed"):
            delivery.review()

    def test_open_tasks_block_publication(self):
        self.ready()
        self.tasks(False)
        with self.assertRaisesRegex(RuntimeError, "Unchecked tasks"):
            delivery.publish()
        self.assertFalse(self.remote_prs)

    def test_tests_and_content_scan_block_push(self):
        self.ready()
        self.fail_tests = True
        with self.assertRaisesRegex(RuntimeError, "test failure"):
            delivery.publish()
        self.fail_tests = False
        Path("src/app.cs").write_text("aus" + "tin\n")
        with self.assertRaisesRegex(RuntimeError, "content scan"):
            delivery.publish()
        self.assertFalse(any(e[:2] == ("git", "push") for e in self.events))

    def test_unexpected_committed_files_block_publication(self):
        self.ready()
        Path("scripts").mkdir()
        Path("scripts/unreviewed.py").write_text("print('unexpected')\n")
        self.real_run("git", "add", "scripts")
        self.real_run("git", "commit", "-qm", "unexpected agent commit")
        with self.assertRaisesRegex(RuntimeError, "Unexpected changed file"):
            delivery.publish()

    def test_tracked_pointer_not_published_and_staging_it_is_rejected(self):
        Path(".specify/feature.json").write_text('{"feature_directory":"specs/old"}\n')
        self.real_run("git", "add", "-f", ".specify/feature.json")
        self.real_run("git", "commit", "-qm", "legacy tracked pointer")
        self.base = self.real_run("git", "rev-parse", "HEAD")
        self.real_run("git", "update-ref", "refs/remotes/origin/main", self.base)
        self.ready()
        delivery.publish()
        self.assertEqual('{"feature_directory":"specs/old"}',
                         self.real_run("git", "show", "HEAD:.specify/feature.json"))
        self.real_run("git", "add", ".specify/feature.json")
        with self.assertRaisesRegex(RuntimeError, "Unstage"):
            delivery.publish()

    def test_success_and_retry_reuse_commit_and_draft_pr(self):
        self.ready()
        delivery.publish()
        head = self.real_run("git", "rev-parse", "HEAD")
        delivery.publish()
        self.assertEqual(head, self.real_run("git", "rev-parse", "HEAD"))
        self.assertEqual(self.base, self.real_run("git", "rev-parse", "main"))
        self.assertEqual(len(self.remote_prs), 1)
        self.assertIn(delivery.TRAILER, self.real_run("git", "log", "-1", "--format=%B"))
        self.assertNotIn(".specify/feature.json", self.real_run("git", "ls-files"))
        create = next(e for e in self.events if e[:3] == ("gh", "pr", "create"))
        self.assertIn("--draft", create)
        self.assertEqual(create[create.index("--base") + 1], "main")
        self.assertIn("Closes #1", create[create.index("--body") + 1])
        pushes = [e for e in self.events if e[:2] == ("git", "push")]
        self.assertTrue(all("HEAD:refs/heads/demo/delivery-" in e[-1] for e in pushes))
        self.assertFalse(any("--force" in e for e in pushes))

    def test_push_failure_is_retryable_and_closed_pr_is_not_reused(self):
        self.ready()
        self.fail_push = True
        with self.assertRaisesRegex(RuntimeError, "push failed"):
            delivery.publish()
        self.assertFalse(self.remote_prs)
        self.fail_push = False
        delivery.publish()
        self.remote_prs[0]["state"] = "MERGED"
        with self.assertRaisesRegex(RuntimeError, "closed or merged"):
            delivery.publish()


if __name__ == "__main__":
    unittest.main()
