"""Reuse this task's session, or launch PSCAD without touching other processes."""
from pathlib import Path
import json
import mhi.pscad
from mhi.common import process
ROOT=Path(__file__).resolve().parents[1]
def get_app(port=None):
    record=ROOT/'diagnostics/session.json'
    if port is not None:
        return mhi.pscad.connect(port=port)
    if record.exists():
        try:
            data=json.loads(record.read_text());app=mhi.pscad.connect(port=data['port'],timeout=3)
            if app.licensed():return app
        except (OSError,ValueError,RuntimeError,TimeoutError):pass
    port=process.unused_tcp_port()
    app=mhi.pscad.launch(port=port,version='5.1.0',silence=True,minimize=True,timeout=30,
                         settings={'fortran_version':'GFortran 8.1 (64-bit)'})
    if not app.licensed():raise RuntimeError('PSCAD connected but no active license is available')
    record.parent.mkdir(exist_ok=True)
    # This is the newly launched task process, not another user's open session.
    app.new_workspace(str(record.parent/'Automation.pswx'))
    record.write_text(json.dumps({'port':port,'version':app.version},indent=2))
    return app
