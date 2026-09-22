"""One discoverable CLI; commands return JSON suitable for agent tool calls."""
import argparse
import json
import sys
from pathlib import Path
from .files import read, write
from .project import Project


def parser():
    root=argparse.ArgumentParser(prog='agent4ppt',description='Plan, produce and export image-led presentations.')
    from . import __version__
    root.add_argument('--version',action='version',version=f'agent4ppt {__version__}')
    commands=root.add_subparsers(dest='command',required=True)
    ingest=commands.add_parser('import-image',help='Validate and copy an explicitly selected host image; does not register a stage')
    ingest.add_argument('--source',required=True);ingest.add_argument('--out',required=True)
    ingest.add_argument('--sha256',help='Expected hash of the selected tool output, when available')
    comparison=commands.add_parser('compare-render',help='Measure text raster differences and create per-object target/render panels')
    comparison.add_argument('project');comparison.add_argument('--review-file',required=True)
    comparison.add_argument('--preview',required=True);comparison.add_argument('--out',required=True)
    init=commands.add_parser('init',help='Create a project from a JSON brief')
    init.add_argument('project');init.add_argument('--brief',required=True)
    commands.add_parser('prepare',help='Write all page planning requests without claiming work').add_argument('project')
    schedule=commands.add_parser('dispatch-plan',help='Recommend maximum available page-worker dispatch without claiming or spawning')
    schedule.add_argument('project');schedule.add_argument('--host-slots',type=int,required=True)
    schedule.add_argument('--sample-page',type=int)
    native_batch=commands.add_parser('mcp-batch',help='Validate one page correction batch for host MCP execution; does not edit a deck')
    native_batch.add_argument('--spec',required=True);native_batch.add_argument('--out',required=True)
    template=commands.add_parser('template',help='Write an example brief for the selected production mode')
    template.add_argument('--out',required=True);template.add_argument('--mode',choices=['full_slide','editable'],default='full_slide')
    guide=commands.add_parser('layout-guide',help='Create a diagnostic native-overlay reservation guide before generation')
    guide.add_argument('--page-file',required=True);guide.add_argument('--out',required=True)
    guide.add_argument('--ratio',choices=['16:9','4:3'],default='16:9')
    bridge=commands.add_parser('image-job',help='Convert a saved request into an API job, preserving every reference')
    bridge.add_argument('--request',required=True);bridge.add_argument('--out',required=True);bridge.add_argument('--save',required=True)
    for name in ('status','history'):
        commands.add_parser(name).add_argument('project')
    claim=commands.add_parser('claim',help='Lease a page and return a self-contained generation request')
    claim.add_argument('project');claim.add_argument('--worker',required=True);claim.add_argument('--page',type=int);claim.add_argument('--lease',type=float,default=900)
    compose=commands.add_parser('compose',help='Compose one editable page for rendering and review; does not complete it')
    compose.add_argument('project');compose.add_argument('--page',type=int,required=True);compose.add_argument('--token',required=True)
    compose.add_argument('--image',required=True);compose.add_argument('--out',required=True)
    compose.add_argument('--native-draft',help='Adopt a host-adjusted single-page compose draft; preserve native text formatting')
    for stage in ('design','background'):
        item=commands.add_parser('record-'+stage,help='Register a reviewed full-slide-first conversion artifact')
        item.add_argument('project');item.add_argument('--page',type=int,required=True);item.add_argument('--token',required=True)
        item.add_argument('--image',required=True);item.add_argument('--method-file',required=True);item.add_argument('--qa',required=True)
        if stage=='design':item.add_argument('--overlays-file',required=True,help='JSON array measured from the finished design; preserve IDs and contents')
    for name in ('complete','fail','renew'):
        item=commands.add_parser(name);item.add_argument('project');item.add_argument('--page',type=int,required=True);item.add_argument('--token',required=True)
        if name=='complete':
            item.add_argument('--image',required=True);item.add_argument('--backend',required=True);item.add_argument('--qa',required=True);item.add_argument('--sample',action='store_true')
            item.add_argument('--method-file',help='JSON describing the actual image tool, mode and exposed settings')
            item.add_argument('--review-file',help='Receipt returned by compose for an editable page')
            item.add_argument('--preview',help='Rendered image of the composed PPTX, visually inspected by the host')
            item.add_argument('--qa-report',help='Structured visual QA JSON bound to this composition and preview')
        elif name=='fail':item.add_argument('--reason',required=True)
        else:item.add_argument('--lease',type=float,default=900)
    revision=commands.add_parser('revise',help='Invalidate a lease/result and prepare a revised page')
    revision.add_argument('project');revision.add_argument('--page',required=True,type=int);revision.add_argument('--reason',required=True);revision.add_argument('--page-file')
    export=commands.add_parser('export',help='Export only a fully verified project')
    export.add_argument('project');export.add_argument('--out');export.add_argument('--max-image-mb',type=float)
    assemble=commands.add_parser('assemble',help='Assemble existing page images without claiming they were generated by this project')
    assemble.add_argument('--images',nargs='+',required=True);assemble.add_argument('--out',required=True);assemble.add_argument('--notes');assemble.add_argument('--ratio',choices=['16:9','4:3'],default='16:9');assemble.add_argument('--max-image-mb',type=float)
    for name in ('image','batch'):
        item=commands.add_parser(name);item.add_argument('job');item.add_argument('--dry-run',action='store_true')
        if name=='batch':
            item.add_argument('--concurrency',type=int,default=3);item.add_argument('--fail-fast',action='store_true');item.add_argument('--report')
            item.add_argument('--defaults',help='JSON with common output directory, options and prompt brief')
    mat=commands.add_parser('key',help='Remove a specified solid background from an asset, not a finished slide')
    mat.add_argument('input');mat.add_argument('--out',required=True);mat.add_argument('--color',default='#00ff00');mat.add_argument('--tolerance',type=int,default=12);mat.add_argument('--opaque',type=int,default=96);mat.add_argument('--soft',action='store_true');mat.add_argument('--sample',choices=['none','corners','border'],default='none');mat.add_argument('--contract',type=int,default=0);mat.add_argument('--feather',type=float,default=0);mat.add_argument('--despill',action='store_true');mat.add_argument('--overwrite',action='store_true')
    style=commands.add_parser('styles');style.add_argument('--name');style.add_argument('--save');style.add_argument('--overwrite',action='store_true')
    setup=commands.add_parser('setup');setup.add_argument('--upgrade',action='store_true')
    cfg=commands.add_parser('config');cfg.add_argument('--base-url');cfg.add_argument('--model');cfg.add_argument('--key-env');cfg.add_argument('--clear-base',action='store_true')
    doctor=commands.add_parser('doctor');doctor.add_argument('--check-api',action='store_true')
    return root


