"""Module for processing network device bandwidth, CPU, memory, and firewall log data."""

import math

import pandas as pd


def bw_unit_normalize(input):
    """Normalize the bandwidth of a record to Mbps.

    Args:
        input (dict or pd.Series): The record containing 'Bandwidth' and 'Unit'.

    Returns:
        dict or pd.Series: The record with normalized 'Bandwidth' and unit set to 'Mbps'.
    """
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
    input["Bandwidth"] = input["Bandwidth"] * math.pow(10, units[input["Unit"].strip().lower()])
    input["Unit"] = "Mbps"
    return input


def process_with_from_n_to(raw: dict[str, pd.DataFrame], lookUpTable: pd.DataFrame) -> pd.DataFrame:
    """Process raw data using lookup table based on 'From' and 'To' hostname/interface pairs.

    Args:
        raw (dict[str, pd.DataFrame]): Dictionary mapping metric names to DataFrames.
        lookUpTable (pd.DataFrame): Lookup table containing routing or network links.

    Returns:
        pd.DataFrame: The merged and processed DataFrame.
    """
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
        calc[each][f"{each} %"] = (calc[each][f"{each} Bandwidth"] / calc[each]["Bandwidth"]).round(decimals=5)
    res = calc[list(calc.keys())[0]]
    for key in list(calc.keys())[1:]:
        res = pd.merge(
            left=res,
            right=calc[key],
            on=res.columns.to_list()[:-3],
            how="left",
        )
    return res


def process_basic(raw: dict[str, pd.DataFrame], lookUpTable: pd.DataFrame) -> pd.DataFrame:
    """Process basic hostname/interface data.

    Args:
        raw (dict[str, pd.DataFrame]): Dictionary of raw data DataFrames.
        lookUpTable (pd.DataFrame): The lookup DataFrame.

    Returns:
        pd.DataFrame: Merged and calculated DataFrame with percentage values.
    """
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
        calc[each][f"{each} %"] = (calc[each][f"{each} Bandwidth"] / calc[each]["Bandwidth"]).round(decimals=5)
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
    """Process F5 CPU, memory, and bandwidth data.

    Args:
        raw (dict[str, pd.DataFrame]): Dictionary of F5 metrics (in/out bandwidth, cpu, memory).
        lookUpTable (pd.DataFrame): Lookup table for F5 interfaces.

    Returns:
        pd.DataFrame: The processed and re-indexed DataFrame containing F5 performance metrics.
    """
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
        calc[each][f"{each} %"] = (calc[each][f"{each} Bandwidth"] / calc[each]["Bandwidth"]).round(decimals=5)
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
    rawCpu = rawCpu.pivot_table(index="Hostname", columns="cpu_num", values="95th CPU", aggfunc="first").reset_index()
    cpu_columns = [f"cpu{i}" for i in range(8)]
    rawCpu[cpu_columns] = rawCpu[cpu_columns].map(lambda x: float(str(x).split("%")[0]) / 100)
    res = pd.merge(res, rawCpu, how="left", on="Hostname")
    raw["mem"].rename(columns={"Metric": "Hostname", "95th Memory": "mem %"}, inplace=True)
    raw["mem"]["mem %"] = raw["mem"]["mem %"].apply(lambda x: float(str(x).split("%")[0]) / 100)
    res = pd.merge(res, raw["mem"], how="left", on="Hostname")
    colOrder = (
        [
            "F5",
            "Hostname",
        ]
        + [f"cpu{i}" for i in range(8)]
        + [
            "mem %",
            "Interface",
            "Bandwidth",
            "bw-in Bandwidth",
            "bw-in %",
            "bw-out Bandwidth",
            "bw-out %",
        ]
    )
    res = res.reindex(columns=colOrder)
    return res


