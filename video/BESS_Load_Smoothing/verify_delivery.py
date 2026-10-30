"""Verify the delivered film, numerical assets and preserved source evidence."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import sys
import numpy as np
import av
from data_pipeline import sha, power_metrics
from source_reader import average
from shaft_twist import load_twist_data, summary as twist_summary, GAUGE_GAIN
from render_video import SCENES, TITLES, probe

HERE=Path(__file__).resolve().parent


def verify(project_root=None):
    checks=[]
    def check(name,passed,detail=None):
        checks.append({'name':name,'status':'PASS' if bool(passed) else 'FAIL','detail':detail})
    video=HERE/'output/BESS_Abrupt_Loads_1080p.mp4'
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-show_chapters','-of','json',str(video)]))
    stream=next(s for s in info['streams'] if s['codec_type']=='video')
    check('full_hd',stream['width']==1920 and stream['height']==1080)
    check('frame_rate',stream['avg_frame_rate']=='30/1',stream['avg_frame_rate'])
    check('portable_h264',stream['codec_name']=='h264' and stream['pix_fmt']=='yuv420p',{'codec':stream['codec_name'],'pixel_format':stream['pix_fmt']})
    timeline=json.loads((HERE/'evidence/final_timeline.json').read_text())
    approved=['Applications','ParallelBuffer','PowerComparison','ShaftMechanism','MeasuredBenefits']
    check('approved_five_scene_order',[c['scene'] for c in timeline]==approved)
    check('duration_matches_timeline',abs(float(info['format']['duration'])-timeline[-1]['end_s'])<.05,info['format']['duration'])
    check('five_chapters',len(info['chapters'])==5)
    check('chapter_titles',[c.get('tags',{}).get('title') for c in info['chapters']]==TITLES)
    check('ends_on_measured_results',info['chapters'][-1].get('tags',{}).get('title')=='Measured benefits')
    count=0; previous=None; monotonic=True; first_time=None;last_time=None
    with av.open(str(video)) as container:
        for frame in container.decode(video=0):
            t=float(frame.pts*frame.time_base)
            if previous is not None and t<=previous:monotonic=False
            if first_time is None:first_time=t
            previous=t;last_time=t;count+=1
    check('full_video_decode',count==int(stream['nb_frames']) and count>0,count)
    check('strictly_increasing_frame_timestamps',monotonic)
    check('no_missing_time',abs((last_time-first_time+1/30)-count/30)<.06,
          {'decoded_frames':count,'first_s':first_time,'last_s':last_time})
    metrics=json.loads((HERE/'data/metrics.json').read_text())
    provenance=json.loads((HERE/'data/provenance.json').read_text())
    check('raw_archive_hash',sha(HERE/'data/raw_selected.npz')==provenance['raw_archive_sha256'])
    check('display_archive_hash',sha(HERE/'data/display.npz')==provenance['display_archive_sha256'])
    raw=np.load(HERE/'data/raw_selected.npz'); display=np.load(HERE/'data/display.npz')
    check('same_raw_timeline',np.array_equal(raw['without__time'],raw['with__time']))
    check('same_raw_load_command',np.array_equal(raw['without__Pload_command_MW'],raw['with__Pload_command_MW']))
    for case in ['without','with']:
        t=raw[case+'__time']
        check(case+'_source_sampling',np.allclose(np.diff(t),.0001,rtol=0,atol=1e-11))
        check(case+'_duration',abs(t[-1]-30)<1e-10)
        for ch in ['Pgen_MW','Pgrid_MW']:
            p=average(t,raw[case+'__'+ch]);m=power_metrics(t,p)
            check(case+'_'+ch+'_metrics_reproduced',all(abs(m[k]-metrics[case][ch][k])<1e-8 for k in m))
        td=display[case+'__time'];j=np.searchsorted(t,td)
        for ch in ['Shaft_T12_pu','Shaft_T23_pu','Shaft_theta1_rad','Shaft_theta2_rad','Shaft_theta3_rad']:
            check(case+'_'+ch+'_unfiltered',np.array_equal(raw[case+'__'+ch][j],display[case+'__'+ch]))
        snap=HERE/'evidence'/case
        model=next(snap.glob('*.pscx'))
        check(case+'_snapshot_hash',sha(model)==provenance[case]['source_project_sha256'])
        if project_root is not None:
            canonical=project_root/'pscad'/model.name
            check(case+'_canonical_model_unchanged',sha(canonical)==provenance[case]['source_project_sha256'])
            folder=project_root/provenance[case]['original_folder']
            errors=[name for name,h in provenance[case]['original_outputs_sha256'].items() if sha(folder/name)!=h]
            check(case+'_original_outputs_unchanged',not errors,errors)
    vendor=HERE/'vendor'
    manifest=json.loads((vendor/'SOURCE_MANIFEST.json').read_text())
    vendor_bad=[]
    for f in manifest['files']:
        b=(vendor/f['path']).read_bytes()
        if hashlib.sha256(b).hexdigest()!=f['local_sha256']:vendor_bad.append(f['path'])
        if 'sha' in f and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()!=f['sha']:vendor_bad.append(f['path']+' upstream')
    check('official_schemdraw_identity',not vendor_bad,vendor_bad)
    inventories=[HERE/'evidence/inventories'/(s+'.json') for s in SCENES]
    check('five_active_scene_inventories',len(inventories)==5 and all(p.is_file() for p in inventories))
    all_text=[];all_math=[]
    for p in inventories:
        d=json.loads(p.read_text());all_text+=d['text'];all_math+=d['math']
    check('numerals_excluded_from_plain_text',not any(re.search(r'\d',s) for s in all_text))
    check('no_data_center_on_screen',not any(re.search(r'data\s*center|datacenter',s,re.I) for s in all_text+all_math))
    check('latex_inventory_present',len(set(all_math))>20,len(set(all_math)))
    check('contextual_torsion_note_visible','Slow motion  |  Amplitudes are step-size sensitive' in all_text)
    check('removed_slide_text_absent',not any(s in all_text for s in ['A closer look at the load step','Buffer the load. Verify the shaft.','Shaft damping not established']))
    check('four_generic_load_examples',all(s in all_text for s in ['Motors','Rolling mills','Cranes','Pulsed loads']))
    twist=twist_summary(load_twist_data(HERE/'data/display.npz'))
    recorded=json.loads((HERE/'evidence/shaft_twist_revision.json').read_text())
    check('twist_summary_reproduced',twist==recorded)
    check('twist_common_gain_visible',GAUGE_GAIN==200 and r'\times200' in all_math)
    for case in ['without','with']:
        check(case+'_twist_zero_pre_step_mean',abs(twist['cases'][case]['baseline_mean_change_rad'])<1e-12)
    check('twist_visible_excursion',50<twist['cases']['without']['peak_visual_deflection_deg']<65,
          twist['cases']['without']['peak_visual_deflection_deg'])
    check('twist_with_bess_uses_same_scale',0<twist['cases']['with']['peak_visual_deflection_deg']<5,
          twist['cases']['with']['peak_visual_deflection_deg'])
    baseline=json.loads((HERE/'evidence/revision_baseline.json').read_text())
    edit_baseline=json.loads((HERE/'evidence/edit_baseline.json').read_text())
    converter_baseline=json.loads((HERE/'evidence/converter_baseline.json').read_text())
    check('chapter_timing_unchanged',sha(HERE/'evidence/final_timeline.json')==converter_baseline['preserved_files']['evidence/final_timeline.json']['sha256'])
    check('original_display_data_unchanged',sha(HERE/'data/display.npz')==baseline['source_display_sha256'])
    asset_changes={name for name,old_sha in converter_baseline['previous_assets_sha256'].items()
                   if sha(HERE/'assets'/name)!=old_sha}
    check('only_converter_assets_changed',asset_changes=={'converter.svg','parallel_single_line.svg'},sorted(asset_changes))
    chapters=HERE/'media/final/videos/scenes/1080p30'
    if chapters.exists():
        differences=[s for s in SCENES if s!='ParallelBuffer' and
                     sha(chapters/(s+'.mp4'))!=converter_baseline['previous_chapters_sha256'][s+'.mp4']]
        check('four_other_retained_chapters_unchanged',not differences,differences)
        check('converter_chapter_revised',sha(chapters/'ParallelBuffer.mp4')!=converter_baseline['previous_chapters_sha256']['ParallelBuffer.mp4'])
        check('shaft_chapter_revised',sha(chapters/'ShaftMechanism.mp4')!=baseline['previous_chapters_sha256']['ShaftMechanism.mp4'])
        check('standalone_scene_matches_chapter',sha(HERE/'output/Shaft_Twist_Comparison_1080p.mp4')==sha(chapters/'ShaftMechanism.mp4'))
        expected_frames=sum(int(next(s for s in probe(chapters/(name+'.mp4'))['streams'] if s['codec_type']=='video')['nb_frames']) for name in SCENES)
        check('only_selected_frames_in_video',count==expected_frames,{'decoded':count,'selected_chapters':expected_frames})
    if project_root is not None:
        history=Path(baseline['history_folder'])
        if not history.resolve().is_relative_to(project_root.resolve()):
            raise ValueError('History path outside original project')
        changed=[name for name,item in baseline['preserved_files'].items() if sha(history/name)!=item['sha256']]
        check('previous_delivery_and_sources_preserved',not changed,changed)
        edit_history=Path(edit_baseline['history_folder'])
        if not edit_history.resolve().is_relative_to(project_root.resolve()):
            raise ValueError('Editorial history path outside original project')
        changed=[name for name,item in edit_baseline['preserved_files'].items() if sha(edit_history/name)!=item['sha256']]
        check('pre_cut_delivery_preserved',not changed,changed)
        converter_history=Path(converter_baseline['history_folder'])
        if not converter_history.resolve().is_relative_to(project_root.resolve()):
            raise ValueError('Converter history path outside original project')
        changed=[name for name,item in converter_baseline['preserved_files'].items() if sha(converter_history/name)!=item['sha256']]
        check('pre_converter_fix_delivery_preserved',not changed,changed)
    for p in [HERE/'evidence/logs'/('final_'+s+'.log') for s in SCENES]:
        text=p.read_text(encoding='utf-8')
        check('render_log_'+p.stem,not any(s in text for s in ['Traceback (most recent call last)','LaTeX compilation error','ERROR']))
    process=subprocess.run([sys.executable,'-m','unittest','test_data_pipeline','test_shaft_twist'],cwd=HERE,capture_output=True,text=True)
    check('data_pipeline_tests',process.returncode==0,process.stdout+process.stderr)
    review_path=HERE/'evidence/visual_review.json'
    if review_path.exists():
        review=json.loads(review_path.read_text())
        check('visual_review',review.get('status')=='PASS',review.get('scope'))
        check('converter_visual_review',review.get('checks',{}).get('converter_AC_top_DC_bottom')=='PASS')
    else:
        check('visual_review',False,'Visual review record missing')
    report={'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL',
            'checks_passed':sum(c['status']=='PASS' for c in checks),'checks_total':len(checks),
            'video_sha256':sha(video),'video_bytes':video.stat().st_size,
            'video_duration_s':float(info['format']['duration']),'decoded_frames':count,
            'original_project_verification':str(project_root) if project_root else 'Skipped; portable package mode',
            'checks':checks}
    (HERE/'evidence/delivery_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
    for c in checks:
        if c['status']=='FAIL':print(c)
    return report['status']=='PASS'


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project-root',type=Path)
    args=p.parse_args();raise SystemExit(0 if verify(args.project_root) else 1)
