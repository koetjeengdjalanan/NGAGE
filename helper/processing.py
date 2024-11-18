import math

import pandas as pd


def bw_unit_normalize(input):
    units = {
        "bps": -6,
        "kbps": -3,
        "mbps": 0,
        "gbps": 3,
        "b/s": -6,
        "kb/s": -3,
        "mb/s": 0,
        "gb/s": 3,
    }
    input["Bandwidth"] = input["Bandwidth"] * math.pow(
        10, units[input["Unit"].strip().lower()]
    )
    input["Unit"] = "Mbps"
    return input


def process_with_from_n_to(
    raw: dict[str, pd.DataFrame], lookUpTable: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    calc: dict[str, pd.DataFrame] = {}
    for each in list(raw.keys()):
        raw[each] = raw[each][["Hostname", "Interface", "Bandwidth", "Unit"]].rename(
            columns={"Bandwidth": f"{each} Bandwidth", "Unit": f"{each} unit"}
        )
        raw[each]["Hostname"] = raw[each]["Hostname"].apply(lambda x: x.lower())
        calc[each] = pd.merge(
            left=lookUpTable,
            right=raw[each],
            how="left",
            left_on=["From Hostname", "From Interface"],
            right_on=["Hostname", "Interface"],
        ).drop(["Hostname", "Interface"], axis=1)
        missing = calc[each][calc[each][f"{each} Bandwidth"].isna()]
        if not missing.empty:
            additional = pd.merge(
                left=lookUpTable,
                right=raw[each],
                how="left",
                left_on=["To Hostname", "To Interface"],
                right_on=["Hostname", "Interface"],
            ).drop(["Hostname", "Interface"], axis=1)
            calc[each].update(additional)
        calc[each][f"{each} %"] = (
            calc[each][f"{each} Bandwidth"] / calc[each]["Bandwidth"]
        ).round(decimals=5)
    res = calc[list(calc.keys())[0]]
    for key in list(calc.keys())[1:]:
        res = pd.merge(
            left=res,
            right=calc[key],
            on=res.columns.to_list()[:-3],
            how="left",
        )
    return res


def process_basic(
    raw: dict[str, pd.DataFrame], lookUpTable: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    calc: dict[str, pd.DataFrame] = {}
    for each in list(raw.keys()):
        raw[each] = raw[each][["Hostname", "Interface", "Bandwidth", "Unit"]].rename(
            columns={"Bandwidth": f"{each} Bandwidth", "Unit": f"{each} unit"}
        )
        raw[each]["Hostname"] = raw[each]["Hostname"].apply(lambda x: x.lower())
        raw[each]["Interface"] = raw[each]["Interface"].apply(lambda x: str(x))
        lookUpTable["Interface"] = lookUpTable["Interface"].apply(lambda x: str(x))
        calc[each] = pd.merge(
            left=lookUpTable,
            right=raw[each],
            how="left",
            left_on=["Hostname", "Interface"],
            right_on=["Hostname", "Interface"],
        )
        calc[each][f"{each} %"] = (
            calc[each][f"{each} Bandwidth"] / calc[each]["Bandwidth"]
        ).round(decimals=5)
    res = calc[list(calc.keys())[0]]
    for key in list(calc.keys())[1:]:
        res = pd.merge(
            left=res,
            right=calc[key],
            on=res.columns.to_list()[:-3],
            how="left",
        )
    return res


def process_f5(raw: dict[str, pd.DataFrame], lookUpTable: pd.DataFrame) -> pd.DataFrame:
    calc: dict[str, pd.DataFrame] = {}
    for each in ["bw-in", "bw-out"]:
        raw[each] = raw[each][["Hostname", "Interface", "Bandwidth", "Unit"]].rename(
            columns={"Bandwidth": f"{each} Bandwidth", "Unit": f"{each} unit"}
        )
        raw[each]["Hostname"] = raw[each]["Hostname"].apply(lambda x: x.lower())
        raw[each]["Interface"] = raw[each]["Interface"].apply(lambda x: str(x))
        lookUpTable["Interface"] = lookUpTable["Interface"].apply(lambda x: str(x))
        calc[each] = pd.merge(
            left=lookUpTable,
            right=raw[each],
            how="left",
            left_on=["Hostname", "Interface"],
            right_on=["Hostname", "Interface"],
        )
        calc[each][f"{each} %"] = (
            calc[each][f"{each} Bandwidth"] / calc[each]["Bandwidth"]
        ).round(decimals=5)
    res = calc[list(calc.keys())[0]]
    for key in list(calc.keys())[1:]:
        res = pd.merge(
            left=res,
            right=calc[key],
            on=res.columns.to_list()[:-3],
            how="left",
        )
    rawCpu = pd.concat([raw["pdc-cpu"], raw["sdc-cpu"]]).reset_index()
    rawCpu["Hostname"] = rawCpu["Metric"].apply(lambda x: x.split(" ")[0].lower())
    rawCpu["cpu_num"] = rawCpu["Metric"].apply(lambda x: "cpu" + x.split("cpu")[-1])
    rawCpu = rawCpu.pivot_table(
        index="Hostname", columns="cpu_num", values="95th CPU", aggfunc="first"
    ).reset_index()
    cpu_columns = [f"cpu{i}" for i in range(8)]
    rawCpu[cpu_columns] = rawCpu[cpu_columns].map(
        lambda x: float(str(x).split("%")[0]) / 100
    )
    res = pd.merge(res, rawCpu, how="left", on="Hostname")
    raw["mem"].rename(
        columns={"Metric": "Hostname", "95th Memory": "mem %"}, inplace=True
    )
    raw["mem"]["mem %"] = raw["mem"]["mem %"].apply(
        lambda x: float(str(x).split("%")[0]) / 100
    )
    res = pd.merge(res, raw["mem"], how="left", on="Hostname")
    return res


def process_firewall(
    raw: dict[str, pd.DataFrame], lookUpTable: pd.DataFrame
) -> pd.DataFrame:
    raw["con"] = pd.concat([raw["con-cp"], raw["con-noncp"]]).reset_index()
    del raw["con-cp"], raw["con-noncp"]
    for each in raw.keys():
        lookUpTable = pd.merge(lookUpTable, raw[each], how="left", on="Hostname")
    for col in ["CPU 95%", "Memory 95%", "Connection Count 95%"]:
        lookUpTable[col] = lookUpTable[col].apply(
            lambda x: (float(str(x).split("%")[0].replace(",", ".")) / 100)
        )
    lookUpTable.drop("index", axis=1, inplace=True)
    return lookUpTable


def conc_df(
    orig: dict[str, pd.DataFrame], ext: dict[str, pd.DataFrame]
) -> dict[str, pd.DataFrame]:
    res = {}
    for key in orig.keys():
        res[key] = pd.concat(objs=[orig[key], ext[key]], axis=0, ignore_index=True)
    return res
