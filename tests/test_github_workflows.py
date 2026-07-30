"""Regression checks for GitHub Actions workflow contracts."""

from __future__ import annotations

from pathlib import Path


def test_phoenix_smoke_verifies_multiple_trace_markers() -> None:
    """The Phoenix smoke job must prove more than one persisted trace."""
    workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "main.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "export TRACE_COUNT=3" in text
    assert "for index in range(1, trace_count + 1):" in text
    assert "trace_markers.append(trace_name)" in text
    assert "for marker in $(cat /tmp/agentseek-trace-markers.txt); do" in text
    assert "Verified ${verified_count} Phoenix trace markers persisted in OceanBase seekdb." in text


def test_hybrid_template_smoke_runs_rendered_project_tests() -> None:
    """The hybrid template should be tested after rendering, not only by static source checks."""
    workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "main.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "agentic-rag-hybrid-template-smoke:" in text
    assert "agentseek create langchain/agentic-rag-hybrid --no-input" in text
    assert "uv sync --extra dev" in text
    assert "uv run python -m pytest" in text


def test_agentic_rag_template_smoke_runs_rendered_project_tests() -> None:
    """The agentic RAG template should prove embedded add-and-retrieve after rendering."""
    workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "main.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "agentic-rag-template-smoke:" in text
    assert 'agentseek create "${GITHUB_WORKSPACE}/templates/langchain/agentic-rag" --no-input' in text
    assert 'cd "${AGENTSEEK_RAG_SMOKE_PROJECT}"' in text
    assert "uv sync --extra dev" in text
    assert "uv run python -m pytest" in text


def test_hybrid_template_smoke_builds_rendered_frontend() -> None:
    """The hybrid smoke should install and production-build the rendered frontend."""
    workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "main.yml"
    text = workflow.read_text(encoding="utf-8")

    assert 'cd "${AGENTSEEK_HYBRID_SMOKE_PROJECT}/frontend"' in text
    assert "npm install" in text
    assert "npm run build" in text


def test_openvino_template_smoke_is_path_gated_and_invokes_graph() -> None:
    """The heavy OpenVINO smoke should run only for relevant PRs and prove runtime wiring."""
    workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "openvino-template-smoke.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "permissions:" in text
    assert "contents: read" in text
    assert "concurrency:" in text
    assert "workflow_dispatch:" in text
    assert "pull_request:" in text
    assert ".github/workflows/openvino-template-smoke.yml" in text
    assert ".github/actions/setup-python-env/**" in text
    assert "pyproject.toml" in text
    assert "uv.lock" in text
    assert "src/agentseek/**" in text
    assert "templates/index.json" in text
    assert "templates/langchain/agentic-rag-openvino/**" in text
    assert "tests/cli_commands/test_templates_render.py" in text
    assert "tests/test_github_workflows.py" in text
    assert "runs-on: ubuntu-latest" in text
    assert "agentseek create langchain/agentic-rag-openvino --no-input" in text
    assert "agentseek task sync" in text
    assert "agentseek task models" in text
    assert "until docker compose exec -T seekdb mysql" in text
    assert "openvino-smoke-fixture.md" in text
    assert "cobalt-lantern-42" in text
    assert "uv run ingest openvino-smoke-fixture.md" in text
    assert "agentseek task ingest-sample" not in text
    assert "lilianweng.github.io" not in text
    assert "agentseek dev --dry-run" in text
    assert "from langchain_core.messages import HumanMessage" in text
    assert "from my_openvino_rag_agent import agent as agent_module" in text
    assert "agent_module.retrieve = verified_retrieve" in text
    assert "retrieval_calls.clear()" in text
    assert "OpenVINO retrieval did not return fixture context" in text
    assert "OpenVINO graph did not call retrieval during sync invoke" in text
    assert "OpenVINO graph did not call retrieval during async invoke" in text
    assert "graph.invoke" in text
    assert "graph.ainvoke" in text
    assert "asyncio.run" in text
    assert "OpenVINO graph returned empty response" in text
    assert "OpenVINO async graph returned empty response" in text


