import tempfile
import unittest
from pathlib import Path

from sevent4.city_dataset import CityDataset
from sevent4.layer_manifest import LayerManifest


class CityDatasetPathTest(unittest.TestCase):
    def test_symlinked_city_config_keeps_repo_root_for_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            external = base / "external" / "data" / "cities" / "testville"
            repo_city_parent = repo / "data" / "cities"
            repo_city = repo_city_parent / "testville"

            repo.mkdir()
            (repo / "pyproject.toml").write_text("[project]\nname='fake'\n", encoding="utf-8")
            repo_city_parent.mkdir(parents=True)
            external.mkdir(parents=True)
            (external / "city.yaml").write_text(
                "\n".join(
                    [
                        "id: testville",
                        "name: Testville",
                        "country: India",
                        "state: State",
                        "center: [72.0, 23.0]",
                        "bbox: [71.0, 22.0, 73.0, 24.0]",
                        "crs_metric: EPSG:32643",
                        "layers_dir: data/cities/testville/layers",
                        "source_dir: data/cities/testville/source",
                        "outputs_dir: public/cities/testville",
                    ]
                ),
                encoding="utf-8",
            )
            repo_city.symlink_to(external, target_is_directory=True)

            city = CityDataset.from_yaml(repo_city / "city.yaml")

            self.assertEqual(repo, city.repo_root)
            self.assertEqual(repo_city / "layers", city.layers_dir)
            self.assertEqual(repo_city / "source", city.source_dir)
            self.assertEqual(repo / "public" / "cities" / "testville", city.outputs_dir)

    def test_symlinked_layer_manifest_keeps_repo_root_for_layer_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = base / "repo"
            external = base / "external" / "data" / "cities" / "testville"
            repo_city_parent = repo / "data" / "cities"
            repo_city = repo_city_parent / "testville"

            repo.mkdir()
            (repo / "pyproject.toml").write_text("[project]\nname='fake'\n", encoding="utf-8")
            repo_city_parent.mkdir(parents=True)
            (external / "layers").mkdir(parents=True)
            (external / "source").mkdir()
            (external / "layers" / "wards.geojson").write_text('{"type":"FeatureCollection","features":[]}', encoding="utf-8")
            (external / "layer_manifest.json").write_text(
                '{"layers":[{"id":"wards","label":"Wards","file":"wards.geojson","kind":"fill"}]}',
                encoding="utf-8",
            )
            (external / "city.yaml").write_text(
                "\n".join(
                    [
                        "id: testville",
                        "name: Testville",
                        "country: India",
                        "state: State",
                        "center: [72.0, 23.0]",
                        "bbox: [71.0, 22.0, 73.0, 24.0]",
                        "crs_metric: EPSG:32643",
                        "layers_dir: data/cities/testville/layers",
                        "source_dir: data/cities/testville/source",
                        "outputs_dir: public/cities/testville",
                    ]
                ),
                encoding="utf-8",
            )
            repo_city.symlink_to(external, target_is_directory=True)

            city = CityDataset.from_yaml(repo_city / "city.yaml")
            manifest = LayerManifest.from_json(repo_city / "layer_manifest.json", city)

            self.assertEqual(repo_city / "layer_manifest.json", manifest.path)
            self.assertEqual("wards", manifest.layers[0].id)


if __name__ == "__main__":
    unittest.main()
