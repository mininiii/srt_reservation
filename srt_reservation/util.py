import argparse
import json

def load_config_from_json(file_path="config.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config

def parse_cli_args():
    parser = argparse.ArgumentParser(description='')

    parser.add_argument("--json", help="Load config from JSON file", type=bool, default=False)

    parser.add_argument("--user", help="Username", type=str, metavar="1234567890")
    parser.add_argument("--psw", help="Password", type=str, metavar="abc1234")
    parser.add_argument("--dpt", help="Departure Station", type=str, metavar="동탄")
    parser.add_argument("--arr", help="Arrival Station", type=str, metavar="동대구")
    parser.add_argument("--dt", help="Departure Date", type=str, metavar="20220118")
    parser.add_argument("--tm", help="Departure Time", type=str, metavar="08, 10, 12, ...")

    parser.add_argument("--stnum", help="start no of trains to check", type=int, metavar="1", default=1)
    parser.add_argument("--num", help="no of trains to check", type=int, metavar="2", default=2)
    parser.add_argument("--reserve", help="Reserve or not", type=bool, metavar="2", default=False)

    parser.add_argument("--sender", help="Sender email address", type=str, metavar="")
    parser.add_argument("--recipient", help="Recipient email address", type=str, metavar="")
    parser.add_argument("--app_password", help="App password for sender email", type=str, metavar="")

    args = parser.parse_args()

    if args.json:
        config = load_config_from_json()
        return config
    else:
        # 딕셔너리가 아닌 Namespace 객체를 반환하므로
        # 필요한 경우 dict로 변환
        return vars(args)
