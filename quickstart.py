# """ Quickstart script for InstaPy usage """

# # imports
# from srt_reservation.main_old import SRT
# from srt_reservation.util_old import parse_cli_args


# if __name__ == "__main__":
#     cli_args = parse_cli_args()

#     login_id = cli_args.user
#     login_psw = cli_args.psw
#     dpt_stn = cli_args.dpt
#     arr_stn = cli_args.arr
#     dpt_dt = cli_args.dt
#     dpt_tm = cli_args.tm
    
#     start_trains_to_check = cli_args.stnum
#     num_trains_to_check = cli_args.num
#     want_reserve = cli_args.reserve

#     sender = cli_args.sender
#     recipient = cli_args.recipient
#     app_password = cli_args.app_password

#     srt = SRT(dpt_stn, arr_stn, dpt_dt, dpt_tm, start_trains_to_check, num_trains_to_check, want_reserve)
#     srt.run(login_id, login_psw, sender, recipient, app_password)

from srt_reservation.main_old import SRT
from srt_reservation.util import parse_cli_args

if __name__ == "__main__":
    config = parse_cli_args()

    login_id = config.get("user")
    login_psw = config.get("psw")
    dpt_stn = config.get("dpt")
    arr_stn = config.get("arr")
    dpt_dt = config.get("dt")
    dpt_tm = config.get("tm")

    start_trains_to_check = config.get("stnum", 1)
    num_trains_to_check = config.get("num", 2)
    want_reserve = config.get("reserve", False)

    sender = config.get("sender")
    recipient = config.get("recipient")
    app_password = config.get("app_password")

    srt = SRT(dpt_stn, arr_stn, dpt_dt, dpt_tm, start_trains_to_check, num_trains_to_check, want_reserve)
    srt.run(login_id, login_psw, sender, recipient, app_password)
