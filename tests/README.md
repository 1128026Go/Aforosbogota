# Tests

La suite actual valida el pipeline de análisis avanzado (filtros, RILSA, conteos, velocidades y conflictos) del backend.

## Dependencias

```bash
pip install -r api/requirements.txt
```

## Ejecución

```bash
cd api
../venv/Scripts/pytest ../tests/test_analysis_services.py -v
```

`conftest.py` añade la raíz del proyecto al `PYTHONPATH` para simplificar los imports.

## Links Útiles

- [Documentación pytest](https://docs.pytest.org/)
- [Best practices](https://docs.pytest.org/en/stable/example/simple.html)
- [Fixtures](https://docs.pytest.org/en/stable/fixture.html)
