import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.apply_template_context import inject_context
from scripts.revert_template_context import revert_context


def test_roundtrip_revert(tmp_path):
    generic = tmp_path / "generic"
    private = tmp_path / "private"
    public = tmp_path / "public"
    generic.mkdir()

    (generic / "app.py").write_text("user={{ USER }}\n")

    profile = tmp_path / "profile.yaml"
    profile.write_text("USER: admin\n")

    inject_context(generic, private, profile)
    assert (private / "app.py").read_text() == "user=admin\n"

    revert_context(private, public, profile)
    assert (public / "app.py").read_text() == "user={{ USER }}\n"


def test_no_partial_word_replacement(tmp_path):
    private = tmp_path / "private"
    public = tmp_path / "public"
    private.mkdir()

    (private / "app.md").write_text("admin badmington\n")

    profile = tmp_path / "profile.yaml"
    profile.write_text("USER: admin\n")

    revert_context(private, public, profile)
    assert (public / "app.md").read_text() == "{{ USER }} badmington\n"


def test_revert_longest_match(tmp_path):
    generic = tmp_path / "generic"
    private = tmp_path / "private"
    public = tmp_path / "public"
    generic.mkdir()

    (generic / "config.py").write_text(
        "BASE_URL = \"{{ INTERNAL_URL }}\"\nAPI_URL = \"{{ INTERNAL_URL }}/{{ API_VERSION }}\"\n"
    )

    profile = tmp_path / "profile.yaml"
    profile.write_text(
        "PROTO: https\nCOMPANY_DOMAIN: acme.com\nINTERNAL_URL: https://internal.acme.com\nAPI_VERSION: v2\n"
    )

    inject_context(generic, private, profile)

    revert_context(private, public, profile)

    expected = (
        "BASE_URL = \"{{ INTERNAL_URL }}\"\n"
        "API_URL = \"{{ INTERNAL_URL }}/{{ API_VERSION }}\"\n"
    )
    assert (public / "config.py").read_text() == expected


def test_smart_match_no_boundary(tmp_path):
    private = tmp_path / "private"
    public = tmp_path / "public"
    private.mkdir()

    (private / "note.txt").write_text("ACME CorpClient")

    profile = tmp_path / "profile.yaml"
    profile.write_text("COMPANY_NAME: ACME Corp\n")

    revert_context(private, public, profile)

    assert (public / "note.txt").read_text() == "{{ COMPANY_NAME }}Client"


def test_exact_matching_requires_boundary(tmp_path):
    private = tmp_path / "private"
    public = tmp_path / "public"
    private.mkdir()

    (private / "note.txt").write_text("ACME CorpClient")

    profile = tmp_path / "profile.yaml"
    profile.write_text("COMPANY_NAME: ACME Corp\n")

    revert_context(private, public, profile, exact=True)

    assert (public / "note.txt").read_text() == "ACME CorpClient"


def test_revert_class_and_function_identifiers(tmp_path):
    generic = tmp_path / "generic"
    private = tmp_path / "private"
    public = tmp_path / "public"
    generic.mkdir()

    (generic / "app.py").write_text(
        "class {{ COMPANY_NAME }}Client:\n"
        "    def {{ FUNC_NAME }}(self):\n"
        "        pass\n"
    )

    profile = tmp_path / "profile.yaml"
    profile.write_text(
        "COMPANY_NAME: ACME Corp\n"
        "FUNC_NAME: run job\n"
    )

    inject_context(generic, private, profile)

    private_text = (private / "app.py").read_text()
    assert "class ACME_CorpClient:" in private_text
    assert "def run_job(self):" in private_text

    revert_context(private, public, profile)

    expected = (
        "class {{ COMPANY_NAME }}Client:\n"
        "    def {{ FUNC_NAME }}(self):\n"
        "        pass\n"
    )
    assert (public / "app.py").read_text() == expected


def test_revert_partial_identifier_prefix(tmp_path):
    generic = tmp_path / "generic"
    private = tmp_path / "private"
    public = tmp_path / "public"
    generic.mkdir()

    (generic / "app.py").write_text(
        "class {{ USER }}Service:\n"
        "    pass\n"
    )

    profile = tmp_path / "profile.yaml"
    profile.write_text("USER: admin\n")

    inject_context(generic, private, profile)
    assert (private / "app.py").read_text().startswith("class adminService:")

    revert_context(private, public, profile)

    expected = "class {{ USER }}Service:\n    pass\n"
    assert (public / "app.py").read_text() == expected
