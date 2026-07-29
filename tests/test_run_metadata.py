from utils.run_metadata import build_run_metadata, file_sha256


def test_file_sha256_hashes_file(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("alpha: 1\n", encoding="utf-8")

    assert len(file_sha256(path)) == 64


def test_build_run_metadata_includes_config_hash(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("alpha: 1\n", encoding="utf-8")

    metadata = build_run_metadata(
        model_version="variant_j",
        config_paths=[path],
        data_cutoff="2025_w12",
    )

    assert metadata["model_version"] == "variant_j"
    assert metadata["data_cutoff"] == "2025_w12"
    assert metadata["commit_sha"]
    assert metadata["config_sha256"]
    assert str(path) in metadata["config_hashes"]
