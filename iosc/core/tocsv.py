"""Just holds CVS export function."""
# 1. std
import pathlib
import csv
import datetime

# 3. local
from iosc.core import mycomtrade


def export_to_csv(osc: mycomtrade.MyComtrade, y_centered: bool, pors: bool, dst: pathlib.Path):
    """Export osc into CSV file.

    :param osc: Osc to export
    :param y_centered: Subj
    :param pors: Current Primary/Secondary state
    :param dst: Destination file
    """
    with open(dst, 'wt', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=';')
        # 1. header
        h1 = ["Sample N", "Relative time", "Astronomic time"]
        h2 = ["", "ms", ""]
        for s in osc.y:
            h1.append(s.sid)
            h2.append("Log. 0/1" if s.is_bool else s.uu)
        csv_writer.writerow(h1)
        csv_writer.writerow(h2)
        # 2. body
        for i in range(osc.total_samples):
            data = [
                i + 1,
                "%.6f" % osc.x[i],
                (osc.trigger_timestamp + datetime.timedelta(milliseconds=osc.x[i])).time().isoformat()
            ]
            for j in range(len(osc.y)):
                data.append(osc.y[j].value(i, y_centered, pors))
            csv_writer.writerow(data)
