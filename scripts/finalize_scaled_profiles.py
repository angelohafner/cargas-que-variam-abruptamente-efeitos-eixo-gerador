"""Persist final definitions/views and bind the four defaults to fresh runs."""
import json
from scale_models_250_500 import main as build
from run_scale_250_500 import run, ROOT, LABELS, RESULTS
def main():
    path=RESULTS/'latest_suite.json';report=json.loads(path.read_text())
    report['status']='FINALIZING';path.write_text(json.dumps(report,indent=2))
    build()
    for case in LABELS:
        report['cases'][case]=run(case,case+'_final').relative_to(ROOT).as_posix()
        path.write_text(json.dumps(report,indent=2))
    report['status']='COMPLETE';path.write_text(json.dumps(report,indent=2))
if __name__=='__main__':main()
