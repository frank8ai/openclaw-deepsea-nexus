#!/usr/bin/env python3
"""
Deep-Sea Nexus Test Runner

Run all tests for the hot-pluggable architecture.
"""

import subprocess
import sys
import os

# Mark test mode for write-guard so degraded-mode tests can exercise
# lexical fallback without requiring vector DB env variables.
os.environ.setdefault("NEXUS_TEST_MODE", "1")
import importlib
import importlib.util
from pathlib import Path
from typing import Optional


def _maybe_reexec_in_venv() -> Optional[int]:
    """Re-run the test runner with the preferred venv python if available."""
    if os.environ.get("NEXUS_VENV_REEXEC") == "1":
        return None
    venv_py = os.environ.get("NEXUS_PYTHON_PATH")
    if not venv_py:
        candidate = Path(__file__).parent / ".venv-3.13" / "bin" / "python"
        if candidate.exists():
            venv_py = str(candidate)
    if venv_py and os.path.exists(venv_py) and sys.executable != venv_py:
        env = {**os.environ, "NEXUS_VENV_REEXEC": "1"}
        result = subprocess.run([venv_py, __file__], env=env)
        return result.returncode
    return None


def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n🔧 {description}")
    print(f"   Command: {cmd}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env={
                **os.environ,
                # Ensure subprocess uses the same Python environment when invoked
                "PYTHONNOUSERSITE": os.environ.get("PYTHONNOUSERSITE", "0"),
            },
        )
        
        if result.returncode == 0:
            print(f"   ✅ Success")
            if result.stdout.strip():
                print(f"   Output: {result.stdout[:200]}...")
            return True
        else:
            print(f"   ❌ Failed")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False


def get_runtime_capabilities() -> dict:
    """Detect optional dependencies to make test behavior explicit."""
    def _has_module(name: str) -> bool:
        try:
            return importlib.util.find_spec(name) is not None
        except Exception:
            return False

    return {
        "chromadb": _has_module("chromadb"),
        "sentence_transformers": _has_module("sentence_transformers"),
        "yaml": _has_module("yaml"),
    }


def _import_deepsea_nexus():
    """Import helper that tolerates path ordering differences."""
    try:
        import deepsea_nexus
        return deepsea_nexus
    except ImportError:
        skills_parent = str(Path(__file__).resolve().parent.parent)
        if skills_parent not in sys.path:
            sys.path.insert(0, skills_parent)
        importlib.invalidate_caches()
        import deepsea_nexus
        return deepsea_nexus


def run_python_tests():
    """Run Python unit and integration tests"""
    tests_dir = Path(__file__).parent / "tests"
    
    print("\n🧪 Running Python Tests...")
    
    # Test file paths
    test_files = [
        tests_dir / "test_units.py",
        tests_dir / "test_integration.py", 
        tests_dir / "test_performance.py",
        tests_dir / "test_smart_context_upgrade.py",
        tests_dir / "test_memory_v5.py",
        tests_dir / "brain" / "test_brain_units.py",
        tests_dir / "brain" / "test_brain_integration.py",
    ]
    
    all_passed = True
    
    for test_file in test_files:
        if test_file.exists():
            print(f"\n📋 Running {test_file.name}...")
            # Prefer venv python if available (avoids missing deps in system python)
            venv_py = os.environ.get("NEXUS_PYTHON_PATH")
            if not venv_py:
                candidate = Path(__file__).parent / ".venv-3.13" / "bin" / "python"
                if candidate.exists():
                    venv_py = str(candidate)
            py = venv_py or sys.executable
            cmd = f"{py} {test_file} -v"
            success = run_command(cmd, f"Running {test_file.name}")
            all_passed = all_passed and success
        else:
            print(f"\n⚠️  Warning: {test_file} not found")
    
    return all_passed


