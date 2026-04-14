from datetime import datetime


def log_msg(level: str, name: str, function: str, line: str, message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    level_padded = f"{level:<8}"
    print(f"{timestamp} | {level_padded} | {name}:{function}:{line} - {message}", flush=True)