def process_firewall(raw: dict[str, pd.DataFrame], lookUpTable: pd.DataFrame) -> pd.DataFrame:
    """Process firewall system performance metrics (CPU, Memory, Connections).

    Args:
        raw (dict[str, pd.DataFrame]): Dictionary containing firewall CPU, Memory, and Connection logs.
        lookUpTable (pd.DataFrame): Lookup table of firewall hosts.

    Returns:
        pd.DataFrame: LookUpTable DataFrame merged with system metrics.
    """
    raw["con"] = pd.concat([raw["con-cp"], raw["con-noncp"]]).reset_index()
    del raw["con-cp"], raw["con-noncp"]
    for each in raw.keys():
        lookUpTable = pd.merge(lookUpTable, raw[each], how="left", on="Hostname")
    for col in ["CPU 95%", "Memory 95%", "Connection Count 95%"]:
        lookUpTable[col] = lookUpTable[col].apply(lambda x: (float(str(x).split("%")[0].replace(",", ".")) / 100))
    lookUpTable.drop("index", axis=1, inplace=True)
    return lookUpTable


def conc_df(orig: dict[str, pd.DataFrame], ext: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Concatenate two dictionaries of DataFrames matching by key.

    Args:
        orig (dict[str, pd.DataFrame]): Original dictionary of DataFrames.
        ext (dict[str, pd.DataFrame]): Extension dictionary of DataFrames.

    Returns:
        dict[str, pd.DataFrame]: New dictionary of concatenated DataFrames.
    """
    res = {}
    for key in orig.keys():
        res[key] = pd.concat(objs=[orig[key], ext[key]], axis=0, ignore_index=True)
    return res


def count_occurrences(raw: pd.DataFrame, lookupTable: pd.DataFrame) -> pd.DataFrame:
    """Count state-down occurrences for each interface in lookupTable.

    Args:
        raw (pd.DataFrame): Raw log messages.
        lookupTable (pd.DataFrame): Lookup table containing interfaces of interest.

    Returns:
        pd.DataFrame: The lookupTable with occurrences counted.
    """
    interface_patterns = "|".join(lookupTable["Interface"].unique().astype(str))
    raw = (
        raw[raw["log_message"].str.contains("changed state to down", case=False)]
        .assign(Interface=raw["log_message"].str.extract(f"({interface_patterns})"))
        .drop_duplicates(subset=["@timestamp", "hostname", "Interface"], keep="last")
    )
    count_series = raw.groupby(["hostname", "Interface"]).size().reset_index(name="Count")
    count_series.columns = [col.title() for col in count_series.columns]
    res = (
        pd.merge(
            left=lookupTable,
            right=count_series,
            left_on=["Headend Router", "Interface"],
            right_on=["Hostname", "Interface"],
            how="left",
        )
        .drop(columns="Hostname")
        .fillna({"Count": 0})
        .astype({"Count": int})
    )
    return res


def count_by_column(lookupTable: pd.DataFrame, columnList: list[str], raw: pd.DataFrame) -> pd.DataFrame:
    """Count state-down occurrences grouped by specified hostname columns.

    Args:
        lookupTable (pd.DataFrame): Lookup table containing interfaces of interest.
        columnList (list[str]): List of column names representing hostnames to filter/group by.
        raw (pd.DataFrame): Raw log messages.

    Returns:
        pd.DataFrame: The lookup table with counted occurrences per column host.
    """
    res = lookupTable.copy()
    interface_patterns = "|".join(lookupTable["Interface"].unique().astype(str))
    raw = (
        raw[raw["log_message"].str.contains("changed state to down", case=False)]
        .assign(Interface=raw["log_message"].str.extract(f"({interface_patterns})"))
        .drop_duplicates(subset=["@timestamp", "hostname", "Interface"], keep="last")
    )
    count_series = raw.groupby(["hostname", "Interface"]).size().reset_index(name="Count")
    for column in columnList:
        res = (
            res.merge(
                count_series[count_series["hostname"] == column],
                left_on="Interface",
                right_on="Interface",
                how="left",
            )
            .drop(columns=["hostname"])
            .fillna({"Count": 0})
            .astype({"Count": int})
            .rename(columns={"Count": column})
        )
    return res
