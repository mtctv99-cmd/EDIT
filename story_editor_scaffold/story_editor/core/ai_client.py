import os, shlex, subprocess, tempfile, random, time

class AIClient:
    @staticmethod
    def run_cmd_template(cmd_template: str, model: str, prompt: str, image: str, env_vars: dict = None, prompt_file_mode=False, api_keys: list = None):
        """
        Chạy lệnh CLI theo template.
        - cmd_template: "gemini --model {model} --input-text {prompt} --input-image {image}"
        - Nếu CLI yêu cầu prompt từ file, đặt prompt_file_mode=True để ghi ra file tạm và dùng {prompt_file}.
        - api_keys: Danh sách các API keys để thử.
        """
        if api_keys is None:
            api_keys = [""] # Use an empty key if no keys are provided

        random.shuffle(api_keys) # Shuffle keys for random selection

        for api_key in api_keys:
            tmp_prompt_file = None
            try:
                if prompt_file_mode:
                    fd, path = tempfile.mkstemp(suffix=".txt")
                    os.close(fd)
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(prompt)
                    tmp_prompt_file = path
                    cmd = f"python gemini_cli_wrapper.py --model {model} --prompt-file {shlex.quote(path)} --image {shlex.quote(image)}"
                else:
                    cmd = f"python gemini_cli_wrapper.py --model {model} --prompt {shlex.quote(prompt)} --image {shlex.quote(image)}"

                # Chuẩn bị env (để đưa API KEY cho CLI nếu cần)
                run_env = os.environ.copy()
                if env_vars:
                    run_env.update(env_vars)
                if api_key: # Add the current API key to the environment
                    run_env["GEMINI_API_KEY"] = api_key

                # Thực thi
                proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=run_env)
                ok = (proc.returncode == 0)

                if ok:
                    return ok, proc.stdout.strip(), proc.stderr.strip(), proc.returncode
                else:
                    # Check for common API errors (e.g., 429, 5xx) and retry
                    if "429" in proc.stderr or "500" in proc.stderr or "503" in proc.stderr:
                        print(f"API call failed with error: {proc.stderr}. Retrying with another key...")
                        time.sleep(2) # Wait before retrying
                        continue # Try next API key
                    else:
                        return ok, proc.stdout.strip(), proc.stderr.strip(), proc.returncode # Return other errors immediately
            finally:
                if tmp_prompt_file and os.path.exists(tmp_prompt_file):
                    try: os.remove(tmp_prompt_file)
                    except: pass
        return False, "", "All API keys failed or no keys provided.", -1 # All keys failed