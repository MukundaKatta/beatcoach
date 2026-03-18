"""CLI for beatcoach."""
import sys, json, argparse
from .core import Beatcoach

def main():
    parser = argparse.ArgumentParser(description="BeatCoach — AI Music Practice Coach. Real-time instrument practice feedback with pitch and rhythm analysis.")
    parser.add_argument("command", nargs="?", default="status", choices=["status", "run", "info"])
    parser.add_argument("--input", "-i", default="")
    args = parser.parse_args()
    instance = Beatcoach()
    if args.command == "status":
        print(json.dumps(instance.get_stats(), indent=2))
    elif args.command == "run":
        print(json.dumps(instance.process(input=args.input or "test"), indent=2, default=str))
    elif args.command == "info":
        print(f"beatcoach v0.1.0 — BeatCoach — AI Music Practice Coach. Real-time instrument practice feedback with pitch and rhythm analysis.")

if __name__ == "__main__":
    main()
