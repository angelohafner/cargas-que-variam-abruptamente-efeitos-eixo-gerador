from pathlib import Path
import json, sys, traceback
from datetime import datetime, timezone
import mhi.pscad

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / 'diagnostics'
out.mkdir(exist_ok=True)
data = {'utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version,
        'versions': mhi.pscad.versions()}
try:
    app = mhi.pscad.launch(version='5.1.0', silence=True, minimize=True,
                          timeout=30, settings={'fortran_version':'GFortran 8.1 (64-bit)'})
    data['settings'] = app.settings()
    data['projects'] = app.projects()
    data['api_methods'] = [x for x in dir(app) if any(s in x for s in ('licen','cert','port','version'))]
    for name in ('licensed','license','certificates','get_available_certificates'):
        try:
            value = getattr(app,name)
            data[name] = value() if callable(value) else value
        except Exception as exc:
            data[name] = str(exc)
    data['app_repr'] = repr(app)
    data['status'] = 'CONNECTED'
except Exception:
    data['status'] = 'FAILED'
    data['error'] = traceback.format_exc()
(out/'environment.json').write_text(json.dumps(data,indent=2,default=str),encoding='utf-8')
print(json.dumps(data,indent=2,default=str),flush=True)