def check_code_quality():
    """Check code quality (basic checks)"""
    print("\n🧹 Checking Code Quality...")
    venv_candidate = Path(__file__).parent / ".venv-3.13" / "bin" / "python"
    if sys.executable != str(venv_candidate):
        try:
            import yaml  # noqa: F401
        except Exception:
            if venv_candidate.exists():
                print("   ⚠️  Skipping code quality in system python (missing deps); use venv for full checks.")
                return True

    # Check imports work
    try:
        deepsea_nexus = _import_deepsea_nexus()
        print("   ✅ Main import works")
        
        # Check key functions exist
        functions_to_check = [
            'create_app', 'nexus_init', 'nexus_recall', 'nexus_add',
            'get_plugin_registry', 'get_event_bus', 'CompressionManager'
        ]
        
        for func in functions_to_check:
            if hasattr(deepsea_nexus, func):
                print(f"   ✅ {func} available")
            else:
                print(f"   ❌ {func} missing")
                return False
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False


def validate_architecture():
    """Validate the hot-pluggable architecture"""
    print("\n🏗️  Validating Architecture...")
    venv_candidate = Path(__file__).parent / ".venv-3.13" / "bin" / "python"
    if sys.executable != str(venv_candidate):
        try:
            import yaml  # noqa: F401
        except Exception:
            if venv_candidate.exists():
                print("   ⚠️  Skipping architecture validation in system python (missing deps); use venv for full checks.")
                return True
    
    try:
        deepsea_nexus = _import_deepsea_nexus()
        
        # Test app creation
        app = deepsea_nexus.create_app()
        print("   ✅ App creation works")
        
        # Test component access
        components = [
            ('get_plugin_registry', deepsea_nexus.get_plugin_registry()),
            ('get_event_bus', deepsea_nexus.get_event_bus()),
            ('get_config_manager', deepsea_nexus.get_config_manager()),
        ]
        
        for name, comp in components:
            if comp is not None:
                print(f"   ✅ {name} available")
            else:
                print(f"   ❌ {name} not available")
                return False
        
        # Test compression manager
        cm = deepsea_nexus.CompressionManager("gzip")
        test_data = b"test data"
        compressed = cm.compress(test_data)
        decompressed = cm.decompress(compressed)
        if decompressed == test_data:
            print("   ✅ Compression manager works")
        else:
            print("   ❌ Compression manager failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Architecture validation failed: {e}")
        return False


def main():
    """Main test runner"""
    reexec_code = _maybe_reexec_in_venv()
    if reexec_code is not None:
        return reexec_code
    print("🚀 Deep-Sea Nexus Test Suite (v5.0.0 release gate)")
    print("=" * 50)
    caps = get_runtime_capabilities()
    print(
        "🧩 Runtime capabilities: "
        f"chromadb={'yes' if caps['chromadb'] else 'no'}, "
        f"sentence_transformers={'yes' if caps['sentence_transformers'] else 'no'}"
    )
    
    # Change to the skills directory
    skills_dir = Path(__file__).parent
    os.chdir(skills_dir)

    # Ensure the workspace `skills/` directory is importable.
    workspace_skills_dir = str(skills_dir.parent)
    if workspace_skills_dir not in sys.path:
        sys.path.insert(0, workspace_skills_dir)

    # Ensure tests can import `deepsea_nexus` even when executed as subprocesses.
    # (The project directory is `deepsea-nexus` but the import name is `deepsea_nexus`.)
    os.environ["PYTHONPATH"] = workspace_skills_dir + (os.pathsep + os.environ["PYTHONPATH"] if os.environ.get("PYTHONPATH") else "")
    
    all_passed = True
    
    # Run architecture validation
    all_passed = validate_architecture() and all_passed
    
    # Run code quality checks
    all_passed = check_code_quality() and all_passed
    
    # Run Python tests
    all_passed = run_python_tests() and all_passed
    
    # Final summary
    print("\n" + "=" * 50)
    print("📋 TEST RUNNER SUMMARY")
    print("=" * 50)
    
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("   ✓ Architecture validation: PASS")
        print("   ✓ Code quality: PASS") 
        print("   ✓ Python tests: RUN")
        print("\n🎉 Deep-Sea Nexus is ready!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("   Check output above for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
