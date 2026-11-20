"""Machine-readable runtime check, executable without project dependencies."""
import json
import sys

result = {'executable': sys.executable, 'version': list(sys.version_info[:3]), 'dependencies': {}}
try:
    if sys.version_info < (3, 11):
        raise RuntimeError('Python 3.11+ required')
    import numpy
    import PIL
    result['dependencies'] = {'numpy': numpy.__version__, 'Pillow': PIL.__version__}
    result['ready'] = True
except Exception as exc:
    result.update(ready=False, reason=str(exc))
print(json.dumps(result))
sys.exit(0 if result['ready'] else 1)
