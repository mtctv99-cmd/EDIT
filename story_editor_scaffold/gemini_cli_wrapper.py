import argparse
import subprocess
import shlex
import os

def main():
    parser = argparse.ArgumentParser(description="Gemini CLI Wrapper")
    parser.add_argument("--model", required=True, help="Gemini model to use")
    parser.add_argument("--prompt", help="Prompt text")
    parser.add_argument("--prompt-file", help="Path to prompt file")
    parser.add_argument("--image", help="Path to image file")
    parser.add_argument("--api-key-env", default="GEMINI_API_KEY", help="Environment variable name for API key")

    args = parser.parse_args()

    cmd = ["gemini", "--model", args.model]

    if args.prompt_file:
        cmd.extend(["--input-text-file", shlex.quote(args.prompt_file)])
    elif args.prompt:
        cmd.extend(["--input-text", shlex.quote(args.prompt)])

    if args.image:
        cmd.extend(["--input-image", shlex.quote(args.image)])

    # Set API key from environment variable if available
    env = os.environ.copy()
    if args.api_key_env in env:
        # Assuming the actual gemini CLI reads from this env var
        pass

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
        print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr.strip()}", file=os.sys.stderr)
        os.sys.exit(e.returncode)
    except FileNotFoundError:
        print("Error: 'gemini' command not found. Please ensure Gemini CLI is installed and in your PATH.", file=os.sys.stderr)
        os.sys.exit(1)

if __name__ == "__main__":
    main()