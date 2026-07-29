from pathlib import Path

import pytest

from metrics.variant_registry import active_variants, filter_variants, load_variants


def test_load_variants_requires_one_champion(tmp_path):
    path = tmp_path / "variants.yaml"
    path.write_text(
        """
variants:
  - name: variant_j
    status: champion
    tag_config: config/tag_rules/variant_j.yaml
    picks_dir: data/picks_variant_j
  - name: variant_k
    status: challenger
    tag_config: config/tag_rules/variant_k.yaml
    picks_dir: data/picks_variant_k
""",
        encoding="utf-8",
    )

    variants = load_variants(path)

    assert [variant["name"] for variant in active_variants(variants)] == [
        "variant_j",
        "variant_k",
    ]


def test_load_variants_rejects_missing_champion(tmp_path):
    path = tmp_path / "variants.yaml"
    path.write_text(
        """
variants:
  - name: variant_k
    status: challenger
    tag_config: config/tag_rules/variant_k.yaml
    picks_dir: data/picks_variant_k
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="champion"):
        load_variants(path)


def test_filter_variants_by_status_and_name():
    variants = [
        {"name": "variant_j", "status": "champion"},
        {"name": "variant_k", "status": "challenger"},
        {"name": "variant_o", "status": "experimental"},
    ]

    selected = filter_variants(
        variants,
        statuses={"experimental"},
        names={"variant_o"},
    )

    assert selected == [{"name": "variant_o", "status": "experimental"}]


def test_project_variant_registry_is_valid():
    variants = load_variants(Path("config/tag_variants.yaml"))

    assert len([variant for variant in variants if variant["status"] == "champion"]) == 1
    assert {variant["name"] for variant in active_variants(variants)} >= {
        "variant_j",
        "variant_c_psdiff",
        "variant_k",
    }
