import os
import pytest
import yaml
import raft
from numpy.testing import assert_allclose
from raft_opt import raft_opt
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


expected_mass_fowt = {
    "spar-buoy": 812.14,   
    "oc4_semisub": 3514.02 
}


@pytest.fixture(scope="module", params=['spar-buoy', 'oc4_semisub'])
def paths(request):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_dir = os.path.join(current_dir, 'test_data', request.param)
    calcuvate_path = os.path.join(test_dir, 'calcuvate.py')
    return {
        "current_dir": current_dir,
        "test_dir": test_dir,
        "calcuvate_path": calcuvate_path,
        "folder_name": request.param
    }


@pytest.fixture(scope="module")
def design(paths):
    design_file_path = os.path.join(paths["test_dir"], f'{paths["folder_name"]}.yaml')
    with open(design_file_path) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def user_input(paths):
    user_input_file_path = os.path.join(paths["test_dir"], 'user_input.yaml')
    with open(user_input_file_path) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module", autouse=True)
def cleanup_files(request):
    output_files = ['output.txt', 'dummy.sql']

    def cleanup():
        for file in output_files:
            try:
                os.remove(file)
                print(f"Deleted file: {file}")
            except OSError as e:
                print(f"Error deleting file {file}: {e}")

    request.addfinalizer(cleanup)


@pytest.fixture(scope="module")
def mass_optimized(design, user_input, paths):
    output = "output.txt"
    optimized_design, _ = raft_opt.run_opt(
        design, user_input, paths["calcuvate_path"], output
    )

    model = raft.Model(optimized_design)
    model.analyzeUnloaded()
    model.analyzeCases(display=0)
    mass_optimized = model.fowtList[0].m_shell / 1000
    return mass_optimized


def test_sparbuoy(mass_optimized, paths):
    if paths["folder_name"] != "spar-buoy":
        pytest.skip("Skipping test for spar-buoy")

    expected_mass = expected_mass_fowt["spar-buoy"]
    assert_allclose(mass_optimized, expected_mass, rtol=1, atol=1e-1)


def test_oc4_semisub(mass_optimized, paths):
    if paths["folder_name"] != "oc4_semisub":
        pytest.skip("Skipping test for oc4_semisub")

    expected_mass = expected_mass_fowt["oc4_semisub"]
    assert_allclose(mass_optimized, expected_mass, rtol=1, atol=1e-1)

if __name__ == "__main__":
    test_sparbuoy()
    test_oc4_semisub()