def dispatch(args):
    name=args.command
    if name=='dispatch-plan':
        return Project(args.project).dispatch_plan(args.host_slots,args.sample_page)
    if name=='mcp-batch':
        from .mcp_batch import plan_batch
        result=plan_batch(read(args.spec))
        if Path(args.out).exists():raise FileExistsError('Use a new batch plan path')
        write(args.out,result)
        return {'plan':str(Path(args.out).resolve()), 'executed':False, **result}
    if name=='compare-render':
        from .comparison import compare
        return compare(Project(args.project),args.review_file,args.preview,args.out)
    if name=='import-image':
        from .ingest import import_image
        return import_image(args.source,args.out,args.sha256)
    if name=='init':
        return Project.create(args.project,read(args.brief),Path(args.brief).resolve().parent).snapshot()
    if name in ('record-design','record-background'):
        from .conversion import register
        return register(Project(args.project),args.page,args.token,name.removeprefix('record-'),args.image,
                        read(args.method_file),args.qa,read(args.overlays_file) if name=='record-design' else None)
    if name=='layout-guide':
        from .planning import layout_guide
        return layout_guide(args.page_file,args.out,args.ratio)
    if name in ('prepare','template','image-job'):
        from .planning import preview, template, api_job
        if name=='prepare':return preview(Project(args.project))
        if name=='template':return template(args.out,args.mode)
        return api_job(args.request,args.out,args.save)
    if name in ('status','history','claim','compose','complete','fail','renew','revise','export'):
        project=Project(args.project)
        if name=='status':return project.snapshot()
        if name=='history':return project.history()
        if name=='claim':return project.claim(args.worker,args.page,args.lease)
        if name=='compose':return project.compose(args.page,args.token,args.image,args.out,args.native_draft)
        if name=='complete':return project.complete(args.page,args.token,args.image,args.backend,args.qa,args.sample,
                                                   read(args.method_file) if args.method_file else None,
                                                   args.review_file,args.preview,args.qa_report)
        if name=='fail':project.fail(args.page,args.token,args.reason);return project.snapshot()
        if name=='renew':project.renew(args.page,args.token,args.lease);return {'renewed':args.page}
        if name=='revise':return project.retry(args.page,args.reason,read(args.page_file) if args.page_file else None)
        if name=='export':
            from .package import export_project
            return export_project(project,args.out,None if args.max_image_mb is None else int(args.max_image_mb*1048576))
    if name=='assemble':
        from .package import export_pptx,parse_notes
        notes=parse_notes(Path(args.notes).read_text(encoding='utf-8')) if args.notes else {}
        return export_pptx(args.images,args.out,args.ratio,notes,max_bytes=None if args.max_image_mb is None else int(args.max_image_mb*1048576))
    if name in ('image','batch','key'):
        from .imaging import generate,batch,chroma
        if name=='image':return generate(read(args.job),args.dry_run)
        if name=='batch':
            jobs=[json.loads(line) for line in Path(args.job).read_text(encoding='utf-8-sig').splitlines() if line.strip()]
            result=batch(jobs,args.concurrency,args.dry_run,args.fail_fast,
                         defaults=read(args.defaults) if args.defaults else None)
            if args.report:write(args.report,result)
            return {'ok':all(x['ok'] for x in result),'jobs':result}
        return chroma(args.input,args.out,args.color,args.tolerance,args.soft,args.opaque,args.sample,args.contract,args.feather,args.despill,args.overwrite)
    if name=='styles':
        from .styles import catalog,save
        if args.save:
            if not args.name:raise ValueError('--save requires --name')
            return save(args.name,read(args.save),args.overwrite)
        values=catalog()
        return values[args.name] if args.name else values
    from .runtime import configure,bootstrap,doctor
    if name=='config':return configure(args.base_url,args.model,args.key_env,args.clear_base)
    if name=='setup':return bootstrap(args.upgrade)
    if name=='doctor':return doctor(args.check_api)
    raise ValueError('Unknown command')


def main(argv=None):
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8',errors='backslashreplace')
    args=parser().parse_args(argv)
    try:
        result=dispatch(args)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 1 if isinstance(result,dict) and result.get('ok') is False else 0
    except Exception as exc:
        print(json.dumps({'ok':False,'error':str(exc),'type':type(exc).__name__},ensure_ascii=False))
        return 1

# a4p-provenance: a4p-50d41ed6-f9f9-4470-ac9c-e700dd134a07/d329b2c4390a56dcfef1
