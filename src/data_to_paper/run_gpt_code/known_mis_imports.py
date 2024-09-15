import importlib

KNOWN_MIS_IMPORTS = {
    'Mediation': 'statsmodels.stats.mediation',
}


# assert KNOWN_MIS_IMPORTS:
def _assert_known_mis_imports():
    for name, module in KNOWN_MIS_IMPORTS.items():
        try:
            importlib.import_module(module, name)
        except ImportError:
            raise ImportError(f"Wrong imports in KNOWN_MIS_IMPORTS.\nFailed importing {name} from {module}")


_assert_known_mis_imports()