def test_tag_release_rechecks_candidate_anchored_legacy_compatibility() -> None:
    """A tag may not reach the build job without every published v1 resolver passing at its SHA."""
    workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "on-release-main.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "legacy-template-compatibility:" in text
    assert 'version: ["0.0.1", "0.0.2", "0.0.3", "0.0.4", "0.0.5"]' in text
    assert "UV_TOOL_DIR: ${{ runner.temp }}/agentseek-legacy-tools" in text
    assert 'python scripts/check_legacy_template_compat.py "${{ matrix.version }}"' in text
    assert '--candidate-ref "${{ github.sha }}"' in text
    assert "needs: [validate-version, legacy-template-compatibility]" in text


def test_legacy_tool_directory_uses_runner_context_only_at_step_scope() -> None:
    """The runner context is unavailable in job-level env expressions."""
    workflows = Path(__file__).resolve().parents[1] / ".github" / "workflows"
    cases = [
        (workflows / "main.yml", "  legacy-template-compatibility:", "  contrib-package-checks:", 2),
        (workflows / "on-release-main.yml", "  legacy-template-compatibility:", "  build:", 1),
    ]

    for workflow, start_marker, end_marker, expected_count in cases:
        text = workflow.read_text(encoding="utf-8")
        job = text[text.index(start_marker) : text.index(end_marker)]
        job_header = job[: job.index("    steps:")]
        assert "runner.temp" not in job_header
        assert job.count("UV_TOOL_DIR: ${{ runner.temp }}/agentseek-legacy-tools") == expected_count


def test_tag_release_runs_focused_catalog_contract_tests() -> None:
    """The immutable catalog and release validators must run again from the tagged source."""
    workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "on-release-main.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "tests/test_release_version.py" in text
    assert "tests/cli_commands/test_locked_catalog.py" in text
    assert "tests/test_legacy_template_compat.py" in text
    assert "--verify-remote-tags" in text


def test_tag_release_requires_the_peeled_commit_to_be_merged_to_main() -> None:
    """An authorized tag from an unmerged branch must not be publishable."""
    workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "on-release-main.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "fetch-depth: 0" in text
    assert "git fetch --no-tags origin +refs/heads/main:refs/remotes/origin/main" in text
    assert 'tag_commit="$(git rev-list -n 1 "${GITHUB_REF_NAME}")"' in text
    assert 'git merge-base --is-ancestor "${tag_commit}" refs/remotes/origin/main' in text


def test_tag_release_smokes_the_built_wheel_before_uploading_it() -> None:
    """PyPI input must be the wheel that listed, fetched, rendered, and described the locked template."""
    workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "on-release-main.yml"
    text = workflow.read_text(encoding="utf-8")

    smoke_start = text.index("- name: Smoke built wheel against locked catalog")
    upload_start = text.index("- name: Upload artifacts")
    smoke = text[smoke_start:upload_start]

    assert "uv pip install" in smoke
    assert "sdists=(dist/*.tar.gz)" in smoke
    assert 'uv pip install --no-cache --python "${sdist_python_bin}" "${sdists[0]}"' in smoke
    assert '"${sdist_agentseek_bin}" create --list-templates' in smoke
    assert "for index, key in enumerate(lock.templates)" in smoke
    assert "_extract_template_archive(archive, candidate, lock, key)" in smoke
    assert "create --list-templates" in smoke
    assert "http_proxy=http://127.0.0.1:9" in smoke
    assert "https_proxy=http://127.0.0.1:9" in smoke
    assert "all_proxy=http://127.0.0.1:9" in smoke
    assert "create bub/default --no-input" in smoke
    assert "info --json" in smoke
    assert "json.load" in smoke
    assert smoke_start < upload_start


def test_tag_release_verifies_built_distribution_provenance() -> None:
    """The wheel and sdist must retain the immutable catalog and reviewed build-skill source."""
    workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "on-release-main.yml"
    text = workflow.read_text(encoding="utf-8")

    assert 'skills_ref="4f09937234d128656fdc8c8658c840ebbf7e28d1"' in text
    assert "https://github.com/PsiACE/skills.git" in text
    assert 'fetch --depth 1 origin "${skills_ref}"' in text
    assert 'test "$(git -C "${skills_source}" rev-parse HEAD)" = "${skills_ref}"' in text
    assert '--wheel "${wheels[0]}"' in text
    assert '--sdist "${sdists[0]}"' in text
    assert '--skills-root "${AGENTSEEK_PINNED_SKILLS_ROOT}"' in text
