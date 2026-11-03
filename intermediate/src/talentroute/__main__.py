import argparse,json
from .data import download,prepare

def main():
    """Parse the command and optional budget, then run its development workflow."""
    p=argparse.ArgumentParser();p.add_argument('command',choices=['download','prepare','fit','evaluate','eda','report','stability','demo','data-sensitivity','revision','diagnostics']);p.add_argument('--budget',type=float,default=300);args=p.parse_args()
    if args.command=='download': print(download())
    elif args.command=='prepare': print(json.dumps(prepare(),indent=2))
    elif args.command=='fit':
        from .models import fit_development
        print(fit_development())
    elif args.command=='evaluate':
        from .evaluation import evaluate_development
        print(evaluate_development())
    elif args.command=='eda':
        from .eda import eda
        eda()
    elif args.command=='data-sensitivity':
        from .data_sensitivity import data_sensitivity
        data_sensitivity()
    elif args.command=='stability':
        from .stability import stability
        stability()
    elif args.command=='report':
        from .report import report
        report()
    elif args.command=='revision':
        from .revision import revision
        print(revision())
    elif args.command=='diagnostics':
        from .diagnostics import diagnostics
        diagnostics()
    elif args.command=='demo':
        from .demo import demo
        demo(args.budget)
if __name__=='__main__': main()
