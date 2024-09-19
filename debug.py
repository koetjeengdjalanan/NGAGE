import pandas as pd
from pathlib import Path

raw = pd.read_csv(
    filepath_or_buffer=Path(
        r"C:\Users\marti\Documents\NipponTelephonyTelecomination\Playground\ReportingAutomation\.devAsset\res['F5'].csv"
    ).absolute()
)

cpu_columns = [f"cpu{i}" for i in range(8)]
raw[cpu_columns] = raw[cpu_columns].map(lambda x: float(str(x).split("%")[0]) / 100)

raw["95th Memory"] = raw["95th Memory"].apply(
    lambda x: float(str(x).split("%")[0]) / 100
)
print(raw)
